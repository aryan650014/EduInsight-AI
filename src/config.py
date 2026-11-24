
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def get_setting(name, default=None):
    """Read settings from environment variables or Streamlit Cloud secrets."""
    value = os.getenv(name)

    if value is not None:
        return value

    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"

DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

APP_NAME = "EduInsight AI"

APP_ENV = str(
    get_setting("APP_ENV", "development")
).strip().lower()

IS_PRODUCTION = APP_ENV in {"production", "prod"}

DATABASE_URL = get_setting(
    "DATABASE_URL",
    f"sqlite:///{DATA_DIR / 'eduinsight.db'}"
)

_demo_setting = get_setting("ENABLE_DEMO_USERS")

if _demo_setting is None:
    ENABLE_DEMO_USERS = not IS_PRODUCTION
else:
    ENABLE_DEMO_USERS = str(_demo_setting).strip().lower() in {
        "1", "true", "yes", "on"
    }

if IS_PRODUCTION and ENABLE_DEMO_USERS:
    raise RuntimeError(
        "Demo users must be disabled in production."
    )

APP_SECRET = str(get_setting("APP_SECRET", "")).strip()

if not APP_SECRET:
    if IS_PRODUCTION:
        raise RuntimeError(
            "APP_SECRET must be configured before production deployment."
        )
    APP_SECRET = "development-only-change-me"

if IS_PRODUCTION and APP_SECRET.lower() in {
    "change-this-before-deployment",
    "development-only-change-me",
    "secret",
    "changeme"
}:
    raise RuntimeError(
        "Please configure a strong APP_SECRET for production."
    )
