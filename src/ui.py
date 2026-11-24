
import streamlit as st
import pandas as pd
import plotly.express as px

from sqlalchemy import select

from src.database import SessionLocal, Student, User
from src.analytics import (
    student_frame,
    save_prediction,
    get_prediction_history,
    get_performance_summary
)
from src.ml import (
    predict_student,
    model_metrics,
    train_models,
    FEATURES
)
from src.career import recommend_careers, skill_gap


# --------------------------------------------------
# STUDENT DATABASE HELPERS
# --------------------------------------------------


# --------------------------------------------------
# STUDENT DATABASE HELPERS & ACCESS CONTROL
# --------------------------------------------------

def _require_role(user, allowed_roles):
    if (
        not isinstance(user, dict)
        or user.get("role") not in allowed_roles
    ):
        st.error("Access denied: You are not authorized.")
        st.stop()


def _student_profile(s):
    return {
        k: getattr(s, k) for k in FEATURES
    } | {
        "interests": s.interests
    }


def _get_student(student_id, actor):
    _require_role(actor, {"student", "faculty", "hod", "admin"})
    role = actor["role"]

    if role == "student" and student_id != actor.get("student_id"):
        st.error("Access denied: You can only access your own profile.")
        st.stop()

    db = SessionLocal()
    try:
        query = select(Student).where(Student.student_id == student_id)
        if role in {"faculty", "hod"}:
            query = query.where(Student.department == actor["department"])
        return db.scalar(query)
    finally:
        db.close()


def _upsert_student(
    student_id, name, department, semester, attendance, internal,
    assignment, study, gpa, programming, communication, analytical,
    interests, actor
):
    _require_role(actor, {"student", "faculty", "admin"})
    role = actor["role"]

    if role in {"student", "faculty"}:
        department = actor["department"]

    if role == "student" and student_id != actor.get("student_id"):
        raise PermissionError("Cannot modify another student's profile.")

    db = SessionLocal()
    try:
        student = db.scalar(
            select(Student).where(Student.student_id == student_id)
        )

        if student is not None and role in {"student", "faculty"}:
            if student.department != department:
                raise PermissionError(
                    "You cannot modify a student outside your department."
                )

        if student is None:
            if role == "faculty":
                raise PermissionError(
                    "Faculty can only update existing department students."
                )
            student = Student(
                student_id=student_id,
                name=name,
                department=department
            )
            db.add(student)

        values = {
            "name": name,
            "department": department,
            "semester": semester,
            "attendance": attendance,
            "internal_marks": internal,
            "assignment_score": assignment,
            "study_hours": study,
            "previous_gpa": gpa,
            "programming_skill": programming,
            "communication_skill": communication,
            "analytical_skill": analytical,
            "interests": interests
        }
        for key, value in values.items():
            setattr(student, key, value)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# --------------------------------------------------

# STUDENT PROFILE FORM
# --------------------------------------------------

def _profile_form(
    default=None,
    student_id="STU001",
    name="Student",
    actor=None
):
    _require_role(actor, {"student", "faculty", "admin"})
    d = default or {}

    with st.form("profile_form"):

        c1, c2 = st.columns(2)

        sid = c1.text_input(
            "Student ID",
            value=student_id,
            disabled=bool(default)
        )

        nm = c2.text_input(
            "Student name",
            value=name if not d else d.get("name", name)
        )

        dept = c1.text_input(
            "Department",
            value=(
                actor["department"]
                if actor["role"] in {"student", "faculty"}
                else d.get("department", "CSE")
            ),
            disabled=actor["role"] != "admin"
    )

        sem = c2.number_input(
            "Semester",
            1,
            8,
            int(d.get("semester", 1))
        )

        attendance = c1.slider(
            "Attendance (%)",
            0,
            100,
            int(d.get("attendance", 75))
        )

        internal = c2.slider(
            "Internal marks (%)",
            0,
            100,
            int(d.get("internal_marks", 60))
        )

        assignment = c1.slider(
            "Assignment score (%)",
            0,
            100,
            int(d.get("assignment_score", 60))
        )

        study = c2.slider(
            "Study hours per day",
            0.0,
            12.0,
            float(d.get("study_hours", 2.0)),
            0.5
        )

        gpa = c1.slider(
            "Previous GPA (0-10)",
            0.0,
            10.0,
            float(d.get("previous_gpa", 6.5)),
            0.1
        )

        programming = c2.slider(
            "Programming skill (1-5)",
            1,
            5,
            int(d.get("programming_skill", 3))
        )

        communication = c1.slider(
            "Communication skill (1-5)",
            1,
            5,
            int(d.get("communication_skill", 3))
        )

        analytical = c2.slider(
            "Analytical skill (1-5)",
            1,
            5,
            int(d.get("analytical_skill", 3))
        )

        interests = st.multiselect(
            "Career interests",
            [
                "Software Development",
                "Data Analytics",
                "Data Science",
                "Artificial Intelligence",
                "Cybersecurity",
                "Cloud Computing",
                "Business Analytics",
                "Web Development"
            ],
            default=[
                x.strip()
                for x in d.get(
                    "interests",
                    "Software Development"
                ).split(",")
                if x.strip()
            ]
        )

        submitted = st.form_submit_button(
            "Save student profile",
            use_container_width=True
        )

    if submitted:

        if not nm.strip() or not dept.strip():
            st.error("Student name and department are required.")
            return

        _upsert_student(
            sid,
            nm.strip(),
            dept.strip(),
            int(sem),
            attendance,
            internal,
            assignment,
            study,
            gpa,
            programming,
            communication,
            analytical,
            " , ".join(interests),
            actor=actor
        )

        st.success("Student profile saved successfully.")
        st.rerun()


# --------------------------------------------------
# AI PREDICTION PANEL
# --------------------------------------------------

def _prediction_panel(s, actor):
    _require_role(actor, {"student", "faculty", "admin"})
    authorized_student = _get_student(s.student_id, actor)
    if authorized_student is None:
        st.error("Access denied: Student record is unavailable.")
        st.stop()
    s = authorized_student

    profile = _student_profile(s)

    if st.button(
        "Run AI academic prediction",
        type="primary"
    ):

        try:
            marks, risk, label = predict_student(profile)

            save_prediction(
                s.student_id,
                "marks",
                marks,
                "Model estimate; not a guaranteed result."
            )

            save_prediction(
                s.student_id,
                "risk_probability",
                risk,
                label
            )

            st.session_state[
                f"prediction_{s.student_id}"
            ] = (marks, risk, label)

            st.success("AI prediction completed.")

        except Exception as e:
            st.error(f"Prediction failed: {e}")

    result = st.session_state.get(
        f"prediction_{s.student_id}"
    )

    if result:

        marks, risk, label = result

        a, b, c = st.columns(3)

        a.metric(
            "Predicted marks",
            f"{marks:.1f}/100"
        )

        b.metric(
            "Academic risk probability",
            f"{risk * 100:.1f}%"
        )

        c.metric(
            "Current risk indicator",
            label
        )

        st.caption(
            "This is a model estimate from available features, "
            "not a guarantee or a high-stakes decision. "
            "Discuss support needs with faculty."
        )


# --------------------------------------------------
# CAREER RECOMMENDATION PANEL
# --------------------------------------------------

def _career_panel(s):

    profile = _student_profile(s)

    recs = recommend_careers(profile)

    st.subheader("Career Recommendations")

    st.caption(
        "Profile-match suggestions for exploration, "
        "not an aptitude diagnosis or guaranteed career outcome."
    )

    for r in recs:

        with st.container(border=True):

            st.write(
                f"**{r['career']} - {r['match_score']}% profile match**"
            )

            st.progress(
                min(1.0, r["match_score"] / 100)
            )

            st.caption(
                f"Interest overlap: {r['matched_interests']}"
            )

            st.write(
                "Suggested learning path: "
                + " -> ".join(r["learning_path"])
            )

            gaps = skill_gap(
                profile,
                r["career"]
            )

            if gaps:

                st.write("Potential skill gaps:")

                st.write(
                    ", ".join(
                        g["skill"] for g in gaps
                    )
                )

            else:

                st.write(
                    "No major gaps in the two skills "
                    "assessed by this prototype."
                )


# --------------------------------------------------
# STUDENT PERFORMANCE ANALYTICS
# --------------------------------------------------

def _performance_analytics(s):

    st.subheader("Academic Performance Analytics")

    st.caption(
        "Analysis of your latest saved academic profile "
        "and AI prediction history."
    )

    summary = get_performance_summary(
        s.student_id
    )

    if not summary:

        st.warning(
            "Student performance data is unavailable."
        )
        return

    # Academic overview

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Attendance",
        f"{summary['attendance']:.1f}%"
    )

    c2.metric(
        "Internal Marks",
        f"{summary['internal_marks']:.1f}%"
    )

    c3.metric(
        "Assignment Score",
        f"{summary['assignment_score']:.1f}%"
    )

    c4.metric(
        "Previous GPA",
        f"{summary['previous_gpa']:.2f}/10"
    )

    st.divider()

    # Academic indicators

    st.subheader("Academic Indicators")

    academic_data = pd.DataFrame({
        "Metric": [
            "Attendance",
            "Internal Marks",
            "Assignment Score"
        ],
        "Score": [
            summary["attendance"],
            summary["internal_marks"],
            summary["assignment_score"]
        ]
    })

    fig = px.bar(
        academic_data,
        x="Metric",
        y="Score",
        color="Metric",
        range_y=[0, 100],
        title="Current Academic Performance",
        text_auto=".1f"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # Skills overview

    st.subheader("Skills Assessment")

    skill_data = pd.DataFrame({
        "Skill": [
            "Programming",
            "Communication",
            "Analytical"
        ],
        "Level": [
            summary["programming_skill"],
            summary["communication_skill"],
            summary["analytical_skill"]
        ]
    })

    fig2 = px.bar(
        skill_data,
        x="Skill",
        y="Level",
        range_y=[0, 5],
        color="Skill",
        title="Self-Reported Skill Levels",
        text_auto=True
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    st.divider()

    # Prediction history

    st.subheader("AI Prediction History")

    history = get_prediction_history(
        s.student_id
    )

    if history.empty:

        st.info(
            "No prediction history available. "
            "Run an AI prediction from the AI Prediction tab first."
        )

    else:

        marks_history = history[
            history["model_type"] == "marks"
        ].copy()

        risk_history = history[
            history["model_type"] == "risk_probability"
        ].copy()

        if not marks_history.empty:

            marks_history = marks_history.sort_values(
                ["created_at", "id"]
            )

            fig3 = px.line(
                marks_history,
                x="created_at",
                y="predicted_value",
                markers=True,
                title="Predicted Marks History",
                labels={
                    "created_at": "Prediction Date",
                    "predicted_value": "Predicted Marks"
                }
            )

            fig3.update_yaxes(
                range=[0, 100]
            )

            st.plotly_chart(
                fig3,
                use_container_width=True
            )

        if not risk_history.empty:

            risk_history = risk_history.sort_values(
                ["created_at", "id"]
            ).copy()

            risk_history["Risk Percentage"] = (
                risk_history["predicted_value"] * 100
            )

            fig4 = px.line(
                risk_history,
                x="created_at",
                y="Risk Percentage",
                markers=True,
                title="Academic Risk Probability History",
                labels={
                    "created_at": "Prediction Date",
                    "Risk Percentage": "Risk Probability (%)"
                }
            )

            fig4.update_yaxes(
                range=[0, 100]
            )

            st.plotly_chart(
                fig4,
                use_container_width=True
            )

        # Prediction records

        st.subheader("Saved Prediction Records")

        display_history = history.copy()

        display_history["created_at"] = pd.to_datetime(
            display_history["created_at"]
        ).dt.strftime("%d-%m-%Y %H:%M")

        display_history["predicted_value"] = (
            display_history.apply(
                lambda row: (
                    f"{row['predicted_value'] * 100:.1f}%"
                    if row["model_type"] == "risk_probability"
                    else f"{row['predicted_value']:.2f}"
                ),
                axis=1
            )
        )

        st.dataframe(
            display_history[
                [
                    "model_type",
                    "predicted_value",
                    "explanation",
                    "created_at"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # Study profile

    st.subheader("Study Profile")

    a, b = st.columns(2)

    a.metric(
        "Daily Study Hours",
        f"{summary['study_hours']:.1f} hours"
    )

    b.metric(
        "Current Semester",
        summary["semester"]
    )

    st.caption(
        "These charts describe the currently saved profile "
        "and recorded predictions. They do not represent "
        "verified semester-to-semester improvement or "
        "actual examination results."
    )


# --------------------------------------------------
# STUDENT PORTAL
# --------------------------------------------------

def student_page(user):
    _require_role(user, {"student"})


    st.header("Student Portal")

    s = _get_student(
        user.get("student_id") or "", user
    )

    if s is None:

        st.info(
            "Complete your profile to begin."
        )

        _profile_form(
            student_id=user.get("student_id") or "STU001",
            name=user["name"],
            actor=user
        )

        return

    tabs = st.tabs([
        "Overview",
        "Profile",
        "Performance Analytics",
        "AI Prediction",
        "Career & Learning",
        "Reports"
    ])

    # Tab 1: Overview

    with tabs[0]:

        st.subheader(
            f"Welcome, {s.name}"
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Attendance",
            f"{s.attendance:.0f}%"
        )

        c2.metric(
            "Internal Marks",
            f"{s.internal_marks:.0f}%"
        )

        c3.metric(
            "Previous GPA",
            f"{s.previous_gpa:.1f}/10"
        )

        st.info(
            "Keep your academic information updated "
            "so the analytics remain meaningful."
        )

    # Tab 2: Profile

    with tabs[1]:

        _profile_form(
            _student_profile(s) | {
                "name": s.name,
                "department": s.department,
                "semester": s.semester
            },
            student_id=s.student_id,
            name=s.name,
            actor=user
        )

    # Tab 3: Performance Analytics

    with tabs[2]:

        _performance_analytics(s)

    # Tab 4: AI Prediction

    with tabs[3]:

        _prediction_panel(s, user)

    # Tab 5: Career and Learning

    with tabs[4]:

        _career_panel(s)

    # Tab 6: Reports

    with tabs[5]:

        st.subheader("Academic Summary")

        report_data = {
            "Student ID": s.student_id,
            "Name": s.name,
            "Department": s.department,
            "Semester": s.semester,
            "Attendance": s.attendance,
            "Internal Marks": s.internal_marks,
            "Assignment Score": s.assignment_score,
            "Previous GPA": s.previous_gpa,
            "Daily Study Hours": s.study_hours
        }

        st.write(report_data)

        report_df = pd.DataFrame([
            report_data
        ])

        st.download_button(
            "Download Academic Summary",
            report_df.to_csv(index=False),
            file_name=f"{s.student_id}_academic_summary.csv",
            mime="text/csv",
            use_container_width=True
        )


# --------------------------------------------------
# FACULTY PORTAL
# --------------------------------------------------


def faculty_page(user):
    _require_role(user, {"faculty"})


    st.header("Faculty Portal")

    st.caption(
        "Department-wise academic monitoring, "
        "student management and AI-powered insights."
    )

    # Get department students using a department-scoped query.
    df = student_frame(department=user["department"])

    if df.empty:
        st.info("No student records available.")
        return

    if df.empty:
        st.warning(
            "No students found in your department."
        )
        return

    # Department overview
    st.subheader("Department Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Students", len(df))

    c2.metric(
        "Average Attendance",
        f"{df['attendance'].mean():.1f}%"
    )

    c3.metric(
        "Average Internal Marks",
        f"{df['internal_marks'].mean():.1f}%"
    )

    c4.metric(
        "Average GPA",
        f"{df['previous_gpa'].mean():.2f}/10"
    )

    st.divider()

    # Student search
    st.subheader("Student Management")

    search = st.text_input(
        "Search by Student ID or Name"
    )

    filtered_df = df.copy()

    if search.strip():

        search_value = search.strip().lower()

        filtered_df = filtered_df[
            filtered_df["student_id"].astype(str).str.lower().str.contains(
                search_value, na=False
            )
            |
            filtered_df["name"].astype(str).str.lower().str.contains(
                search_value, na=False
            )
        ]

    if filtered_df.empty:

        st.warning("No matching students found.")

    else:

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True
        )

        selected_id = st.selectbox(
            "Select a student",
            filtered_df["student_id"].tolist()
        )

        selected_student = _get_student(selected_id, user)

        if selected_student:

            st.divider()

            st.subheader(
                f"Student Profile: {selected_student.name}"
            )

            a, b, c, d = st.columns(4)

            a.metric(
                "Attendance",
                f"{selected_student.attendance:.1f}%"
            )

            b.metric(
                "Internal Marks",
                f"{selected_student.internal_marks:.1f}%"
            )

            c.metric(
                "Assignment Score",
                f"{selected_student.assignment_score:.1f}%"
            )

            d.metric(
                "Previous GPA",
                f"{selected_student.previous_gpa:.2f}"
            )

            # Edit student profile
            with st.expander(
                "Update Student Academic Profile"
            ):

                _profile_form(
                    _student_profile(selected_student) | {
                        "name": selected_student.name,
                        "department": selected_student.department,
                        "semester": selected_student.semester
                    },
                    student_id=selected_student.student_id,
                    name=selected_student.name,
                    actor=user
                )

            # Individual prediction
            st.divider()

            st.subheader("Individual AI Analysis")

            _prediction_panel(selected_student, user)

    st.divider()

    # Department analytics
    st.subheader("Department Performance Analytics")

    col1, col2 = st.columns(2)

    with col1:

        fig1 = px.scatter(
            df,
            x="attendance",
            y="internal_marks",
            color="semester",
            hover_name="student_id",
            title="Attendance vs Internal Marks",
            labels={
                "attendance": "Attendance (%)",
                "internal_marks": "Internal Marks (%)"
            }
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    with col2:

        fig2 = px.box(
            df,
            x="semester",
            y="previous_gpa",
            title="GPA Distribution by Semester"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # Student-wise attendance
    fig3 = px.bar(
        df.sort_values("attendance"),
        x="student_id",
        y="attendance",
        color="attendance",
        title="Student-wise Attendance",
        range_y=[0, 100]
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # Download department records
    st.subheader("Department Reports")

    st.download_button(
        "Download Department Student Report",
        df.to_csv(index=False),
        file_name="department_student_report.csv",
        mime="text/csv",
        use_container_width=True
    )



# --------------------------------------------------
# HOD PORTAL
# --------------------------------------------------


def hod_page(user):
    _require_role(user, {"hod"})


    st.header("HOD - Institutional Intelligence")

    st.caption(
        "Department-level academic performance, "
        "attendance monitoring and student insights."
    )

    df = student_frame(department=user["department"])

    if df.empty:
        st.warning("No student records available.")
        return

    if df.empty:
        st.warning(
            "No records found for your department."
        )
        return

    # Department KPIs
    st.subheader("Department Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Students", len(df))
    c2.metric(
        "Average Attendance",
        f"{df['attendance'].mean():.1f}%"
    )
    c3.metric(
        "Average Internal Marks",
        f"{df['internal_marks'].mean():.1f}%"
    )
    c4.metric(
        "Average GPA",
        f"{df['previous_gpa'].mean():.2f}/10"
    )

    st.divider()

    # Attendance monitoring
    st.subheader("Attendance Monitoring")

    low_attendance = df[
        df["attendance"] < 75
    ].copy()

    a, b = st.columns(2)

    a.metric(
        "Below 75% Attendance",
        len(low_attendance)
    )

    a.metric(
        "Attendance Compliance",
        f"{(len(df) - len(low_attendance)) / len(df) * 100:.1f}%"
    )

    with b:
        fig = px.histogram(
            df,
            x="attendance",
            nbins=10,
            title="Attendance Distribution"
        )

        fig.add_vline(
            x=75,
            line_dash="dash",
            annotation_text="75% reference"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    if not low_attendance.empty:

        st.warning(
            "Students below the 75% attendance reference threshold"
        )

        st.dataframe(
            low_attendance[
                [
                    "student_id",
                    "name",
                    "attendance",
                    "semester"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.success(
            "No students are currently below the 75% reference threshold."
        )

    st.divider()

    # Academic performance
    st.subheader("Academic Performance")

    col1, col2 = st.columns(2)

    with col1:

        fig1 = px.box(
            df,
            x="semester",
            y="internal_marks",
            title="Internal Marks by Semester"
        )

        st.plotly_chart(
            fig1,
            use_container_width=True
        )

    with col2:

        fig2 = px.histogram(
            df,
            x="previous_gpa",
            nbins=10,
            title="GPA Distribution"
        )

        st.plotly_chart(
            fig2,
            use_container_width=True
        )

    # Semester comparison
    st.subheader("Semester-wise Department Summary")

    semester_summary = (
        df.groupby("semester")
        .agg(
            Students=("student_id", "count"),
            Avg_Attendance=("attendance", "mean"),
            Avg_Internal_Marks=("internal_marks", "mean"),
            Avg_GPA=("previous_gpa", "mean")
        )
        .reset_index()
    )

    st.dataframe(
        semester_summary.round(2),
        use_container_width=True,
        hide_index=True
    )

    fig3 = px.bar(
        semester_summary,
        x="semester",
        y="Avg_Internal_Marks",
        color="semester",
        title="Average Internal Marks by Semester"
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    st.divider()

    # Student performance groups
    st.subheader("Student Performance Overview")

    top_students = df.sort_values(
        ["previous_gpa", "internal_marks"],
        ascending=False
    ).head(5)

    support_students = df.sort_values(
        ["previous_gpa", "internal_marks"],
        ascending=True
    ).head(5)

    left, right = st.columns(2)

    with left:

        st.markdown("**Top 5 GPA Profiles**")

        st.dataframe(
            top_students[
                [
                    "student_id",
                    "name",
                    "previous_gpa",
                    "internal_marks"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    with right:

        st.markdown("**5 Profiles for Academic Review**")

        st.dataframe(
            support_students[
                [
                    "student_id",
                    "name",
                    "previous_gpa",
                    "internal_marks"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "These lists use current recorded GPA and internal marks. "
        "They are monitoring indicators, not final student rankings "
        "or automatic decisions."
    )

    st.divider()

    # Complete records
    st.subheader("Department Student Records")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "Download HOD Department Report",
        df.to_csv(index=False),
        file_name="hod_department_report.csv",
        mime="text/csv",
        use_container_width=True
    )



# --------------------------------------------------
# ADMIN PORTAL
# --------------------------------------------------


def admin_page(user):
    _require_role(user, {"admin"})


    st.header("Admin - System Administration")

    st.caption(
        "Centralized system monitoring, user management, "
        "academic data quality and AI model evaluation."
    )

    df = student_frame()

    db = SessionLocal()

    try:
        users = db.scalars(
            select(User)
        ).all()

        user_data = [
            {
                "Username": u.username,
                "Name": u.name,
                "Role": u.role,
                "Department": u.department,
                "Student ID": u.student_id or "-"
            }
            for u in users
        ]

    finally:
        db.close()

    # SYSTEM OVERVIEW
    st.subheader("System Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total Students", len(df))
    c2.metric("Total User Accounts", len(user_data))

    c3.metric(
        "Departments",
        df["department"].nunique() if not df.empty else 0
    )

    c4.metric(
        "Average Attendance",
        f"{df['attendance'].mean():.1f}%"
        if not df.empty else "N/A"
    )

    st.divider()

    # USER MANAGEMENT
    st.subheader("User Management")

    user_df = pd.DataFrame(user_data)

    if not user_df.empty:

        role_counts = (
            user_df["Role"]
            .value_counts()
            .rename_axis("Role")
            .reset_index(name="Accounts")
        )

        left, right = st.columns(2)

        with left:

            st.dataframe(
                role_counts,
                use_container_width=True,
                hide_index=True
            )

        with right:

            fig = px.pie(
                role_counts,
                names="Role",
                values="Accounts",
                title="Role-wise Account Distribution"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.subheader("Registered Accounts")

        st.dataframe(
            user_df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("No user accounts found.")

    st.divider()

    # DATA QUALITY MONITORING
    st.subheader("Student Data Quality")

    if not df.empty:

        quality_checks = {
            "Missing Student IDs": int(
                df["student_id"].isna().sum()
            ),
            "Missing Names": int(
                df["name"].isna().sum()
            ),
            "Missing Attendance": int(
                df["attendance"].isna().sum()
            ),
            "Missing Internal Marks": int(
                df["internal_marks"].isna().sum()
            ),
            "Missing GPA": int(
                df["previous_gpa"].isna().sum()
            )
        }

        quality_df = pd.DataFrame(
            list(quality_checks.items()),
            columns=["Quality Check", "Issue Count"]
        )

        st.dataframe(
            quality_df,
            use_container_width=True,
            hide_index=True
        )

        total_issues = sum(
            quality_checks.values()
        )

        if total_issues == 0:

            st.success(
                "No missing values found in the monitored fields."
            )

        else:

            st.warning(
                f"{total_issues} missing-value issues found."
            )

        invalid_checks = {
            "Attendance outside 0-100": int(
                (
                    (df["attendance"] < 0)
                    | (df["attendance"] > 100)
                ).sum()
            ),
            "Internal marks outside 0-100": int(
                (
                    (df["internal_marks"] < 0)
                    | (df["internal_marks"] > 100)
                ).sum()
            ),
            "GPA outside 0-10": int(
                (
                    (df["previous_gpa"] < 0)
                    | (df["previous_gpa"] > 10)
                ).sum()
            )
        }

        st.markdown("**Invalid Value Checks**")

        st.dataframe(
            pd.DataFrame(
                list(invalid_checks.items()),
                columns=["Validation", "Invalid Records"]
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Student data is not available for quality checks."
        )

    st.divider()

    # AI MODEL MANAGEMENT
    st.subheader("AI Model Management")

    st.caption(
        "Model metrics currently reflect the configured "
        "training data. Synthetic demonstration metrics "
        "must not be interpreted as real-world validation."
    )

    try:

        metrics = model_metrics()

        st.markdown("**Current Model Evaluation**")

        st.json(metrics)

    except Exception as e:

        st.warning(
            f"Model metrics unavailable: {e}"
        )

    if st.button(
        "Train / Retrain AI Models",
        type="primary"
    ):

        try:

            with st.spinner(
                "Training AI models..."
            ):

                result = train_models()

            st.success(
                "AI models trained successfully."
            )

            st.json(result)

        except Exception as e:

            st.error(
                f"Model training failed: {e}"
            )

    st.divider()

    # STUDENT DATA EXPORT
    st.subheader("Student Data Export")

    if not df.empty:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download All Student Records",
            df.to_csv(index=False),
            file_name="eduinsight_all_students.csv",
            mime="text/csv",
            use_container_width=True
        )

    else:

        st.info("No student records available for export.")

    st.divider()

    # ACCOUNT CREATION
    st.subheader("Create New User Account")

    with st.form("admin_create_user"):

        username = st.text_input("Username")

        name = st.text_input("Full Name")

        password = st.text_input(
            "Temporary Password",
            type="password"
        )

        role = st.selectbox(
            "Account Role",
            ["student", "faculty", "hod", "admin"]
        )

        sid = st.text_input(
            "Student ID (Required for Student)"
        )

        dept = st.text_input(
            "Department",
            value="CSE"
        )

        submitted = st.form_submit_button(
            "Create Account",
            use_container_width=True
        )

    if submitted:

        from src.auth import _hash

        db = SessionLocal()

        try:

            if (
                not username.strip()
                or not name.strip()
                or len(password) < 8
                or not dept.strip()
            ):

                st.error(
                    "Enter all required details. "
                    "Password must contain at least 8 characters."
                )

            elif role == "student" and not sid.strip():

                st.error(
                    "Student ID is required for student accounts."
                )

            elif db.scalar(
                select(User).where(
                    User.username == username.strip()
                )
            ):

                st.error(
                    "Username already exists."
                )

            elif (
                role == "student"
                and db.scalar(
                    select(User).where(
                        User.student_id == sid.strip()
                    )
                )
            ):

                st.error(
                    "This Student ID is already linked to an account."
                )

            else:

                db.add(
                    User(
                        username=username.strip(),
                        password_hash=_hash(password),
                        name=name.strip(),
                        role=role,
                        student_id=sid.strip() or None,
                        department=dept.strip()
                    )
                )

                db.commit()

                st.success(
                    "User account created successfully."
                )

                st.rerun()

        except Exception as e:

            db.rollback()

            st.error(
                f"Account creation failed: {e}"
            )

        finally:

            db.close()



# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

def home_page():

    st.write(
        "Welcome to EduInsight AI."
    )
