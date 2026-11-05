"""
Step 1: Must pass.

Per the diagram, the algorithm does not run for a candidate unless all four gate
fields are present and pass: open to work, work authorization, FCRA consent, and
job search status. Missing data fails the gate, the same as a "no".

Two more checks keep pairs out of scoring:
  * Jobs must be open and not paused.
  * Work authorization is also checked per job: a candidate who needs sponsorship
    only passes for jobs that offer it (configurable).
"""
from .config import MatchConfig
from .models import Candidate, GateResult, Job


def check_candidate(c: Candidate, cfg: MatchConfig) -> GateResult:
    reasons = []
    if c.open_to_work is None:
        reasons.append("missing: open to work")
    elif not c.open_to_work:
        reasons.append("not open to work")

    if not (c.residency or "").strip():
        reasons.append("missing: work authorization")

    if c.fcra_consent is None:
        reasons.append("missing: FCRA consent")
    elif not c.fcra_consent:
        reasons.append("FCRA consent not given")

    status = (c.job_search_status or "").strip().lower()
    if not status:
        reasons.append("missing: job search status")
    elif status not in cfg.searching_statuses:
        reasons.append(f"job search status is '{c.job_search_status}'")

    return GateResult(passed=not reasons, reasons=reasons)


def check_job(j: Job) -> GateResult:
    reasons = []
    if (j.status or "").strip().lower() != "open":
        reasons.append(f"posting status is '{j.status}'")
    if j.is_paused:
        reasons.append("posting is paused")
    return GateResult(passed=not reasons, reasons=reasons)


def check_pair(c: Candidate, j: Job, cfg: MatchConfig) -> GateResult:
    """Work authorization for this specific job."""
    if not cfg.sponsorship_required_for_others:
        return GateResult(True)
    authorized = (c.residency or "").strip().upper() in cfg.authorized_residency
    if authorized or not j.requires_us_work_authorization or j.sponsorship_available:
        return GateResult(True)
    return GateResult(False, ["job requires US work authorization and does not offer sponsorship"])
