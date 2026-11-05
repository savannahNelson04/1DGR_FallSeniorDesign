"""Data models. Field names follow the 1DGR schema where one exists."""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional


# ------------------------------------------------------------------ inputs
@dataclass
class WorkEntry:
    title: str
    description: str = ""
    start: Optional[date] = None
    end: Optional[date] = None          # None with is_current=True means "present"
    is_current: bool = False


@dataclass
class EducationEntry:
    level: Optional[str]                # education_level enum
    field_of_study: str = ""
    graduation_year: Optional[int] = None
    institution: str = ""


@dataclass
class Candidate:
    profile_id: str
    user_id: str
    display_name: str = ""              # for output only; never used in scoring
    # Step 1 gate fields
    open_to_work: Optional[bool] = None
    job_search_status: Optional[str] = None
    fcra_consent: Optional[bool] = None
    residency: Optional[str] = None     # used for work authorization only, never scored
    # Scored fields
    bio: str = ""
    location: str = ""
    willing_to_relocate: Optional[bool] = None
    work_type: str = ""                 # arrangement: Remote / Hybrid / On-site
    employment_type: str = ""           # work_preference: Full-time / Internship / ...
    target_compensation: Optional[float] = None   # annual USD
    availability: str = ""
    experience: str = ""                # industry_exp enum
    highest_education: str = ""
    education: list[EducationEntry] = field(default_factory=list)
    industry_interests: list[str] = field(default_factory=list)
    core_values: list[str] = field(default_factory=list)
    hard_skills: list[str] = field(default_factory=list)
    soft_skills: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    awards: list[str] = field(default_factory=list)
    target_roles: list[str] = field(default_factory=list)
    work_history: list[WorkEntry] = field(default_factory=list)


@dataclass
class Company:
    user_id: str
    name: str
    industry: str = ""
    headquarters: str = ""
    locations: list[str] = field(default_factory=list)   # "City, ST" strings, HQ included
    core_values: list[str] = field(default_factory=list)
    mission_statement: str = ""
    why_us: str = ""


@dataclass
class Job:
    id: str
    company_id: str
    title: str
    description: str = ""
    salary_text: str = ""
    location: str = ""
    work_type: str = ""                 # arrangement
    employment_type: str = ""           # Full-time / Internship / ...
    is_relocation_covered: Optional[bool] = None
    skills: list[str] = field(default_factory=list)
    status: str = "open"
    is_paused: bool = False
    posted_date: Optional[date] = None
    time_to_fill_days: Optional[int] = None
    start_date: Optional[date] = None
    min_education: Optional[str] = None
    required_languages: list[str] = field(default_factory=list)
    required_certifications: list[str] = field(default_factory=list)
    requires_us_work_authorization: bool = True
    sponsorship_available: bool = False


@dataclass
class Dataset:
    candidates: dict[str, Candidate]
    companies: dict[str, Company]
    jobs: dict[str, Job]
    expected: list[dict] = field(default_factory=list)


# ------------------------------------------------------------------ results
@dataclass
class GateResult:
    passed: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class FactorScore:
    name: str
    score: Optional[float]              # 0-1, or None when data is missing on either side
    detail: str = ""


@dataclass
class CategoryScore:
    name: str
    weight: float
    score: Optional[float]              # 0-100, or None when every factor is missing
    factors: list[FactorScore] = field(default_factory=list)


@dataclass
class MatchResult:
    """Stored result. The score is internal: used for ranking, never shown to users."""
    candidate_id: str
    job_id: str
    score: float                        # 0-100
    coverage: float                     # share of total weight that had data on both sides (0-1)
    categories: list[CategoryScore]
    config_version: str
    computed_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RankedJob:
    """What a candidate sees: the ranked list, without the score."""
    rank: int
    job_id: str
    title: str
    company_name: str
    location: str
    highlights: list[str] = field(default_factory=list)


@dataclass
class RankedCandidate:
    """What a company sees for one of its jobs: the ranked list, without the score."""
    rank: int
    candidate_id: str
    display_name: str
    highlights: list[str] = field(default_factory=list)
