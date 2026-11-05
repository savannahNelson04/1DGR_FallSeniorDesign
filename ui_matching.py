"""
Bridge between the matching algorithm (matching-algorithm/matching) and the UI (ui_main.py).

Loads the dataset once, runs the MatchingEngine, and turns its output into the
row tuples the UI tables expect. Match scores are used for ranking only and are
never returned in any row, so they never reach the screen.

    from ui_matching import MatchingBackend
    backend = MatchingBackend()          # loads matching-algorithm/data/sample
    backend.job_matches_for_candidate("Riley Chen (0136efea)")
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Optional, Union

ROOT = Path(__file__).resolve().parent
ALGO_DIR = ROOT / "matching-algorithm"
if str(ALGO_DIR) not in sys.path:
    sys.path.insert(0, str(ALGO_DIR))

from matching import MatchingEngine, load_dataset  # noqa: E402
from matching.normalize import title_level        # noqa: E402

# The algorithm's copy of the sample data includes the gate fields it needs
# (FCRA consent, job search status, ...), which the top-level sample/ folder lacks.
DATA_DIR = ALGO_DIR / "data" / "sample"

# The sample data was generated for this date (availability / fill dates are
# compared against it). Set to None to score as of today once real data is used.
AS_OF: Optional[date] = date(2026, 10, 22)

TOP_N = 5

SENIORITY_LABELS = {0: "Intern", 1: "Entry", 2: "Mid", 3: "Senior", 4: "Lead / Manager"}

# A result is either a list of row tuples or a message explaining why there are none.
Rows = Union[list, str]


def _join(items) -> str:
    return ", ".join(str(x) for x in items if x)


def _pretty_enum(v: Optional[str]) -> str:
    return (v or "").replace("_", " ").title()


def _yes_no(v: Optional[bool]) -> str:
    return "" if v is None else ("Yes" if v else "No")


def _unique_labels(pairs):
    """pairs = [(id, label)] -> {label: id}; repeated labels get a short id suffix."""
    counts = {}
    for _, label in pairs:
        counts[label] = counts.get(label, 0) + 1
    out = {}
    for _id, label in pairs:
        key = label if counts[label] == 1 else f"{label} ({_id[:8]})"
        out[key] = _id
    return dict(sorted(out.items(), key=lambda kv: kv[0].lower()))


class MatchingBackend:
    def __init__(self, data_dir: Union[str, Path] = DATA_DIR, as_of: Optional[date] = AS_OF,
                 top_n: int = TOP_N):
        self.data = load_dataset(data_dir)
        self.engine = MatchingEngine(self.data, as_of=as_of)
        self.top_n = top_n

        d = self.data
        self.candidate_options = _unique_labels(
            [(cid, c.display_name or cid[:8]) for cid, c in d.candidates.items()])

        def _job_label(j):
            co = d.companies.get(j.company_id)
            return f"{j.title} — {co.name}" if co else j.title
        # Only open, unpaused postings can be matched, so only those are offered.
        self.job_options = _unique_labels(
            [(jid, _job_label(j)) for jid, j in d.jobs.items() if self.engine._job_gate[jid].passed])
        self.company_options = _unique_labels(
            [(uid, co.name or uid[:8]) for uid, co in d.companies.items()])

    # ------------------------------------------------------------ profile completion
    @staticmethod
    def profile_completion(c) -> int:
        """Percent of profile fields filled in (the fields shown in Candidate Info, plus bio,
        values, and work history)."""
        filled = [
            bool(c.target_roles), bool(c.industry_interests), bool(c.location),
            c.open_to_work is not None, bool(c.hard_skills or c.soft_skills),
            bool(c.education or c.highest_education), bool(c.certifications), bool(c.languages),
            c.willing_to_relocate is not None, c.target_compensation is not None,
            bool(c.availability), bool(c.bio), bool(c.core_values), bool(c.work_history),
        ]
        return round(100 * sum(filled) / len(filled))

    def _candidate_row(self, rank, cid):
        c = self.data.candidates[cid]
        role = c.target_roles[0] if c.target_roles else ""
        return (rank, c.display_name, role, self.profile_completion(c))

    def _rank_by_completion(self, scores: dict) -> list:
        """scores = {candidate_id: best match score}. Company side ranks by profile
        completion; the match score only breaks ties (and is not returned)."""
        order = sorted(scores, key=lambda cid: (-self.profile_completion(self.data.candidates[cid]),
                                                -scores[cid], cid))
        return [self._candidate_row(i, cid) for i, cid in enumerate(order[:self.top_n], 1)]

    def _gate_message(self, cid) -> Optional[str]:
        g = self.engine.candidate_gate(cid)
        if g.passed:
            return None
        return "Not ranked — this candidate doesn't pass the Step 1 must-pass check: " + "; ".join(g.reasons) + "."

    # ------------------------------------------------------------ Job <-> Candidate
    def job_matches_for_candidate(self, label: str) -> Rows:
        """(rank, job_title, company, location) for the selected candidate."""
        cid = self.candidate_options[label]
        msg = self._gate_message(cid)
        if msg:
            return msg
        rows = [(r.rank, r.title, r.company_name, r.location)
                for r in self.engine.rank_jobs(cid, top_n=self.top_n)]
        return rows or "No eligible job postings for this candidate."

    def candidates_for_job(self, label: str) -> Rows:
        """(rank, candidate_name, target_role, completion_pct) for the selected job."""
        jid = self.job_options[label]
        j = self.data.jobs[jid]
        scores = {}
        for c in self.data.candidates.values():
            r = self.engine.score_pair(c, j)
            if r:
                scores[c.profile_id] = r.score
        return self._rank_by_completion(scores) or "No eligible candidates for this job posting."

    # ------------------------------------------------------------ Candidate <-> Company
    def company_matches_for_candidate(self, label: str) -> Rows:
        """(rank, company, industry, best_matching_role): each company is placed by its
        best-matching open role."""
        cid = self.candidate_options[label]
        msg = self._gate_message(cid)
        if msg:
            return msg
        rows, seen = [], set()
        for r in self.engine.ranked_results_for_candidate(cid):   # already best-first
            j = self.data.jobs[r.job_id]
            if j.company_id in seen:
                continue
            seen.add(j.company_id)
            co = self.data.companies.get(j.company_id)
            rows.append((len(rows) + 1, co.name if co else "", co.industry if co else "", j.title))
            if len(rows) == self.top_n:
                break
        return rows or "No eligible companies for this candidate."

    def candidates_for_company(self, label: str) -> Rows:
        """(rank, candidate_name, target_role, completion_pct): candidates eligible for at
        least one of the company's open roles."""
        uid = self.company_options[label]
        jobs = [j for j in self.data.jobs.values()
                if j.company_id == uid and self.engine._job_gate[j.id].passed]
        if not jobs:
            return "This company has no open job postings to match against."
        scores = {}
        for c in self.data.candidates.values():
            for j in jobs:
                r = self.engine.score_pair(c, j)
                if r and r.score > scores.get(c.profile_id, -1):
                    scores[c.profile_id] = r.score
        return self._rank_by_completion(scores) or "No eligible candidates for this company."

    # ------------------------------------------------------------ info windows
    def candidate_info_rows(self) -> list:
        rows = []
        for label, cid in self.candidate_options.items():
            c = self.data.candidates[cid]
            edu = c.education[0] if c.education else None
            education = _pretty_enum(edu.level if edu and edu.level else c.highest_education)
            if edu and edu.field_of_study:
                education = f"{education} — {edu.field_of_study}" if education else edu.field_of_study
            rows.append((
                label, _join(c.target_roles), _join(c.industry_interests), c.location,
                _yes_no(c.open_to_work), _join(c.hard_skills + c.soft_skills), education,
                _join(c.certifications), _join(c.languages), _yes_no(c.willing_to_relocate),
                f"${c.target_compensation:,.0f}" if c.target_compensation is not None else "",
                c.availability,
            ))
        return rows

    def job_info_rows(self) -> list:
        rows = []
        for j in sorted(self.data.jobs.values(), key=lambda j: (
                (self.data.companies[j.company_id].name if j.company_id in self.data.companies else ""),
                j.title)):
            co = self.data.companies.get(j.company_id)
            rows.append((
                co.name if co else "", co.industry if co else "", j.title, _join(j.skills),
                _pretty_enum(j.min_education), j.location, j.work_type, j.salary_text,
                SENIORITY_LABELS.get(title_level(j.title), ""),
                f"{j.time_to_fill_days} days" if j.time_to_fill_days is not None else "",
            ))
        return rows
