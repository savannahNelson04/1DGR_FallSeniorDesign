"""
Check the engine against the planted cases in expected_matches (data/sample).

    strong          the planted job ranks in the candidate's top `strong_top_n`
    poor            the pair scores below `poor_max_score`
    sparse_profile  a mostly empty profile still gets at least one ranked job (FR-09)
    gate_excluded   the candidate fails Step 1 and gets no ranked jobs
    never_shown     a closed or paused job never appears in anyone's list
"""
from __future__ import annotations
from collections import defaultdict

from .engine import MatchingEngine


def evaluate(engine: MatchingEngine, strong_top_n: int = 5, poor_max_score: float = 50.0) -> dict:
    ranked = {cid: engine.ranked_results_for_candidate(cid) for cid in engine.data.candidates}
    shown_jobs = {r.job_id for rs in ranked.values() for r in rs}
    outcome = defaultdict(lambda: {"pass": 0, "fail": 0, "failures": []})

    for e in engine.data.expected:
        kind, cid, jid = e["expected_fit"], e.get("candidate_profile_id"), e.get("job_posting_id")
        ok, note = False, ""
        if kind == "strong":
            ids = [r.job_id for r in ranked.get(cid, [])]
            rank = ids.index(jid) + 1 if jid in ids else None
            ok, note = (rank is not None and rank <= strong_top_n), f"ranked {rank}" if rank else "not ranked"
        elif kind == "poor":
            r = engine.score_pair(engine.data.candidates[cid], engine.data.jobs[jid])
            ok, note = (r is None or r.score < poor_max_score), "gated" if r is None else f"score {r.score}"
        elif kind == "sparse_profile":
            ok, note = bool(ranked.get(cid)), f"{len(ranked.get(cid, []))} ranked jobs"
        elif kind == "gate_excluded":
            ok, note = not ranked.get(cid), "; ".join(engine.candidate_gate(cid).reasons) or "passed gate"
        elif kind == "never_shown":
            ok, note = jid not in shown_jobs, "never shown" if jid not in shown_jobs else "SHOWN"
        else:
            continue
        o = outcome[kind]
        o["pass" if ok else "fail"] += 1
        if not ok:
            o["failures"].append({"candidate": e.get("candidate_name"), "job": e.get("job_title"), "note": note})
    return dict(outcome)
