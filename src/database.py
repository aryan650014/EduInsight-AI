from sqlalchemy import create_engine, String, Integer, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, sessionmaker, relationship
from datetime import datetime
from src.config import DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20))
    student_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    department: Mapped[str] = mapped_column(String(80), default="CSE")

class Student(Base):
    __tablename__ = "students"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    department: Mapped[str] = mapped_column(String(80), default="CSE")
    semester: Mapped[int] = mapped_column(Integer, default=1)
    attendance: Mapped[float] = mapped_column(Float, default=75)
    internal_marks: Mapped[float] = mapped_column(Float, default=60)
    assignment_score: Mapped[float] = mapped_column(Float, default=60)
    study_hours: Mapped[float] = mapped_column(Float, default=2)
    previous_gpa: Mapped[float] = mapped_column(Float, default=6.5)
    programming_skill: Mapped[int] = mapped_column(Integer, default=3)
    communication_skill: Mapped[int] = mapped_column(Integer, default=3)
    analytical_skill: Mapped[int] = mapped_column(Integer, default=3)
    interests: Mapped[str] = mapped_column(Text, default="Software Development")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    model_type: Mapped[str] = mapped_column(String(40))
    predicted_value: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[str] = mapped_column(String(40), index=True)
    category: Mapped[str] = mapped_column(String(40))
    title: Mapped[str] = mapped_column(String(160))
    details: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)
