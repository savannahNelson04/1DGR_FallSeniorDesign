"""
Load data in the 1DGR schema shape (the files in data/sample) into the engine's models.

This is the only module that knows field names. When real 1DGR data arrives through
an export or API, replace or extend this module; the scoring code does not change.

Fields that are not in the 1DGR ERD are read from `proposed_*` columns first, then
from the plain name, so either works.
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Any, Optional

from .models import Candidate, Company, Dataset, EducationEntry, Job, WorkEntry
from .normalize import parse_date, parse_days

TABLES = ["users", "student_profiles", "student_higher_education", "company_profiles", "job_postings", "expected_matches"]


# ------------------------------------------------------------------ reading files
def _decode(v: Any) -> Any:
    """CSV cells arrive as strings: decode JSON lists/objects, booleans, numbers, blanks."""
    if not isinstance(v, str):
        return v
    s = v.strip()
    if s == "":
        return None
    if s[0] in "[{":
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return s
    if s in ("true", "false"):
        return s == "true"
    return s


def _read_table(folder: Path, name: str) -> list[dict]:
    for sub in ("json", "", "csv"):
        base = folder / sub if sub else folder
        jp, cp = base / f"{name}.json", base / f"{name}.csv"
        if jp.exists():
            return json.loads(jp.read_text(encoding="utf-8"))
        if cp.exists():
            with open(cp, newline="", encoding="utf-8") as fh:
                return [{k: _decode(v) for k, v in row.items()} for row in csv.DictReader(fh)]
    return []


def _first(row: dict, *names, default=None):
    for n in names:
        if n in row and row[n] not in (None, ""):
            return row[n]
    return default


def _list(v) -> list:
    if v is None or v == "":
        return []
    if isinstance(v, str):
        v = _decode(v)
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
    return list(v) if isinstance(v, (list, tuple)) else [v]


def _bool(v) -> Optional[bool]:
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "y")


def _num(v) -> Optional[float]:
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _names(items) -> list[str]:
    """Lists may hold strings or {'name': ...} objects (awards, certifications)."""
    out = []
    for x in _list(items):
        out.append(x.get("name", "") if isinstance(x, dict) else str(x))
    return [x for x in out if x]


# ------------------------------------------------------------------ mapping
def _candidate(row: dict, edu: list[EducationEntry]) -> Candidate:
    first = _first(row, "preferred_name", "legal_first_name", default="")
    work = []
    for w in _list(row.get("work_history")):
        if not isinstance(w, dict):
            continue
        end_raw = str(w.get("end") or "").strip().lower()
        work.append(WorkEntry(title=w.get("title", ""), description=w.get("description", ""),
                              start=parse_date(w.get("start")), end=parse_date(w.get("end")),
                              is_current=end_raw in ("present", "current", "")))
    return Candidate(
        profile_id=row["profile_id"], user_id=row["user_id"],
        display_name=f"{first} {row.get('legal_last_name') or ''}".strip(),
        open_to_work=_bool(row.get("open_to_work_status")),
        job_search_status=_first(row, "proposed_job_search_status", "job_search_status"),
        fcra_consent=_bool(_first(row, "proposed_fcra_consent", "fcra_consent")),
        residency=_first(row, "residency"),
        bio=row.get("bio") or "",
        location=row.get("location") or "",
        willing_to_relocate=_bool(_first(row, "proposed_willing_to_relocate", "willing_to_relocate")),
        work_type=row.get("work_type") or "",
        employment_type=row.get("work_preference") or "",
        target_compensation=_num(row.get("target_compensation")),
        availability=row.get("availability_period") or "",
        experience=row.get("experience") or "",
        highest_education=row.get("highest_education") or "",
        education=edu,
        industry_interests=_list(row.get("industry_interests")),
        core_values=_list(row.get("core_values")),
        hard_skills=_list(row.get("hard_skills")),
        soft_skills=_list(row.get("soft_skills")),
        languages=_list(row.get("languages")),
        certifications=_names(_first(row, "proposed_certifications", "certifications")),
        achievements=_names(row.get("achievements")),
        awards=_names(row.get("awards")),
        target_roles=_list(row.get("target_roles")),
        work_history=work,
    )


def _company(row: dict) -> Company:
    locs = []
    for l in _list(row.get("locations")):
        if isinstance(l, dict):
            locs.append(", ".join(x for x in (l.get("city"), l.get("state")) if x))
        elif l:
            locs.append(str(l))
    return Company(user_id=row["user_id"], name=row.get("company_name") or "", industry=row.get("industry") or "",
                   headquarters=row.get("headquarters") or "", locations=locs,
                   core_values=_list(row.get("core_values")),
                   mission_statement=row.get("mission_statement") or "", why_us=row.get("why_us") or "")


def _job(row: dict) -> Job:
    req = row.get("application_requirements") or {}
    if isinstance(req, str):
        req = _decode(req) or {}
    return Job(
        id=row["id"], company_id=row["company_id"], title=row.get("title") or "",
        description=row.get("description") or "", salary_text=str(row.get("salary") or ""),
        location=row.get("location") or "", work_type=row.get("work_type") or "",
        employment_type=_first(row, "proposed_employment_type", "employment_type", default=""),
        is_relocation_covered=_bool(row.get("is_relocation_covered")),
        skills=_list(row.get("skills")),
        status=row.get("status") or "open", is_paused=bool(_bool(row.get("is_paused"))),
        posted_date=parse_date(row.get("posted_date")),
        time_to_fill_days=parse_days(row.get("time_to_fill")),
        start_date=parse_date(_first(row, "proposed_start_date", "start_date")),
        min_education=req.get("min_education"),
        required_languages=_list(req.get("required_languages") or req.get("languages_required")),
        required_certifications=_names(req.get("required_certifications") or req.get("certifications_required")),
        requires_us_work_authorization=_bool(req.get("us_work_authorization_required")) is not False,
        sponsorship_available=bool(_bool(req.get("sponsorship_available"))),
    )


def load_dataset(path: str | Path) -> Dataset:
    """`path` is a folder containing json/ and/or csv/ subfolders (like data/sample), or the files directly."""
    folder = Path(path)
    t = {name: _read_table(folder, name) for name in TABLES}
    if not t["student_profiles"] or not t["job_postings"]:
        raise FileNotFoundError(f"No student_profiles or job_postings found under {folder}")
    edu_by_user: dict[str, list[EducationEntry]] = {}
    for e in t["student_higher_education"]:
        edu_by_user.setdefault(e["user_id"], []).append(EducationEntry(
            level=e.get("education_level"), field_of_study=e.get("field_of_study") or "",
            graduation_year=int(e["graduation_year"]) if e.get("graduation_year") else None,
            institution=e.get("university_label") or ""))
    candidates = {r["profile_id"]: _candidate(r, edu_by_user.get(r["user_id"], [])) for r in t["student_profiles"]}
    companies = {r["user_id"]: _company(r) for r in t["company_profiles"]}
    jobs = {r["id"]: _job(r) for r in t["job_postings"]}
    return Dataset(candidates=candidates, companies=companies, jobs=jobs, expected=t["expected_matches"])
