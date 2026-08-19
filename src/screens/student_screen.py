import streamlit as st
import numpy as np
import time

from src.ui.base_layout import (
    style_background_dashboard,
    style_base_layout
)

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card

from src.pipelines.voice_pipeline import (
    get_voice_embedding,
    identify_speaker
)

from src.database.db import (
    get_all_students,
    create_student,
    get_student_subjects,
    get_student_attendance,
    unenroll_student_to_subject
)

from src.components.dialog_enroll import enroll_dialog


# =========================================================
# STUDENT DASHBOARD
# =========================================================

def student_dashboard():

    student_data = st.session_state.student_data
    student_id = student_data["id"]

    # -----------------------------------------------------
    # HEADER
    # -----------------------------------------------------

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge"
    )

    with c1:
        header_dashboard()

    with c2:

        st.subheader(
            f"Welcome, {student_data['name']}"
        )

        if st.button(
            "Logout",
            type="secondary",
            key="student_logout",
            shortcut="control+backspace"
        ):

            st.session_state["is_logged_in"] = False

            if "student_data" in st.session_state:
                del st.session_state.student_data

            st.rerun()

    st.space()

    # -----------------------------------------------------
    # SUBJECTS HEADER
    # -----------------------------------------------------

    c1, c2 = st.columns(2)

    with c1:

        st.header(
            "Your Enrolled Subjects"
        )

    with c2:

        if st.button(
            "Enroll in Subject",
            type="primary",
            width="stretch"
        ):

            enroll_dialog()

    st.divider()

    # -----------------------------------------------------
    # LOAD DATA
    # -----------------------------------------------------

    with st.spinner(
        "Loading your enrolled subjects..."
    ):

        subjects = get_student_subjects(
            student_id
        )

        logs = get_student_attendance(
            student_id
        )

    # -----------------------------------------------------
    # ATTENDANCE STATS
    # -----------------------------------------------------

    stats_map = {}

    for log in logs:

        sid = log["subject_id"]

        if sid not in stats_map:

            stats_map[sid] = {
                "total": 0,
                "attended": 0
            }

        stats_map[sid]["total"] += 1

        if log.get("is_present"):

            stats_map[sid]["attended"] += 1

    # -----------------------------------------------------
    # SUBJECT CARDS
    # -----------------------------------------------------

    cols = st.columns(2)

    for i, sub_node in enumerate(subjects):

        sub = sub_node["subjects"]

        sid = sub["id"]

        stats = stats_map.get(
            sid,
            {
                "total": 0,
                "attended": 0
            }
        )

        def unenroll_button(
            subject_id=sid,
            subject_name=sub["name"]
        ):

            if st.button(
                "Unenroll from this course",
                type="tertiary",
                width="stretch",
                icon=":material/delete_forever:",
                key=f"unenroll_{subject_id}"
            ):

                unenroll_student_to_subject(
                    student_id,
                    subject_id
                )

                st.toast(
                    f"Unenrolled from {subject_name} successfully!"
                )

                st.rerun()

        with cols[i % 2]:

            subject_card(
                name=sub["name"],
                code=sub["subject_code"],
                section=sub["section"],
                stats=[
                    (
                        "📅",
                        "Total",
                        stats["total"]
                    ),
                    (
                        "✅",
                        "Attended",
                        stats["attended"]
                    )
                ],
                footer_callback=unenroll_button
            )

    footer_dashboard()


# =========================================================
# STUDENT SCREEN
# =========================================================

def student_screen():

    style_background_dashboard()
    style_base_layout()

    # =====================================================
    # ALREADY LOGGED IN
    # =====================================================

    if "student_data" in st.session_state:

        student_dashboard()

        return

    # =====================================================
    # HEADER
    # =====================================================

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge"
    )

    with c1:

        header_dashboard()

    with c2:

        if st.button(
            "Go back to Home",
            type="secondary",
            key="student_home",
            shortcut="control+backspace"
        ):

            st.session_state["login_type"] = None

            st.rerun()

    # =====================================================
    # TITLE
    # =====================================================

    st.header(
        "Student Login",
        text_alignment="center"
    )

    st.space()

    st.info(
        "Login securely using your registered voice."
    )

    # =====================================================
    # SESSION STATES
    # =====================================================

    if "voice_registration" not in st.session_state:

        st.session_state.voice_registration = False

    # =====================================================
    # VOICE LOGIN
    # =====================================================

    st.subheader(
        "🎤 Voice Recognition"
    )

    st.write(
        "Use your registered voice to access your student account."
    )

    # UPDATED: full available width
    voice_audio = st.audio_input(
        "Record your voice",
        width="stretch"
    )

    if voice_audio:

        if st.button(
            "Analyze Voice",
            type="primary",
            width="stretch"
        ):

            with st.spinner(
                "AI is recognizing your voice..."
            ):

                new_embedding = get_voice_embedding(
                    voice_audio.read()
                )

                if new_embedding is None:

                    st.error(
                        "Could not process your voice. "
                        "Please try recording again."
                    )

                else:

                    all_students = get_all_students()

                    candidates = {}

                    # -------------------------------------------------
                    # BUILD VOICE PROFILE CANDIDATES
                    # -------------------------------------------------

                    for student in all_students:

                        stored_voice = student.get(
                            "voice_embedding"
                        )

                        if stored_voice:

                            candidates[
                                student["id"]
                            ] = np.array(
                                stored_voice,
                                dtype=float
                            )

                    if not candidates:

                        st.warning(
                            "No registered voice profiles were found."
                        )

                    else:

                        student_id, score = identify_speaker(
                            new_embedding,
                            candidates,
                            threshold=0.60
                        )
                        st.info(f"Voice similarity score: {score:.3f}")

                        # ---------------------------------------------
                        # STUDENT FOUND
                        # ---------------------------------------------

                        if student_id is not None:

                            student = next(
                                (
                                    s
                                    for s in all_students
                                    if s["id"] == student_id
                                ),
                                None
                            )

                            if student:

                                st.session_state.is_logged_in = True

                                st.session_state.user_role = "student"

                                st.session_state.student_data = student

                                st.toast(
                                    f"Welcome back, {student['name']}! 👋"
                                )

                                time.sleep(1)

                                st.rerun()

                        else:

                            st.warning(
                                "Voice not recognized. "
                                "Please try again or register your voice."
                            )

    # =====================================================
    # VOICE REGISTRATION
    # =====================================================

    st.divider()

    st.subheader(
        "🆕 New Student?"
    )

    st.write(
        "Create your student account using your voice."
    )

    if not st.session_state.voice_registration:

        if st.button(
            "Register with Voice",
            type="secondary",
            width="stretch"
        ):

            st.session_state.voice_registration = True

            st.rerun()

    # =====================================================
    # CREATE VOICE ACCOUNT
    # =====================================================

    if st.session_state.voice_registration:

        st.divider()

        st.subheader(
            "Create Voice Account"
        )

        st.info(
            "Enter your name and record your voice "
            "to create your student profile."
        )

        voice_name = st.text_input(
            "Enter your name",
            placeholder="E.g. Hamza Rizvi",
            key="voice_register_name"
        )

        # UPDATED: full available width
        registration_audio = st.audio_input(
            "Record your voice",
            key="voice_registration_audio",
            width="stretch"
        )

        if st.button(
            "Create Voice Account",
            type="primary",
            width="stretch"
        ):

            if not voice_name:

                st.warning(
                    "Please enter your name."
                )

            elif not registration_audio:

                st.warning(
                    "Please record your voice."
                )

            else:

                with st.spinner(
                    "Creating your voice profile..."
                ):

                    voice_emb = get_voice_embedding(
                        registration_audio.read()
                    )

                    if voice_emb is None:

                        st.error(
                            "Could not process your voice. "
                            "Please record again."
                        )

                    else:

                        response_data = create_student(
                            voice_name,
                            voice_embedding=voice_emb
                        )

                        if response_data:

                            st.success(
                                "Voice account created successfully!"
                            )

                            st.session_state.is_logged_in = True

                            st.session_state.user_role = "student"

                            st.session_state.student_data = response_data[0]

                            time.sleep(1)

                            st.rerun()

    footer_dashboard()