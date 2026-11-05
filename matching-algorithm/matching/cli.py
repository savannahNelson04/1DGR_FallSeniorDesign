"""
Command line:

    python -m matching rank       --data data/sample --candidate "Maya Okafor" [--top 5] [--internal]
    python -m matching candidates --data data/sample --job <job_id> [--top 10] [--internal]
    python -m matching run        --data data/sample --out results/match_results.csv
    python -m matching evaluate   --data data/sample

--internal prints scores and category breakdowns for the team. Users never see these.
"""
from __future__ import annotations
import argparse
import sys
from datetime import date

from .engine import MatchingEngine
from .evaluate import evaluate
from .loader import load_dataset
from .store import write_results


def _find_candidate(engine: MatchingEngine, key: str) -> str:
    k = key.strip().lower()
    for cid, c in engine.data.candidates.items():
        if cid.lower().startswith(k) or c.display_name.lower() == k:
            return cid
    sys.exit(f"No candidate matches '{key}' (use a profile_id or a full name).")


def _find_job(engine: MatchingEngine, key: str) -> str:
    for jid in engine.data.jobs:
        if jid.lower().startswith(key.strip().lower()):
            return jid
    sys.exit(f"No job matches '{key}'.")


def _breakdown(r) -> str:
    return "  ".join(f"{c.name} {'-' if c.score is None else f'{c.score:.0f}'}" for c in r.categories)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m matching", description="Candidate <-> job matching")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("rank", "candidates", "run", "evaluate"):
        s = sub.add_parser(name)
        s.add_argument("--data", required=True, help="folder with json/ or csv/ files, e.g. data/sample")
        s.add_argument("--as-of", type=date.fromisoformat, default=None, help="score as of this date (default: today)")
        if name == "rank":
            s.add_argument("--candidate", required=True)
            s.add_argument("--top", type=int, default=5)
            s.add_argument("--internal", action="store_true", help="show scores (team use only)")
        if name == "candidates":
            s.add_argument("--job", required=True)
            s.add_argument("--top", type=int, default=10)
            s.add_argument("--internal", action="store_true", help="show scores (team use only)")
        if name == "run":
            s.add_argument("--out", default="results/match_results.csv", help=".csv or .json")
    a = p.parse_args(argv)

    engine = MatchingEngine(load_dataset(a.data), as_of=a.as_of)

    if a.cmd == "rank":
        cid = _find_candidate(engine, a.candidate)
        c = engine.data.candidates[cid]
        g = engine.candidate_gate(cid)
        print(f"{c.display_name} ({cid[:8]})")
        if not g.passed:
            print("Not ranked. Step 1 must-pass failed: " + "; ".join(g.reasons))
            return
        results = engine.ranked_results_for_candidate(cid)[:a.top]
        for item, r in zip(engine.rank_jobs(cid, a.top), results):
            print(f"{item.rank:>2}. {item.title} at {item.company_name} ({item.location})")
            if item.highlights:
                print("      " + " | ".join(item.highlights))
            if a.internal:
                print(f"      [internal] score {r.score:.1f}  coverage {r.coverage:.0%}  {_breakdown(r)}")

    elif a.cmd == "candidates":
        jid = _find_job(engine, a.job)
        j = engine.data.jobs[jid]
        print(f"{j.title} ({jid[:8]})")
        ranked = engine.rank_candidates(jid, a.top)
        if not ranked:
            print("No eligible candidates.")
        for item in ranked:
            line = f"{item.rank:>2}. {item.display_name}"
            if a.internal:
                line += f"   [internal] score {engine.results[(item.candidate_id, jid)].score:.1f}"
            print(line)
            if item.highlights:
                print("      " + " | ".join(item.highlights))

    elif a.cmd == "run":
        results = engine.score_all()
        out = write_results(results, a.out)
        passed = sum(1 for g in engine._candidate_gate.values() if g.passed)
        print(f"Scored {len(results)} pairs for {passed} of {len(engine.data.candidates)} candidates "
              f"(others failed Step 1). Stored in {out}")

    elif a.cmd == "evaluate":
        if not engine.data.expected:
            sys.exit("No expected_matches file found in the data folder.")
        report = evaluate(engine)
        total_fail = 0
        for kind, o in report.items():
            print(f"{kind:<15} {o['pass']:>3} passed  {o['fail']:>3} failed")
            for f in o["failures"]:
                print(f"    - {f['candidate']} / {f['job']}: {f['note']}")
            total_fail += o["fail"]
        sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()
