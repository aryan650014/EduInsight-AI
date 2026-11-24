import streamlit as st
from src.config import APP_NAME
from src.auth import login, logout, current_user, ensure_demo_users
from src.database import init_db
from src.ui import student_page, faculty_page, hod_page, admin_page, home_page

st.set_page_config(page_title=APP_NAME, page_icon="🎓", layout="wide")
init_db()
ensure_demo_users()

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: #f5f7fb; padding: 14px; border-radius: 12px;}
div.stButton > button {border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

st.title("🎓 EduInsight AI")
st.caption("Student Performance & Career Prediction Intelligence Platform")

user = current_user()
if not user:
    login()
else:
    with st.sidebar:
        st.success(f"Signed in as **{user['name']}**")
        st.caption(f"Role: {user['role'].title()}")
        if st.button("Sign out", use_container_width=True):
            logout()
    if user["role"] == "student":
        student_page(user)
    elif user["role"] == "faculty":
        faculty_page(user)
    elif user["role"] == "hod":
        hod_page(user)
    else:
        admin_page(user)
