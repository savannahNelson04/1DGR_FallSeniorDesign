"""
Matching configuration.

Category weights come straight from the Candidate <-> Job Match Score diagram:
    Match Score = 0.35 Skills + 0.25 Culture + 0.20 Trajectory + 0.20 Logistics

The diagram does not say how much each item *inside* a category counts, so the
factor weights below are starting values for the team to tune with the sponsor.
Each set of factor weights must add up to 1.0.
"""
from dataclasses import dataclass, field

CATEGORY_WEIGHTS = {
    "skills": 0.35,      # Skills & Qualifications
    "culture": 0.25,     # Values & Culture
    "trajectory": 0.20,  # Career Trajectory
    "logistics": 0.20,   # Logistics
}

SKILLS_FACTORS = {
    "skills": 0.50,          # Skills <-> required skills
    "education": 0.15,       # Education <-> degree
    "certifications": 0.05,  # Certifications
    "languages": 0.05,       # Languages
    "achievements": 0.05,    # Achievements & awards
    "work_history": 0.20,    # Work history (domain + years in role)
}
CULTURE_FACTORS = {
    "core_values": 0.60,     # Core values <-> company core values
    "bio_mission": 0.40,     # Bio <-> mission / why us
}
TRAJECTORY_FACTORS = {
    "industry": 0.35,        # Industry interests <-> industry
    "target_role": 0.35,     # Target roles <-> open role
    "seniority": 0.15,       # Seniority level
    "role_level": 0.15,      # Work history (role level)
}
LOGISTICS_FACTORS = {
    "work_type": 0.25,       # Work type (arrangement + employment type)
    "location": 0.30,        # Location / willing to relocate
    "headquarters": 0.05,    # Headquarters
    "pay": 0.25,             # Pay range <-> comp range
    "availability": 0.15,    # Availability <-> time to fill
}


@dataclass
class MatchConfig:
    version: str = "diagram-v1"
    category_weights: dict = field(default_factory=lambda: dict(CATEGORY_WEIGHTS))
    skills_factors: dict = field(default_factory=lambda: dict(SKILLS_FACTORS))
    culture_factors: dict = field(default_factory=lambda: dict(CULTURE_FACTORS))
    trajectory_factors: dict = field(default_factory=lambda: dict(TRAJECTORY_FACTORS))
    logistics_factors: dict = field(default_factory=lambda: dict(LOGISTICS_FACTORS))

    # ---- Step 1: must pass ----------------------------------------------------
    # Job search statuses that count as "searching". Anything else fails the gate.
    searching_statuses: frozenset = frozenset({"actively looking", "open to offers"})
    # Residency values treated as authorized to work in the US without sponsorship.
    authorized_residency: frozenset = frozenset({"CITIZEN", "PERMANENT_RESIDENT"})
    # If True, VISA_HOLDER / OTHER candidates only pass for jobs that offer sponsorship
    # or do not require US work authorization.
    sponsorship_required_for_others: bool = True

    # ---- Scoring parameters ---------------------------------------------------
    hours_per_year: int = 2080            # converts hourly pay to annual
    pay_over_max_tolerance: float = 0.30  # pay score falls to 0 when the target is 30% above the job's max
    text_full_credit: float = 0.50        # bio/mission text similarity that earns full credit
    availability_grace_days: int = 30     # available within this many days after the deadline -> half credit

    def __post_init__(self):
        for name in ("category_weights", "skills_factors", "culture_factors",
                     "trajectory_factors", "logistics_factors"):
            weights = getattr(self, name)
            if any(w < 0 for w in weights.values()):
                raise ValueError(f"{name}: weights must be non-negative")
            if abs(sum(weights.values()) - 1.0) > 1e-6:
                raise ValueError(f"{name}: weights must add up to 1.0 (got {sum(weights.values()):.3f})")
