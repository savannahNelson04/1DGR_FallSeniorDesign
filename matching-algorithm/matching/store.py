"""Store match results. Scores are kept here for ranking, audit, and tuning; they are not shown to users."""
from __future__ import annotations
import csv
import json
from pathlib import Path

from .models import MatchResult


def write_results(results: list[MatchResult], path: str | Path) -> Path:
    """Write results as CSV (one row per pair, with category scores) or JSON (full breakdown), by file extension."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".json":
        path.write_text(json.dumps([r.to_dict() for r in results], indent=2), encoding="utf-8")
        return path
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["candidate_id", "job_id", "score", "coverage", "skills", "culture", "trajectory", "logistics",
                    "config_version", "computed_at", "breakdown"])
        for r in results:
            cat = {c.name: c.score for c in r.categories}
            w.writerow([r.candidate_id, r.job_id, r.score, r.coverage,
                        *("" if cat.get(k) is None else round(cat[k], 2) for k in ("skills", "culture", "trajectory", "logistics")),
                        r.config_version, r.computed_at,
                        json.dumps({c.name: {f.name: f.score for f in c.factors} for c in r.categories})])
    return path
