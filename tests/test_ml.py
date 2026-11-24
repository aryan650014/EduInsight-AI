from src.ml import make_demo_dataset, train_models, predict_student, FEATURES

def test_demo_data_schema():
    df = make_demo_dataset(100)
    assert all(c in df.columns for c in FEATURES + ["final_marks", "academic_risk"])

def test_training_and_prediction():
    df = make_demo_dataset(180)
    metrics = train_models(df)
    assert metrics["mae"] >= 0
    payload = {c: float(df.iloc[0][c]) for c in FEATURES}
    marks, risk, label = predict_student(payload)
    assert 0 <= marks <= 100
    assert 0 <= risk <= 1
    assert label in ["Needs attention", "Lower current risk"]
