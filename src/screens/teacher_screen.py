import streamlit as st
import pandas as pd

from datetime import datetime

from src.ui.base_layout import (
    style_background_dashboard,
    style_base_layout
)

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card

from src.database.db import (
    check_teacher_exists,
    create_teacher,
    teacher_login,
    get_teacher_subjects,
    get_attendance_for_teacher
)

from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_share_subject import share_subject_dialog
from src.components.dialog_voice_attendance import voice_attendance_dialog


# =========================================================
# TEACHER SCREEN
# =========================================================

def teacher_screen():

    style_background_dashboard()
    style_base_layout()

    if "teacher_data" in st.session_state:
        teacher_dashboard()

    elif (
        "teacher_login_type" not in st.session_state
        or st.session_state.teacher_login_type == "login"
    ):
        teacher_screen_login()

    elif st.session_state.teacher_login_type == "register":
        teacher_screen_register()


# =========================================================
# TEACHER DASHBOARD
# =========================================================

def teacher_dashboard():

    teacher_data = st.session_state.teacher_data

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge"
    )

    with c1:
        header_dashboard()

    with c2:

        st.subheader(
            f"Welcome, {teacher_data['name']}"
        )

        if st.button(
            "Logout",
            type="secondary",
            key="teacher_logout",
            shortcut="control+backspace"
        ):

            st.session_state["is_logged_in"] = False

            if "teacher_data" in st.session_state:
                del st.session_state.teacher_data

            st.rerun()

    st.space()

    # =====================================================
    # TABS
    # =====================================================

    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "take_attendance"

    tab1, tab2, tab3 = st.columns(3)

    with tab1:

        type1 = (
            "primary"
            if st.session_state.current_teacher_tab == "take_attendance"
            else "tertiary"
        )

        if st.button(
            "Take Attendance",
            type=type1,
            width="stretch",
            icon=":material/mic:"
        ):

            st.session_state.current_teacher_tab = "take_attendance"
            st.rerun()

    with tab2:

        type2 = (
            "primary"
            if st.session_state.current_teacher_tab == "manage_subjects"
            else "tertiary"
        )

        if st.button(
            "Manage Subjects",
            type=type2,
            width="stretch",
            icon=":material/book_ribbon:"
        ):

            st.session_state.current_teacher_tab = "manage_subjects"
            st.rerun()

    with tab3:

        type3 = (
            "primary"
            if st.session_state.current_teacher_tab == "attendance_records"
            else "tertiary"
        )

        if st.button(
            "Attendance Records",
            type=type3,
            width="stretch",
            icon=":material/cards_stack:"
        ):

            st.session_state.current_teacher_tab = "attendance_records"
            st.rerun()

    st.divider()

    # =====================================================
    # CURRENT TAB
    # =====================================================

    if st.session_state.current_teacher_tab == "take_attendance":

        teacher_tab_take_attendance()

    elif st.session_state.current_teacher_tab == "manage_subjects":

        teacher_tab_manage_subjects()

    elif st.session_state.current_teacher_tab == "attendance_records":

        teacher_tab_attendance_records()

    footer_dashboard()


# =========================================================
# TAKE VOICE ATTENDANCE
# =========================================================

def teacher_tab_take_attendance():

    teacher_id = st.session_state.teacher_data["id"]

    st.header("Take Voice Attendance")

    st.info(
        "Students will be identified using their registered voice. "
        "Select a subject below and start the attendance process."
    )

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:

        st.warning(
            "You haven't created any subjects yet! "
            "Please create one to begin."
        )

        return

    # -----------------------------------------------------
    # SUBJECT OPTIONS
    # -----------------------------------------------------

    subject_options = {
        f"{s['name']} - {s['subject_code']}": s["id"]
        for s in subjects
    }

    selected_subject_label = st.selectbox(
        "Select Subject",
        options=list(subject_options.keys())
    )

    selected_subject_id = subject_options[
        selected_subject_label
    ]

    st.divider()

    # -----------------------------------------------------
    # VOICE ATTENDANCE
    # -----------------------------------------------------

    st.subheader("🎤 Voice Attendance")

    st.write(
        "Click the button below to start voice-based attendance "
        "for the selected subject."
    )

    if st.button(
        "Use Voice Attendance",
        type="primary",
        width="stretch",
        icon=":material/mic:"
    ):

        voice_attendance_dialog(
            selected_subject_id
        )


# =========================================================
# MANAGE SUBJECTS
# =========================================================

def teacher_tab_manage_subjects():

    teacher_id = st.session_state.teacher_data["id"]

    col1, col2 = st.columns(2)

    with col1:

        st.header(
            "Manage Subjects",
            width="stretch"
        )

    with col2:

        if st.button(
            "Create New Subject",
            width="stretch",
            type="primary"
        ):

            create_subject_dialog(teacher_id)

    st.divider()

    subjects = get_teacher_subjects(teacher_id)

    if not subjects:

        st.info(
            "No subjects found. Create one above."
        )

        return

    # -----------------------------------------------------
    # DISPLAY SUBJECTS
    # -----------------------------------------------------

    for sub in subjects:

        stats = [
            (
                "🫂",
                "Students",
                sub.get("total_students", 0)
            ),
            (
                "🕰️",
                "Classes",
                sub.get("total_classes", 0)
            )
        ]

        def share_btn(
            subject_name=sub["name"],
            subject_code=sub["subject_code"]
        ):

            if st.button(
                f"Share Code: {subject_name}",
                key=f"share_{subject_code}",
                icon=":material/share:"
            ):

                share_subject_dialog(
                    subject_name,
                    subject_code
                )

        subject_card(
            name=sub["name"],
            code=sub["subject_code"],
            section=sub["section"],
            stats=stats,
            footer_callback=share_btn
        )

        st.space()


# =========================================================
# ATTENDANCE RECORDS
# =========================================================

def teacher_tab_attendance_records():

    st.header("Attendance Records")

    teacher_id = st.session_state.teacher_data["id"]

    records = get_attendance_for_teacher(
        teacher_id
    )

    if not records:

        st.info(
            "No attendance records found yet."
        )

        return

    data = []

    for r in records:

        ts = r.get("timestamp")

        data.append(
            {
                "ts_group": (
                    ts.split(".")[0]
                    if ts
                    else None
                ),

                "Time": (
                    datetime.fromisoformat(ts).strftime(
                        "%Y-%m-%d %I:%M %p"
                    )
                    if ts
                    else "N/A"
                ),

                "Subject": r["subjects"]["name"],

                "Subject Code": (
                    r["subjects"]["subject_code"]
                ),

                "is_present": bool(
                    r.get("is_present", False)
                )
            }
        )

    df = pd.DataFrame(data)

    summary = (
        df.groupby(
            [
                "ts_group",
                "Time",
                "Subject",
                "Subject Code"
            ]
        )
        .agg(
            Present_Count=(
                "is_present",
                "sum"
            ),

            Total_Count=(
                "is_present",
                "count"
            )
        )
        .reset_index()
    )

    summary["Attendance Status"] = (
        "✅ "
        + summary["Present_Count"].astype(str)
        + " / "
        + summary["Total_Count"].astype(str)
        + " Students"
    )

    display_df = (
        summary
        .sort_values(
            by="ts_group",
            ascending=False
        )
        [
            [
                "Time",
                "Subject",
                "Subject Code",
                "Attendance Status"
            ]
        ]
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True
    )


# =========================================================
# TEACHER LOGIN
# =========================================================

def login_teacher(
    username,
    password
):

    if not username or not password:
        return False

    teacher = teacher_login(
        username,
        password
    )

    if teacher:

        st.session_state.user_role = "teacher"

        st.session_state.teacher_data = teacher

        st.session_state.is_logged_in = True

        return True

    return False


# =========================================================
# TEACHER LOGIN SCREEN
# =========================================================

def teacher_screen_login():

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
            key="teacher_home",
            shortcut="control+backspace"
        ):

            st.session_state["login_type"] = None
            st.rerun()

    st.header(
        "Teacher Login",
        text_alignment="center"
    )

    st.space()
    st.space()

    teacher_username = st.text_input(
        "Enter username",
        placeholder="ananyaroy"
    )

    teacher_pass = st.text_input(
        "Enter password",
        type="password",
        placeholder="Enter password"
    )

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:

        if st.button(
            "Login",
            icon=":material/passkey:",
            shortcut="control+enter",
            width="stretch"
        ):

            if login_teacher(
                teacher_username,
                teacher_pass
            ):

                st.toast(
                    "Welcome back! 👋"
                )

                import time
                time.sleep(1)

                st.rerun()

            else:

                st.error(
                    "Invalid username and password combo"
                )

    with btnc2:

        if st.button(
            "Register Instead",
            type="primary",
            icon=":material/person_add:",
            width="stretch"
        ):

            st.session_state.teacher_login_type = "register"

            st.rerun()

    footer_dashboard()


# =========================================================
# TEACHER REGISTRATION
# =========================================================

def register_teacher(
    teacher_username,
    teacher_name,
    teacher_pass,
    teacher_pass_confirm
):

    if (
        not teacher_username
        or not teacher_name
        or not teacher_pass
    ):

        return False, "All fields are required!"

    if check_teacher_exists(
        teacher_username
    ):

        return False, "Username already taken"

    if teacher_pass != teacher_pass_confirm:

        return False, "Password doesn't match"

    try:

        create_teacher(
            teacher_username,
            teacher_pass,
            teacher_name
        )

        return True, "Successfully created! Login now."

    except Exception:

        return False, "Unexpected error occurred."


# =========================================================
# TEACHER REGISTRATION SCREEN
# =========================================================

def teacher_screen_register():

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
            key="teacher_register_home",
            shortcut="control+backspace"
        ):

            st.session_state["login_type"] = None
            st.rerun()

    st.header(
        "Register Your Teacher Profile"
    )

    st.space()
    st.space()

    teacher_username = st.text_input(
        "Enter username",
        placeholder="ananyaroy"
    )

    teacher_name = st.text_input(
        "Enter name",
        placeholder="Ananya Roy"
    )

    teacher_pass = st.text_input(
        "Enter password",
        type="password",
        placeholder="Enter password"
    )

    teacher_pass_confirm = st.text_input(
        "Confirm your password",
        type="password",
        placeholder="Enter password"
    )

    st.divider()

    btnc1, btnc2 = st.columns(2)

    with btnc1:

        if st.button(
            "Register Now",
            icon=":material/person_add:",
            shortcut="control+enter",
            width="stretch"
        ):

            success, message = register_teacher(
                teacher_username,
                teacher_name,
                teacher_pass,
                teacher_pass_confirm
            )

            if success:

                st.success(message)

                import time
                time.sleep(2)

                st.session_state.teacher_login_type = "login"

                st.rerun()

            else:

                st.error(message)

    with btnc2:

        if st.button(
            "Login Instead",
            type="primary",
            icon=":material/passkey:",
            width="stretch"
        ):

            st.session_state.teacher_login_type = "login"

            st.rerun()

    footer_dashboard()