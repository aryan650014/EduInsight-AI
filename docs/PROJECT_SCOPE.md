# Project Scope and Academic Notes

## Research questions
1. Can academic and engagement features provide useful estimates of student performance?
2. Which features are associated with academic support needs in a defined dataset?
3. Can transparent skill-profile matching provide useful career exploration suggestions?
4. Can dashboards help faculty identify aggregate trends without automating high-stakes decisions?

## Suggested experiments
- Baseline: Linear Regression / Logistic Regression.
- Tree models: Random Forest, XGBoost or CatBoost.
- Compare regression MAE/RMSE/R² and classification precision/recall/F1.
- Evaluate by semester or cohort where sample size permits.
- Use a temporal holdout when records span multiple semesters.
- Document dataset shift, missingness, fairness and limitations.

## Non-goals
- Diagnosing student ability or personality.
- Guaranteeing marks, placements or career success.
- Automatically making disciplinary, admission, scholarship or placement decisions.
