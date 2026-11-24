from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, classification_report
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from src.config import MODEL_DIR, DATA_DIR

FEATURES = ["attendance", "internal_marks", "assignment_score", "study_hours",
            "previous_gpa", "programming_skill", "communication_skill", "analytical_skill"]

def make_demo_dataset(n=1200, seed=42):
    """Synthetic teaching/demo data. Not real student records or validated institutional evidence."""
    rng = np.random.default_rng(seed)
    attendance = rng.uniform(35, 100, n)
    internal = rng.uniform(15, 100, n)
    assignment = rng.uniform(10, 100, n)
    study = rng.uniform(0, 8, n)
    gpa = rng.uniform(3.0, 10.0, n)
    prog = rng.integers(1, 6, n)
    comm = rng.integers(1, 6, n)
    analytical = rng.integers(1, 6, n)
    noise = rng.normal(0, 7, n)
    final = (0.20*attendance + 0.30*internal + 0.15*assignment +
             2.2*study + 2.4*gpa + 1.2*prog + 0.5*comm + 0.8*analytical + noise)
    final = np.clip(final, 0, 100)
    risk = ((attendance < 60) | (gpa < 5.0) | (final < 45)).astype(int)
    return pd.DataFrame({
        "attendance": attendance, "internal_marks": internal,
        "assignment_score": assignment, "study_hours": study,
        "previous_gpa": gpa, "programming_skill": prog,
        "communication_skill": comm, "analytical_skill": analytical,
        "final_marks": final, "academic_risk": risk
    })

def train_models(df=None):
    if df is None:
        path = DATA_DIR / "student_training_data.csv"
        df = pd.read_csv(path) if path.exists() else make_demo_dataset()
    required = FEATURES + ["final_marks", "academic_risk"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Training dataset missing columns: {missing}")
    X = df[FEATURES]
    y_reg = df["final_marks"].astype(float)
    y_cls = df["academic_risk"].astype(int)
    X_train, X_test, yr_train, yr_test = train_test_split(X, y_reg, test_size=.2, random_state=42)
    _, _, yc_train, yc_test = train_test_split(X, y_cls, test_size=.2, random_state=42, stratify=y_cls)
    reg = Pipeline([("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("model", RandomForestRegressor(n_estimators=250, max_depth=12, random_state=42, n_jobs=-1))])
    clf = Pipeline([("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                    ("model", RandomForestClassifier(n_estimators=250, max_depth=12, class_weight="balanced",
                                                     random_state=42, n_jobs=-1))])
    reg.fit(X_train, yr_train)
    clf.fit(X_train, yc_train)
    pred = reg.predict(X_test)
    metrics = {
        "mae": float(mean_absolute_error(yr_test, pred)),
        "rmse": float(np.sqrt(mean_squared_error(yr_test, pred))),
        "r2": float(r2_score(yr_test, pred)),
        "risk_accuracy": float(clf.score(X_test, yc_test)),
        "training_rows": int(len(df)),
        "data_note": "Synthetic demonstration data" if df.equals(make_demo_dataset(n=len(df))) else "User-supplied dataset"
    }
    joblib.dump(reg, MODEL_DIR / "marks_model.joblib")
    joblib.dump(clf, MODEL_DIR / "risk_model.joblib")
    (MODEL_DIR / "metrics.json").write_text(__import__("json").dumps(metrics, indent=2))
    return metrics

def load_models():
    rp, cp = MODEL_DIR / "marks_model.joblib", MODEL_DIR / "risk_model.joblib"
    if not rp.exists() or not cp.exists():
        train_models()
    return joblib.load(rp), joblib.load(cp)

def predict_student(payload):
    reg, clf = load_models()
    X = pd.DataFrame([{k: float(payload[k]) for k in FEATURES}], columns=FEATURES)
    marks = float(np.clip(reg.predict(X)[0], 0, 100))
    risk_probability = float(clf.predict_proba(X)[0][1])
    risk_label = "Needs attention" if risk_probability >= .5 else "Lower current risk"
    return marks, risk_probability, risk_label

def model_metrics():
    import json
    path = MODEL_DIR / "metrics.json"
    if not path.exists():
        train_models()
    return json.loads(path.read_text())
