from src.database import SessionLocal, Student
from src.ml import make_demo_dataset
import pandas as pd

db = SessionLocal()
try:
    if db.query(Student).count() == 0:
        df = make_demo_dataset(30)
        for i, r in df.iterrows():
            db.add(Student(
                student_id=f"DEMO{i+1:03d}", name=f"Demo Student {i+1}", department="CSE",
                semester=int(i % 8 + 1), attendance=float(r.attendance),
                internal_marks=float(r.internal_marks), assignment_score=float(r.assignment_score),
                study_hours=float(r.study_hours), previous_gpa=float(r.previous_gpa),
                programming_skill=int(r.programming_skill),
                communication_skill=int(r.communication_skill),
                analytical_skill=int(r.analytical_skill), interests="Data Analytics, Software Development"
            ))
        db.commit()
        print("Inserted 30 synthetic demo student profiles.")
    else:
        print("Student table already contains records; no rows inserted.")
finally:
    db.close()
