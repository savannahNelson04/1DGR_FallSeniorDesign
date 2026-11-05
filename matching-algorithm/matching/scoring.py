"""
The four scored categories from the diagram. Pure functions, no I/O.

Every factor returns a FactorScore with a 0-1 score, or None when data is missing on
either side. Missing factors are left out and the remaining factor weights are
re-normalized, so an incomplete profile still gets a score (SED AD-06). How much of
the total weight actually had data is stored as `coverage` on each result.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from . import normalize as N
from . import vocab
from .config import MatchConfig
from .models import Candidate, CategoryScore, Company, FactorScore, Job


# ------------------------------------------------------------------ precomputed features
@dataclass
class CandidateFeatures:
    skills: set
    values: set
    bio_tokens: list
    metro: Optional[str]
    seniority: Optional[int]
    last_role_level: Optional[int]
    edu_rank: Optional[int]
    edu_in_progress_rank: Optional[int]
    languages: set
    certifications: set
    achievement_count: int
    interests: set
    target_roles: list
    work: list = field(default_factory=list)   # [(title, tokens, years)]
    available_on: Optional[date] = None


@dataclass
class JobFeatures:
    title: str
    skills: set
    skill_tokens: set
    level: int
    metro: Optional[str]
    is_remote: bool
    pay: Optional[tuple]
    deadline: Optional[date]
    min_edu_rank: Optional[int]
    languages: set
    certifications: set
    employment_type: str
    industry: str
    company_values: set
    company_tokens: list
    company_metros: set


def candidate_features(c: Candidate, as_of: date) -> CandidateFeatures:
    ranks = [N.education_rank(e.level) for e in c.education]
    done = [r for r, e in zip(ranks, c.education) if r is not None and (e.graduation_year or 0) <= as_of.year]
    in_prog = [r for r, e in zip(ranks, c.education) if r is not None and (e.graduation_year or 0) > as_of.year]
    highest = N.education_rank(c.highest_education)
    edu_rank = max([r for r in [highest] + done if r is not None], default=None)

    if N.clean(c.employment_type) == "internship":
        seniority = 0
    else:
        seniority = vocab.EXPERIENCE_LEVEL.get((c.experience or "").upper())

    work = []
    for w in c.work_history:
        end = as_of if (w.is_current or w.end is None) else w.end
        work.append((w.title, set(N.tokens(w.title + " " + w.description)), N.years_between(w.start, end)))
    recent = sorted(c.work_history, key=lambda w: (w.is_current, w.start or date.min), reverse=True)

    return CandidateFeatures(
        skills=N.skill_set(c.hard_skills + c.soft_skills),
        values=N.value_set(c.core_values),
        bio_tokens=N.tokens(c.bio),
        metro=N.metro(c.location),
        seniority=seniority,
        last_role_level=N.title_level(recent[0].title) if recent else None,
        edu_rank=edu_rank,
        edu_in_progress_rank=max(in_prog, default=None),
        languages=N.value_set(c.languages),
        certifications=N.value_set(c.certifications),
        achievement_count=len([a for a in c.achievements if N.clean(a)]) + len([a for a in c.awards if N.clean(a)]),
        interests=N.value_set(c.industry_interests),
        target_roles=[t for t in c.target_roles if N.clean(t)],
        work=work,
        available_on=N.parse_availability(c.availability, as_of),
    )


def job_features(j: Job, co: Optional[Company], cfg: MatchConfig) -> JobFeatures:
    level = N.title_level(j.title)
    metro = N.metro(j.location)
    is_remote = N.clean(j.work_type) == "remote" or metro == "remote"
    deadline = j.start_date
    if deadline is None and j.posted_date and j.time_to_fill_days is not None:
        deadline = j.posted_date + timedelta(days=j.time_to_fill_days)
    emp = N.clean(j.employment_type) or ("internship" if level == 0 else "")
    skills = N.skill_set(j.skills)
    return JobFeatures(
        title=j.title,
        skills=skills,
        skill_tokens={t for s in skills for t in N.tokens(s)} | N.role_tokens(j.title),
        level=level,
        metro=metro,
        is_remote=is_remote,
        pay=N.parse_salary(j.salary_text, cfg.hours_per_year),
        deadline=deadline,
        min_edu_rank=N.education_rank(j.min_education),
        languages=N.value_set(j.required_languages),
        certifications=N.value_set(j.required_certifications),
        employment_type=emp,
        industry=N.clean(co.industry) if co else "",
        company_values=N.value_set(co.core_values) if co else set(),
        company_tokens=N.tokens(f"{co.mission_statement} {co.why_us}") if co else [],
        company_metros={m for m in (N.metro(x) for x in ([co.headquarters] + co.locations)) if m} if co else set(),
    )


# ------------------------------------------------------------------ helpers
def _combine(name: str, weight: float, factors: list[FactorScore], factor_weights: dict) -> tuple[CategoryScore, float]:
    """Weighted average of the factors that have data. Returns the category and the share of its weight that had data."""
    present = [(factor_weights[f.name], f.score) for f in factors if f.score is not None]
    wsum = sum(w for w, _ in present)
    score = round(100 * sum(w * s for w, s in present) / wsum, 4) if wsum else None
    return CategoryScore(name=name, weight=weight, score=score, factors=factors), wsum


def _related(a: str, b: str) -> bool:
    for k, vs in vocab.RELATED_INDUSTRIES.items():
        group = {N.clean(k)} | {N.clean(v) for v in vs}
        if a in group and b in group and (a == N.clean(k) or b == N.clean(k)):
            return True
    return False


def _fmt_list(items, n=3) -> str:
    items = sorted(items)
    return ", ".join(items[:n]) + (f" +{len(items) - n} more" if len(items) > n else "")


# ------------------------------------------------------------------ Skills & Qualifications (35%)
def score_skills(cf: CandidateFeatures, jf: JobFeatures, cfg: MatchConfig) -> tuple[CategoryScore, float]:
    f = []
    # Skills <-> required skills
    if jf.skills and cf.skills:
        hit = jf.skills & cf.skills
        f.append(FactorScore("skills", len(hit) / len(jf.skills), f"Matches {len(hit)} of {len(jf.skills)} required skills"))
    else:
        f.append(FactorScore("skills", None, "No skills listed on one side"))

    # Education <-> degree
    if jf.min_edu_rank is None or (cf.edu_rank is None and cf.edu_in_progress_rank is None):
        f.append(FactorScore("education", None, "No degree requirement or no education data"))
    elif (cf.edu_rank or -1) >= jf.min_edu_rank:
        f.append(FactorScore("education", 1.0, "Meets the degree requirement"))
    elif (cf.edu_in_progress_rank or -1) >= jf.min_edu_rank:
        f.append(FactorScore("education", 0.8, "Degree in progress meets the requirement"))
    elif max(cf.edu_rank or -1, cf.edu_in_progress_rank or -1) == jf.min_edu_rank - 1:
        f.append(FactorScore("education", 0.5, "One level below the degree requirement"))
    else:
        f.append(FactorScore("education", 0.0, "Below the degree requirement"))

    # Certifications and languages (only when the job lists requirements)
    for name, req, have, label in (("certifications", jf.certifications, cf.certifications, "certifications"),
                                   ("languages", jf.languages, cf.languages, "required languages")):
        if req and have:
            hit = req & have
            f.append(FactorScore(name, len(hit) / len(req), f"Has {len(hit)} of {len(req)} {label}"))
        else:
            f.append(FactorScore(name, None, f"No {label} listed on one side"))

    # Achievements & awards (candidate-only signal)
    if cf.achievement_count:
        f.append(FactorScore("achievements", min(1.0, cf.achievement_count / 3),
                             f"{cf.achievement_count} achievements or awards"))
    else:
        f.append(FactorScore("achievements", None, "No achievements listed"))

    # Work history: domain relevance + years in relevant roles
    if cf.work:
        best, rel_years = 0.0, 0.0
        for title, toks, yrs in cf.work:
            # relevant if the past title resembles this job's title, or the entry mentions its skills
            rel = max(N.title_similarity(title, jf.title), min(1.0, len(toks & jf.skill_tokens) / 2))
            best = max(best, rel)
            rel_years += yrs * rel
        need = vocab.EXPECTED_YEARS_BY_LEVEL.get(jf.level, 0.5)
        years_score = 1.0 if need == 0 else min(1.0, rel_years / need)
        f.append(FactorScore("work_history", 0.5 * best + 0.5 * years_score,
                             f"{rel_years:.1f} years of relevant experience"))
    else:
        f.append(FactorScore("work_history", None, "No work history listed"))

    return _combine("skills", cfg.category_weights["skills"], f, cfg.skills_factors)


# ------------------------------------------------------------------ Values & Culture (25%)
def score_culture(cf: CandidateFeatures, jf: JobFeatures, cfg: MatchConfig) -> tuple[CategoryScore, float]:
    f = []
    if cf.values and jf.company_values:
        shared = cf.values & jf.company_values
        f.append(FactorScore("core_values", N.overlap(cf.values, jf.company_values),
                             f"Shares values: {_fmt_list(shared)}" if shared else "No shared core values"))
    else:
        f.append(FactorScore("core_values", None, "No core values listed on one side"))

    if cf.bio_tokens and jf.company_tokens:
        sim = N.cosine(cf.bio_tokens, jf.company_tokens)
        f.append(FactorScore("bio_mission", min(1.0, sim / cfg.text_full_credit), "Bio compared with mission and why-us text"))
    else:
        f.append(FactorScore("bio_mission", None, "No bio or no mission text"))

    return _combine("culture", cfg.category_weights["culture"], f, cfg.culture_factors)


# ------------------------------------------------------------------ Career Trajectory (20%)
def score_trajectory(cf: CandidateFeatures, jf: JobFeatures, cfg: MatchConfig) -> tuple[CategoryScore, float]:
    f = []
    if cf.interests and jf.industry:
        if jf.industry in cf.interests:
            f.append(FactorScore("industry", 1.0, "Interested in this industry"))
        elif any(_related(i, jf.industry) for i in cf.interests):
            f.append(FactorScore("industry", 0.5, "Interested in a related industry"))
        else:
            f.append(FactorScore("industry", 0.0, "Industry is not among interests"))
    else:
        f.append(FactorScore("industry", None, "No industry interests or no company industry"))

    if cf.target_roles:
        best = max(cf.target_roles, key=lambda t: (N.title_similarity(t, jf.title), t))
        sim = N.title_similarity(best, jf.title)
        f.append(FactorScore("target_role", sim, f"Target role '{best}'" + (" matches this role" if sim >= 0.75 else "")))
    else:
        f.append(FactorScore("target_role", None, "No target roles listed"))

    if cf.seniority is not None:
        gap = abs(jf.level - cf.seniority)
        f.append(FactorScore("seniority", {0: 1.0, 1: 0.6, 2: 0.2}.get(gap, 0.0),
                             "Seniority fits" if gap == 0 else f"Seniority differs by {gap} level(s)"))
    else:
        f.append(FactorScore("seniority", None, "No experience level"))

    if cf.last_role_level is not None:
        step = jf.level - cf.last_role_level
        s = {0: 1.0, 1: 1.0, 2: 0.5, -1: 0.6}.get(step, 0.3 if step < -1 else 0.2)
        f.append(FactorScore("role_level", s, "Natural next step" if step in (0, 1) else f"Role is {step:+d} level(s) from last role"))
    else:
        f.append(FactorScore("role_level", None, "No work history"))

    return _combine("trajectory", cfg.category_weights["trajectory"], f, cfg.trajectory_factors)


# ------------------------------------------------------------------ Logistics (20%)
_ARRANGEMENT = {("remote", "remote"): 1.0, ("hybrid", "hybrid"): 1.0, ("on-site", "on-site"): 1.0,
                ("hybrid", "remote"): 0.5, ("remote", "hybrid"): 0.5, ("hybrid", "on-site"): 0.5,
                ("on-site", "hybrid"): 0.5, ("remote", "on-site"): 0.0, ("on-site", "remote"): 0.0}


def score_logistics(c: Candidate, cf: CandidateFeatures, j: Job, jf: JobFeatures, as_of: date,
                    cfg: MatchConfig) -> tuple[CategoryScore, float]:
    f = []
    # Work type: arrangement and employment type
    parts = []
    a = _ARRANGEMENT.get((N.clean(c.work_type), N.clean(j.work_type)))
    if a is not None:
        parts.append(a)
    if N.clean(c.employment_type) and jf.employment_type:
        parts.append(1.0 if N.clean(c.employment_type) == jf.employment_type else 0.0)
    f.append(FactorScore("work_type", sum(parts) / len(parts) if parts else None,
                         f"Wants {c.work_type or '?'} {c.employment_type or ''}; job is {j.work_type or '?'} {jf.employment_type or ''}".strip()))

    # Location / willing to relocate
    if jf.is_remote:
        f.append(FactorScore("location", 1.0, "Remote role"))
    elif not cf.metro or not jf.metro:
        f.append(FactorScore("location", None, "Location missing on one side"))
    elif cf.metro == jf.metro:
        f.append(FactorScore("location", 1.0, "Same city"))
    elif c.willing_to_relocate is True:
        s = 0.75 if j.is_relocation_covered else 0.4
        f.append(FactorScore("location", s, "Willing to relocate" + (" (relocation covered)" if j.is_relocation_covered else "")))
    elif c.willing_to_relocate is False:
        f.append(FactorScore("location", 0.0, "Different city, not willing to relocate"))
    else:
        f.append(FactorScore("location", 0.5, "Different city, relocation preference unknown"))

    # Headquarters (only matters for non-remote roles)
    if jf.is_remote or not cf.metro or not jf.company_metros:
        f.append(FactorScore("headquarters", None, "Not applicable"))
    else:
        near = cf.metro in jf.company_metros
        f.append(FactorScore("headquarters", 1.0 if near else 0.0, "Near a company office" if near else "Not near a company office"))

    # Pay range <-> comp range
    if jf.pay and c.target_compensation:
        lo, hi = jf.pay
        t = float(c.target_compensation)
        if t <= hi:
            f.append(FactorScore("pay", 1.0, "Pay target within range"))
        else:
            gap = (t - hi) / hi
            f.append(FactorScore("pay", max(0.0, 1 - gap / cfg.pay_over_max_tolerance), f"Pay target {gap:.0%} above range"))
    else:
        f.append(FactorScore("pay", None, "Pay range or pay target not stated"))

    # Availability <-> time to fill (or start date when the posting has one)
    if cf.available_on and jf.deadline:
        deadline = max(jf.deadline, as_of)
        late = (cf.available_on - deadline).days
        g = cfg.availability_grace_days
        s = 1.0 if late <= 0 else 0.5 if late <= g else 0.25 if late <= 2 * g else 0.0
        f.append(FactorScore("availability", s, "Available in time" if late <= 0 else f"Available {late} days after needed"))
    else:
        f.append(FactorScore("availability", None, "Availability or fill date unknown"))

    return _combine("logistics", cfg.category_weights["logistics"], f, cfg.logistics_factors)
