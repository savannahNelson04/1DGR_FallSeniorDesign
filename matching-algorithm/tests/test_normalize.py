from datetime import date

from matching import normalize as N


def test_salary_formats():
    assert N.parse_salary("$65,000 - $75,000 per year") == (65000, 75000)
    assert N.parse_salary("$82K-$120K") == (82000, 120000)
    assert N.parse_salary("$57,000–$85,000/yr") == (57000, 85000)
    assert N.parse_salary("$90K-$105K + equity") == (90000, 105000)
    assert N.parse_salary("$24/hr") == (24 * 2080, 24 * 2080)
    assert N.parse_salary("$30 per hour") == (30 * 2080, 30 * 2080)
    for unknown in ("Competitive", "DOE", "Salary commensurate with experience", "", None):
        assert N.parse_salary(unknown) is None


def test_availability():
    today = date(2026, 10, 22)
    assert N.parse_availability("Immediately", today) == today
    assert N.parse_availability("Within 2 weeks", today) == date(2026, 11, 5)
    assert N.parse_availability("Summer 2027", today) == date(2027, 6, 1)
    assert N.parse_availability("January 2027", today) == date(2027, 1, 1)
    assert N.parse_availability("", today) is None


def test_title_level():
    assert N.title_level("Software Engineer Intern") == 0
    assert N.title_level("Junior Data Analyst") == 1
    assert N.title_level("Data Analyst") == 1          # plain title = entry level
    assert N.title_level("Assistant Project Manager") == 1
    assert N.title_level("Senior Software Engineer") == 3
    assert N.title_level("Engineering Manager") == 4


def test_title_similarity_ignores_seniority_words():
    assert N.title_similarity("Junior Software Engineer", "Software Engineer") == 1.0
    assert N.title_similarity("Data Analyst", "Marketing Coordinator") == 0.0


def test_metro_and_skills():
    assert N.metro("Chicago, IL") == "chicago, il"
    assert N.metro("Remote (US)") == "remote"
    assert N.skill_set(["JS", "Postgres", "React.js"]) == {"javascript", "postgresql", "react"}
