
import getpass

import bcrypt
from sqlalchemy import select

from src.database import Base, engine, SessionLocal, User


def main():
    print("\nEduInsight AI - Create Admin Account\n")

    Base.metadata.create_all(bind=engine)

    username = input("Admin username: ").strip()
    name = input("Admin full name: ").strip()
    department = input("Department [CSE]: ").strip() or "CSE"

    if not username or not name:
        print("Username and name are required.")
        return

    password = getpass.getpass("Create password (minimum 12 characters): ")
    confirm = getpass.getpass("Confirm password: ")

    if len(password) < 12:
        print("Password must contain at least 12 characters.")
        return

    if password != confirm:
        print("Passwords do not match.")
        return

    db = SessionLocal()

    try:
        existing = db.scalar(
            select(User).where(User.username == username)
        )

        if existing:
            print("This username already exists. No account was changed.")
            return

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        admin = User(
            username=username,
            password_hash=password_hash,
            name=name,
            role="admin",
            student_id=None,
            department=department
        )

        db.add(admin)
        db.commit()

        print(f"\nAdmin account '{username}' created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
