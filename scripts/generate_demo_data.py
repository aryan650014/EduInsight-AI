from src.ml import make_demo_dataset
from src.config import DATA_DIR
df = make_demo_dataset()
path = DATA_DIR / "student_training_data.csv"
df.to_csv(path, index=False)
print(f"Created {path} with {len(df)} synthetic demonstration rows.")
