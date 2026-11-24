import pandas as pd

CAREERS = {
    "Data Analyst": {"skills": ["analytical_skill", "communication_skill"], "interests": ["data", "analytics", "business"], "learn": ["SQL", "Excel/Power BI", "Statistics", "Python", "Dashboard design"]},
    "Data Scientist": {"skills": ["analytical_skill", "programming_skill"], "interests": ["data", "research", "machine learning", "ai"], "learn": ["Python", "Statistics", "Machine Learning", "SQL", "Model evaluation"]},
    "Software Developer": {"skills": ["programming_skill", "analytical_skill"], "interests": ["software", "development", "coding", "web"], "learn": ["DSA", "OOP", "DBMS", "Git", "Web/API development"]},
    "AI/ML Engineer": {"skills": ["programming_skill", "analytical_skill"], "interests": ["ai", "machine learning", "automation", "research"], "learn": ["Python", "Linear Algebra", "ML", "Deep Learning", "MLOps"]},
    "Cybersecurity Analyst": {"skills": ["analytical_skill", "programming_skill"], "interests": ["security", "network", "cybersecurity"], "learn": ["Networking", "Linux", "Security fundamentals", "Python", "SIEM basics"]},
    "Cloud Engineer": {"skills": ["programming_skill", "communication_skill"], "interests": ["cloud", "devops", "infrastructure"], "learn": ["Linux", "Networking", "AWS/Azure fundamentals", "Docker", "CI/CD"]},
    "Business Analyst": {"skills": ["communication_skill", "analytical_skill"], "interests": ["business", "management", "analytics"], "learn": ["Excel", "SQL", "Statistics", "Power BI", "Requirements analysis"]},
}

def recommend_careers(profile, top_k=3):
    interests = (profile.get("interests") or "").lower()
    rows = []
    for career, spec in CAREERS.items():
        skill_score = sum(float(profile.get(s, 3)) for s in spec["skills"]) / (5 * len(spec["skills"]))
        matched = [word for word in spec["interests"] if word in interests]
        interest_score = min(1.0, len(matched) / max(1, len(spec["interests"])))
        score = 0.65 * skill_score + 0.35 * interest_score
        rows.append({"career": career, "match_score": round(score*100, 1),
                     "matched_interests": ", ".join(matched) if matched else "Explore this field",
                     "learning_path": spec["learn"]})
    return sorted(rows, key=lambda x: x["match_score"], reverse=True)[:top_k]

def skill_gap(profile, career):
    spec = CAREERS[career]
    gaps = []
    for skill in spec["skills"]:
        val = float(profile.get(skill, 3))
        if val < 4:
            gaps.append({"skill": skill.replace("_", " ").title(), "current_level": val,
                         "target_level": 4, "priority": "High" if val <= 2 else "Medium"})
    return gaps
