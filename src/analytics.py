
import pandas as pd
from sqlalchemy import select, desc, func

from src.database import SessionLocal, Student, Prediction


STUDENT_COLUMNS = [
    "student_id", "name", "department", "semester",
    "attendance", "internal_marks", "assignment_score",
    "study_hours", "previous_gpa", "programming_skill",
    "communication_skill", "analytical_skill", "interests"
]


PREDICTION_COLUMNS = [
    "id", "student_id", "model_type",
    "predicted_value", "explanation", "created_at"
]


def student_frame(department=None):
    """Return student records as a pandas DataFrame."""
    db = SessionLocal()

    try:
        query = select(Student)

        if department:
            query = query.where(Student.department == department)

        rows = db.scalars(query).all()

        records = [
            {
                "student_id": x.student_id,
                "name": x.name,
                "department": x.department,
                "semester": x.semester,
                "attendance": x.attendance,
                "internal_marks": x.internal_marks,
                "assignment_score": x.assignment_score,
                "study_hours": x.study_hours,
                "previous_gpa": x.previous_gpa,
                "programming_skill": x.programming_skill,
                "communication_skill": x.communication_skill,
                "analytical_skill": x.analytical_skill,
                "interests": x.interests,
            }
            for x in rows
        ]

        return pd.DataFrame(records, columns=STUDENT_COLUMNS)

    finally:
        db.close()


def save_prediction(student_id, model_type, value, explanation):
    """Save an AI prediction in the database."""
    db = SessionLocal()

    try:
        prediction = Prediction(
            student_id=student_id,
            model_type=model_type,
            predicted_value=float(value),
            explanation=explanation or ""
        )

        db.add(prediction)
        db.commit()

        return prediction.id

    finally:
        db.close()


def get_prediction_history(student_id, model_type=None, limit=100):
    """Fetch recent predictions for an individual student."""
    db = SessionLocal()

    try:
        query = select(Prediction).where(
            Prediction.student_id == student_id
        )

        if model_type:
            query = query.where(
                Prediction.model_type == model_type
            )

        query = query.order_by(
            desc(Prediction.created_at),
            desc(Prediction.id)
        ).limit(max(1, int(limit)))

        rows = db.scalars(query).all()

        records = [
            {
                "id": x.id,
                "student_id": x.student_id,
                "model_type": x.model_type,
                "predicted_value": x.predicted_value,
                "explanation": x.explanation,
                "created_at": x.created_at
            }
            for x in rows
        ]

        return pd.DataFrame(records, columns=PREDICTION_COLUMNS)

    finally:
        db.close()


def get_latest_prediction(student_id, model_type):
    """Return the latest prediction of a particular type."""
    db = SessionLocal()

    try:
        query = (
            select(Prediction)
            .where(
                Prediction.student_id == student_id,
                Prediction.model_type == model_type
            )
            .order_by(
                desc(Prediction.created_at),
                desc(Prediction.id)
            )
            .limit(1)
        )

        prediction = db.scalar(query)

        if prediction is None:
            return None

        return {
            "id": prediction.id,
            "model_type": prediction.model_type,
            "predicted_value": prediction.predicted_value,
            "explanation": prediction.explanation,
            "created_at": prediction.created_at
        }

    finally:
        db.close()


def get_performance_summary(student_id):
    """Generate a current academic summary for a student."""
    db = SessionLocal()

    try:
        student = db.scalar(
            select(Student).where(Student.student_id == student_id)
        )

        if student is None:
            return None

        return {
            "student_id": student.student_id,
            "name": student.name,
            "department": student.department,
            "semester": student.semester,
            "attendance": float(student.attendance),
            "internal_marks": float(student.internal_marks),
            "assignment_score": float(student.assignment_score),
            "study_hours": float(student.study_hours),
            "previous_gpa": float(student.previous_gpa),
            "programming_skill": int(student.programming_skill),
            "communication_skill": int(student.communication_skill),
            "analytical_skill": int(student.analytical_skill),
            "updated_at": student.updated_at
        }

    finally:
        db.close()


def get_department_summary(department=None):
    """Calculate department-level academic indicators."""
    df = student_frame(department)

    if df.empty:
        return {
            "total_students": 0,
            "average_attendance": 0,
            "average_internal_marks": 0,
            "average_gpa": 0,
            "average_assignment_score": 0,
            "semester_count": 0
        }

    return {
        "total_students": int(len(df)),
        "average_attendance": round(float(df["attendance"].mean()), 2),
        "average_internal_marks": round(float(df["internal_marks"].mean()), 2),
        "average_gpa": round(float(df["previous_gpa"].mean()), 2),
        "average_assignment_score": round(
            float(df["assignment_score"].mean()), 2
        ),
        "semester_count": int(df["semester"].nunique())
    }


def get_prediction_counts(student_id):
    """Count saved predictions by model type."""
    db = SessionLocal()

    try:
        rows = db.execute(
            select(
                Prediction.model_type,
                func.count(Prediction.id)
            )
            .where(Prediction.student_id == student_id)
            .group_by(Prediction.model_type)
        ).all()

        return {
            model_type: int(count)
            for model_type, count in rows
        }

    finally:
        db.close()
