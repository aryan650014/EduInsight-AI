from src.career import recommend_careers, skill_gap

def test_recommendations_return_ranked_results():
    profile = {"programming_skill": 5, "analytical_skill": 5,
               "communication_skill": 3, "interests": "AI, data, machine learning"}
    recs = recommend_careers(profile)
    assert len(recs) == 3
    assert recs[0]["match_score"] >= recs[-1]["match_score"]

def test_skill_gap():
    gaps = skill_gap({"programming_skill": 2, "analytical_skill": 4}, "Software Developer")
    assert any(x["skill"] == "Programming Skill" for x in gaps)
