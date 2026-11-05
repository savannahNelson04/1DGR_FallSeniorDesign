"""
Matching engine: Step 1 gate -> four category scores -> weighted match score -> ranked list.

    Match Score = 0.35 Skills + 0.25 Culture + 0.20 Trajectory + 0.20 Logistics

The score is used to rank only and is never included in what users see
(RankedJob / RankedCandidate). It is kept on MatchResult so it can be stored.
"""
from __future__ import annotations
from datetime import date, datetime, timezone
from typing import Optional

from . import gate
from .config import MatchConfig
from .models import (Candidate, Dataset, GateResult, Job, MatchResult, RankedCandidate, RankedJob)
from .scoring import (candidate_features, job_features, score_culture, score_logistics,
                      score_skills, score_trajectory)


class MatchingEngine:
    def __init__(self, data: Dataset, config: Optional[MatchConfig] = None, as_of: Optional[date] = None):
        self.data = data
        self.cfg = config or MatchConfig()
        self.as_of = as_of or date.today()
        self._cf, self._jf = {}, {}
        self._candidate_gate = {cid: gate.check_candidate(c, self.cfg) for cid, c in data.candidates.items()}
        self._job_gate = {jid: gate.check_job(j) for jid, j in data.jobs.items()}
        self.results: dict[tuple[str, str], MatchResult] = {}

    # ---------------------------------------------------------------- features (cached)
    def _cand_feat(self, c: Candidate):
        if c.profile_id not in self._cf:
            self._cf[c.profile_id] = candidate_features(c, self.as_of)
        return self._cf[c.profile_id]

    def _job_feat(self, j: Job):
        if j.id not in self._jf:
            self._jf[j.id] = job_features(j, self.data.companies.get(j.company_id), self.cfg)
        return self._jf[j.id]

    # ---------------------------------------------------------------- gate
    def candidate_gate(self, candidate_id: str) -> GateResult:
        return self._candidate_gate[candidate_id]

    def eligible(self, c: Candidate, j: Job) -> GateResult:
        reasons = (self._candidate_gate[c.profile_id].reasons + self._job_gate[j.id].reasons
                   + gate.check_pair(c, j, self.cfg).reasons)
        return GateResult(passed=not reasons, reasons=reasons)

    # ---------------------------------------------------------------- scoring
    def score_pair(self, c: Candidate, j: Job) -> Optional[MatchResult]:
        """Score one candidate-job pair. Returns None when the pair does not pass Step 1."""
        if not self.eligible(c, j).passed:
            return None
        cf, jf = self._cand_feat(c), self._job_feat(j)
        parts = [score_skills(cf, jf, self.cfg),
                 score_culture(cf, jf, self.cfg),
                 score_trajectory(cf, jf, self.cfg),
                 score_logistics(c, cf, j, jf, self.as_of, self.cfg)]
        cats = [cat for cat, _ in parts]
        present = [(cat.weight, cat.score) for cat in cats if cat.score is not None]
        wsum = sum(w for w, _ in present)
        score = round(sum(w * s for w, s in present) / wsum, 2) if wsum else 0.0
        coverage = round(sum(cat.weight * share for cat, share in parts), 4)
        result = MatchResult(candidate_id=c.profile_id, job_id=j.id, score=score, coverage=coverage,
                             categories=cats, config_version=self.cfg.version,
                             computed_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        self.results[(c.profile_id, j.id)] = result
        return result

    def score_all(self) -> list[MatchResult]:
        """Score every eligible pair (e.g., for a batch run whose results are stored)."""
        out = []
        for c in self.data.candidates.values():
            if not self._candidate_gate[c.profile_id].passed:
                continue
            for j in self.data.jobs.values():
                r = self.score_pair(c, j)
                if r:
                    out.append(r)
        return out

    # ---------------------------------------------------------------- ranking
    def _job_sort_key(self, r: MatchResult):
        j = self.data.jobs[r.job_id]
        # Highest score first; ties: newest posting first, then job ID, so order is always repeatable.
        return (-r.score, -(j.posted_date.toordinal() if j.posted_date else 0), j.id)

    def ranked_results_for_candidate(self, candidate_id: str) -> list[MatchResult]:
        c = self.data.candidates[candidate_id]
        if not self._candidate_gate[candidate_id].passed:
            return []
        results = [r for r in (self.score_pair(c, j) for j in self.data.jobs.values()) if r]
        return sorted(results, key=self._job_sort_key)

    def rank_jobs(self, candidate_id: str, top_n: Optional[int] = None) -> list[RankedJob]:
        """The list a candidate sees: ranked jobs, no scores."""
        out = []
        for i, r in enumerate(self.ranked_results_for_candidate(candidate_id)[:top_n], 1):
            j = self.data.jobs[r.job_id]
            co = self.data.companies.get(j.company_id)
            out.append(RankedJob(rank=i, job_id=j.id, title=j.title, company_name=co.name if co else "",
                                 location=j.location, highlights=highlights(r, self.cfg)))
        return out

    def rank_candidates(self, job_id: str, top_n: Optional[int] = None) -> list[RankedCandidate]:
        """The list a company sees for one job: ranked eligible candidates, no scores."""
        j = self.data.jobs[job_id]
        results = [r for r in (self.score_pair(c, j) for c in self.data.candidates.values()) if r]
        results.sort(key=lambda r: (-r.score, r.candidate_id))
        return [RankedCandidate(rank=i, candidate_id=r.candidate_id,
                                display_name=self.data.candidates[r.candidate_id].display_name,
                                highlights=highlights(r, self.cfg))
                for i, r in enumerate(results[:top_n], 1)]


def highlights(r: MatchResult, cfg: MatchConfig, n: int = 3) -> list[str]:
    """Plain-language reasons for a match (no numbers), from the strongest weighted factors."""
    picks = []
    for cat in r.categories:
        fw = getattr(cfg, f"{cat.name}_factors")
        for f in cat.factors:
            if f.score is not None and f.score >= 0.75:
                picks.append((cat.weight * fw[f.name] * f.score, f.detail))
    picks.sort(key=lambda p: (-p[0], p[1]))
    return [d for _, d in picks[:n]]
