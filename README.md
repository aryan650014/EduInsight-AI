# EduInsight AI
**AI-Based Student Performance & Career Prediction Intelligence System**
Final-year B.Tech CSE major project | Streamlit + Python + ML + SQL

## 1. Project scope
EduInsight AI is a modular educational analytics prototype with four roles:
- **Student:** profile, academic overview, marks prediction, career matching and learning roadmap.
- **Faculty:** view departmental student records, add/update academic records and run predictions.
- **HOD:** department-level academic analytics and comparisons.
- **Admin:** model training, data export and user account management.

The implementation includes profile management, academic analytics, marks prediction, academic-risk indicators, skill-gap analysis, career recommendations, learning suggestions, faculty/HOD dashboards, reporting/export and administration.

> **Data integrity notice:** The included starter training data is synthetic demonstration data. It is not real college data, and model metrics from it are not evidence of real-world accuracy. Replace it with an appropriately licensed, validated dataset before making academic claims. Do not use predictions to deny admission, scholarships, placements or other opportunities.

## 2. Requirements
- Python 3.10â€“3.12 recommended
- VS Code or another Python IDE
- Internet connection for installing packages and optional cloud deployment

## 3. Run locally (Windows PowerShell)
```powershell
cd EduInsight_AI
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python scripts\generate_demo_data.py
python scripts\seed_students.py
python scripts\train_models.py
streamlit run app.py
```
Open the local URL printed by Streamlit, normally `http://localhost:8501`.

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Demo accounts
| Role | Username | Initial password |
|---|---|---|
Demo accounts are for local development only.
Production demo accounts are disabled.

Change these passwords and remove demo accounts before any public deployment. Demo credentials are for local evaluation only.

## 5. Training data format
Place a CSV at `data/student_training_data.csv` with these columns:
```text
attendance,internal_marks,assignment_score,study_hours,previous_gpa,
programming_skill,communication_skill,analytical_skill,final_marks,academic_risk
```
Feature definitions:
- `attendance`: 0â€“100 percentage
- `internal_marks`, `assignment_score`, `final_marks`: 0â€“100
- `study_hours`: average self-reported hours/day
- `previous_gpa`: 0â€“10
- skill ratings: 1â€“5
- `academic_risk`: 0 = lower-risk class, 1 = support-needed class (define consistently from a defensible institutional rule)

Train:
```powershell
python scripts\train_models.py
```
The pipeline trains Random Forest regression for marks and Random Forest classification for the risk indicator, saves models in `models/` and writes evaluation metrics to `models/metrics.json`. Metrics are computed using a held-out split; use cross-validation and external validation for research-grade reporting.

## 6. Public dataset suggestions
Use original sources and check each dataset's licence, data dictionary and intended use:
- UCI Student Performance: https://archive.ics.uci.edu/dataset/320/student+performance
- UCI Predict Students' Dropout and Academic Success: https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success
- Open University Learning Analytics Dataset: https://analyse.kmi.open.ac.uk/open_dataset
- XAPI-Edu-Data: https://www.kaggle.com/datasets/aljarah/xAPI-Edu-Data

Datasets differ in population, feature definitions and target labels. Do not combine them blindly. Create a documented feature mapping and do not claim that a dropout label is equivalent to a final-marks target. The bundled model uses a clearly labelled synthetic dataset until a compatible real dataset has been prepared.

## 7. Database
SQLAlchemy models are created automatically at startup. SQLite is the default for quick local evaluation.
For cloud use, create a managed database and set `DATABASE_URL` in the hosting provider's secrets:
- MySQL example: `mysql+pymysql://USER:PASSWORD@HOST:3306/eduinsight` (install `pymysql`)
- PostgreSQL example: `postgresql+psycopg://USER:PASSWORD@HOST:5432/eduinsight` (install `psycopg[binary]`)

Do not commit `.env`, passwords, private student data or database files.

## 8. Cloud deployment (Streamlit Community Cloud)
1. Create a private GitHub repository and push this project (do not push `.env`, DB files or real student data).
2. Open https://share.streamlit.io/ and connect the repository.
3. Set the main file path to `app.py`.
4. Add required secrets/environment variables in the app settings. Set a strong `APP_SECRET` and a managed `DATABASE_URL`.
5. Deploy and test all roles.
6. Use a persistent managed database. The local SQLite file on an ephemeral cloud filesystem may be reset or unavailable across deployments.
7. Disable or replace demo users, enforce strong passwords, and review access controls before inviting real users.

For a production deployment with real student records, add HTTPS, account recovery, rate limiting, audit logs, backups, secure secret management, data-retention policies and institutional approval. This starter is an academic prototype, not a security-audited production system.

## 9. Tests
```powershell
pytest -q
```
Tests cover dataset schema, model training/prediction and career matching. Add integration tests for authentication, role-based data access and database persistence before deployment.

## 10. Project folder structure
```text
EduInsight_AI/
â”œâ”€â”€ app.py
â”œâ”€â”€ requirements.txt
â”œâ”€â”€ .env.example
â”œâ”€â”€ README.md
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ config.py
â”‚   â”œâ”€â”€ database.py
â”‚   â”œâ”€â”€ auth.py
â”‚   â”œâ”€â”€ ml.py
â”‚   â”œâ”€â”€ career.py
â”‚   â”œâ”€â”€ analytics.py
â”‚   â””â”€â”€ ui.py
â”œâ”€â”€ data/
â”‚   â””â”€â”€ README.md
â”œâ”€â”€ models/
â”‚   â””â”€â”€ README.md
â”œâ”€â”€ scripts/
â”‚   â”œâ”€â”€ generate_demo_data.py
â”‚   â”œâ”€â”€ seed_students.py
â”‚   â””â”€â”€ train_models.py
â””â”€â”€ tests/
    â”œâ”€â”€ test_ml.py
    â””â”€â”€ test_career.py
```

## 11. Limitations and responsible use
- Synthetic starter data is only for demonstrating the end-to-end pipeline.
- Career matching is a transparent profile similarity baseline, not a validated psychometric assessment.
- Risk indicators should trigger supportive review, never automatic punishment.
- Do not collect sensitive personal data unless necessary, consented to and institutionally approved.
- Use anonymized or pseudonymized student records and restrict access by role.
- Validate on representative, recent, institution-specific data before presenting performance claims.
- Monitor for bias across groups and provide students a way to correct inaccurate records.

## 12. Future enhancements
- Semester-wise longitudinal performance forecasting.
- Explainability using SHAP.
- Faculty intervention tracking.
- Course catalogue integration and content-based learning recommendations.
- Placement skill-gap analytics.
- Email notifications with consent.
- Audit trail and downloadable PDF reports.
- Multi-college comparison with privacy-preserving aggregation.

## 13. Academic evaluation checklist
- [ ] Clearly documented problem statement and objectives
- [ ] Dataset source, licence and data dictionary
- [ ] EDA and preprocessing notebook/report
- [ ] Baseline vs advanced model comparison
- [ ] MAE, RMSE, RÂ², precision, recall and F1 as applicable
- [ ] Train/test separation and leakage checks
- [ ] Database ER diagram and role permissions
- [ ] Screenshots and functional test cases
- [ ] Limitations, fairness and privacy discussion
- [ ] Deployment and user manual
