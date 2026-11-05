from datetime import date

import pytest

from matching import MatchConfig, MatchingEngine
from matching.models import Candidate, Company, Dataset, Job

AS_OF = date(2026, 10, 22)


def make(cand_kw=None, job_kw=None):
    c = Candidate(profile_id="c1", user_id="u1", display_name="Test Person", open_to_work=True,
                  job_search_status="Actively looking", fcra_consent=True, residency="CITIZEN",
                  location="Chicago, IL", work_type="Hybrid", employment_type="Full-time",
                  target_compensation=70000, availability="Immediately", experience="INTERNSHIP",
                  highest_education="BACHELORS", industry_interests=["Software"], core_values=["Integrity", "Growth"],
                  hard_skills=["SQL", "Python", "Tableau"], target_roles=["Data Analyst"], bio="I love data")
    for k, v in (cand_kw or {}).items():
        setattr(c, k, v)
    co = Company(user_id="co1", name="Acme", industry="Software", headquarters="Chicago, IL",
                 locations=["Chicago, IL"], core_values=["Integrity", "Impact"], mission_statement="We love data")
    j = Job(id="j1", company_id="co1", title="Data Analyst", salary_text="$65,000 - $75,000", location="Chicago, IL",
            work_type="Hybrid", employment_type="Full-time", skills=["SQL", "Python", "Tableau"],
            posted_date=date(2026, 10, 1), time_to_fill_days=30, min_education="BACHELORS")
    for k, v in (job_kw or {}).items():
        setattr(j, k, v)
    return MatchingEngine(Dataset({c.profile_id: c}, {co.user_id: co}, {j.id: j}), as_of=AS_OF), c, j


def test_diagram_weights():
    w = MatchConfig().category_weights
    assert w == {"skills": 0.35, "culture": 0.25, "trajectory": 0.20, "logistics": 0.20}


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        MatchConfig(category_weights={"skills": 0.5, "culture": 0.25, "trajectory": 0.2, "logistics": 0.2})


@pytest.mark.parametrize("field,value", [
    ("open_to_work", False), ("open_to_work", None),
    ("fcra_consent", False), ("fcra_consent", None),
    ("job_search_status", "Not looking"), ("job_search_status", None),
    ("residency", None),
])
def test_step1_gate_blocks_scoring(field, value):
    e, c, j = make({field: value})
    assert e.score_pair(c, j) is None
    assert e.rank_jobs("c1") == []


def test_closed_or_paused_jobs_are_never_ranked():
    for kw in ({"status": "closed"}, {"is_paused": True}):
        e, c, j = make(job_kw=kw)
        assert e.rank_jobs("c1") == []


def test_sponsorship_rule():
    e, c, j = make({"residency": "VISA_HOLDER"})
    assert e.score_pair(c, j) is None
    e, c, j = make({"residency": "VISA_HOLDER"}, {"sponsorship_available": True})
    assert e.score_pair(c, j) is not None


def test_score_is_blend_of_categories():
    e, c, j = make()
    r = e.score_pair(c, j)
    cats = {x.name: x for x in r.categories}
    expected = sum(x.weight * x.score for x in cats.values()) / sum(x.weight for x in cats.values())
    assert r.score == pytest.approx(expected, abs=0.01)
    assert 0 <= r.score <= 100


def test_better_fit_scores_higher():
    good = make()[0].score_pair(*make()[1:]).score
    e, c, j = make({"hard_skills": ["Excel"], "location": "Miami, FL", "willing_to_relocate": False,
                    "target_compensation": 140000})
    assert e.score_pair(c, j).score < good


def test_missing_data_is_reweighted_not_penalized():
    e, c, j = make({"core_values": [], "bio": ""})       # whole culture category missing
    r = e.score_pair(c, j)
    culture = next(x for x in r.categories if x.name == "culture")
    assert culture.score is None and r.coverage < 1


def test_same_inputs_same_score():
    a = make()[0].score_pair(*make()[1:]).score
    b = make()[0].score_pair(*make()[1:]).score
    assert a == b


def test_ranked_list_hides_score():
    from dataclasses import fields
    from matching.models import RankedJob
    e, c, j = make()
    item = e.rank_jobs("c1")[0]
    assert "score" not in {f.name for f in fields(RankedJob)}
    assert not any("%" in h for h in item.highlights)
