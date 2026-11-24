
import streamlit as st
import bcrypt
from sqlalchemy import select
from src.database import SessionLocal, User
from src.config import ENABLE_DEMO_USERS, get_setting
VALID_ROLES = {"student", "faculty", "hod", "admin"}


def _hash(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")



def ensure_demo_users():
    """Create demo accounts only when explicitly enabled and configured."""
    if not ENABLE_DEMO_USERS:
        return

    demo = [
        (
            "admin",
            get_setting("DEMO_ADMIN_PASSWORD"),
            "System Administrator",
            "admin",
            None
        ),
        (
            "hod",
            get_setting("DEMO_HOD_PASSWORD"),
            "Department HOD",
            "hod",
            None
        ),
        (
            "faculty",
            get_setting("DEMO_FACULTY_PASSWORD"),
            "Demo Faculty",
            "faculty",
            None
        ),
        (
            "student",
            get_setting("DEMO_STUDENT_PASSWORD"),
            "Demo Student",
            "student",
            "STU001"
        ),
    ]

    db = SessionLocal()
    try:
        for username, password, name, role, sid in demo:
            if not password:
                continue

            existing = db.scalar(
                select(User).where(User.username == username)
            )

            if existing is None:
                db.add(
                    User(
                        username=username,
                        password_hash=_hash(str(password)),
                        name=name,
                        role=role,
                        student_id=sid,
                        department="CSE"
                    )
                )

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def current_user():
    """Return a fresh database-validated user session."""
    session_user = st.session_state.get("edu_user")

    if not isinstance(session_user, dict):
        return None

    user_id = session_user.get("id")
    if not isinstance(user_id, int):
        st.session_state.pop("edu_user", None)
        return None

    db = SessionLocal()
    try:
        user = db.get(User, user_id)

        if user is None or user.role not in VALID_ROLES:
            st.session_state.pop("edu_user", None)
            return None

        # Refresh session data from the database.
        verified_user = {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "student_id": user.student_id,
            "department": user.department
        }

        st.session_state.edu_user = verified_user
        return verified_user
    finally:
        db.close()


def login():
    st.subheader("Sign in")

    if ENABLE_DEMO_USERS:
        st.info(
            "Development demo accounts are available. "
            "See README.md for local testing instructions."
        )

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button(
            "Sign in",
            use_container_width=True
        )

    if submitted:
        db = SessionLocal()
        try:
            user = db.scalar(
                select(User).where(
                    User.username == username.strip()
                )
            )

            valid_password = False

            if user:
                try:
                    valid_password = bcrypt.checkpw(
                        password.encode("utf-8"),
                        user.password_hash.encode("utf-8")
                    )
                except (ValueError, TypeError):
                    valid_password = False

            if (
                user
                and valid_password
                and user.role in VALID_ROLES
            ):
                st.session_state.edu_user = {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "role": user.role,
                    "student_id": user.student_id,
                    "department": user.department
                }
                st.rerun()
            else:
                st.error("Invalid username or password.")
        finally:
            db.close()


def logout():
    st.session_state.pop("edu_user", None)
    st.rerun()
