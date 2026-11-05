# Candidate ↔ Job Matching Algorithm

Python implementation of the **Candidate ↔ Job Match Score** diagram. It ranks jobs for a candidate (and candidates for a job)
using the 1DGR sample data in `data/sample`.

```
Step 1: Must pass  ──►  Skills & Qualifications 35%  ┐
(open to work,          Values & Culture        25%  ├──►  Match Score (0–100)  ──►  List of ranked jobs
 work authorization,    Career Trajectory       20%  │     used to rank only;
 FCRA consent,          Logistics               20%  ┘     stored, never shown to users
 job search status)
```

Requires **Python 3.9+**. The algorithm uses only the standard library; `pytest` is needed only to run the tests.

## Quick start

```bash
# Ranked jobs for a candidate (what the candidate sees: no scores)
python -m matching rank --data data/sample --candidate "Priya Ibrahim"

# Same list with scores and category breakdowns (team use only)
python -m matching rank --data data/sample --candidate "Priya Ibrahim" --internal

# Ranked candidates for one job (company view); use the first characters of a job ID
python -m matching candidates --data data/sample --job 9152dab8

# Score every eligible pair and store the results
python -m matching run --data data/sample --out results/match_results.csv

# Check the planted test cases in expected_matches
python -m matching evaluate --data data/sample --as-of 2026-10-22

# Run the tests
pip install pytest
python -m pytest
```

Use `--as-of 2026-10-22` for repeatable results on the sample data. That is the date it was generated for; availability and
fill dates are compared against it. Without `--as-of`, today's date is used.

## Code layout

| File | What it does |
|---|---|
| `matching/config.py` | All weights. Category weights are from the diagram; factor weights inside each category are starting values to tune. |
| `matching/gate.py` | Step 1: must pass. Missing gate data fails the gate, the same as "no". |
| `matching/scoring.py` | The four categories. Each factor returns 0–1, or "missing" when either side has no data. |
| `matching/engine.py` | Runs the gate, blends categories into the match score, ranks, and builds the user-facing lists. |
| `matching/normalize.py` | Cleans messy input: salary text, availability text, locations, skill synonyms, job-title seniority. |
| `matching/vocab.py` | Word lists: skill synonyms, related industries, seniority keywords, education ranks. |
| `matching/loader.py` | The only file that knows 1DGR field names. Replace or extend it when real data arrives. |
| `matching/store.py` | Writes stored results (CSV or JSON) with scores and per-factor breakdowns. |
| `matching/evaluate.py` | Checks results against `expected_matches`. |
| `tests/` | Unit tests plus a full run on the sample data. |

## How scoring works

**Step 1 (must pass).** A candidate is scored only if all four gate fields are present and pass:

- open to work is `true`;
- work authorization (`residency`) is present;
- FCRA consent is `true`;
- job search status is "Actively looking" or "Open to offers".

Closed and paused jobs are never scored. A candidate who needs sponsorship (`VISA_HOLDER` / `OTHER`) passes only for jobs
that offer sponsorship or don't require US work authorization.

**Categories.** Each factor scores 0–1. Each category is the weighted average of its factors that have data, scaled to 0–100.
The match score is the diagram's blend:
`0.35 × Skills + 0.25 × Culture + 0.20 × Trajectory + 0.20 × Logistics`.

| Category | Factor (weight in category) | Rule |
|---|---|---|
| **Skills & Qualifications** | Skills (50%) | Share of the job's required skills the candidate has, after synonym matching |
| | Education (15%) | 1 if the degree requirement is met · 0.8 if a degree in progress meets it · 0.5 if one level below · else 0 |
| | Certifications (5%), Languages (5%) | Share of the job's required ones the candidate has (only when the job lists any) |
| | Achievements & awards (5%) | Number listed, full credit at 3 |
| | Work history (20%) | Half for how related past roles are, half for years in related roles vs. what the job's level needs |
| **Values & Culture** | Core values (60%) | Shared values ÷ size of the smaller list |
| | Bio ↔ mission / why us (40%) | Text similarity of the bio vs. the company's mission and why-us text |
| **Career Trajectory** | Industry (35%) | 1 if the industry is an interest · 0.5 if a related industry · else 0 |
| | Target role (35%) | Best title similarity between a target role and the job title, ignoring words like "Junior" |
| | Seniority (15%) | 1 at the same level · 0.6 one level apart · 0.2 two levels apart |
| | Role level (15%) | 1 if the job is the same level or one step above the last role; lower for bigger jumps or step-downs |
| **Logistics** | Work type (25%) | Arrangement (remote / hybrid / on-site) and employment type (full-time, internship, …) |
| | Location / relocation (30%) | 1 for remote roles or the same city · 0.75 if willing to relocate and relocation is covered · 0.4 if willing but not covered · 0.5 if unknown · 0 if not willing |
| | Headquarters (5%) | 1 if the candidate is in a city where the company has an office (non-remote roles) |
| | Pay (25%) | 1 if the pay target is at or below the top of the range, falling to 0 at 30% above it |
| | Availability (15%) | 1 if available by the start date (or posted date + time to fill) · 0.5 within 30 days after · 0.25 within 60 |

**Missing data.** When a factor has no data on one side, it is left out and the other weights in its category are
re-weighted, so incomplete profiles still get results. Each stored result has a `coverage` value showing how much of the
total weight had data.

**Fairness.** Names, date of birth, photos, and videos are never used in scoring. Residency is used only for the
work-authorization check.

**Ties** are broken by newest posting date, then job ID, so the same data always gives the same order.

## Changing weights

Edit `matching/config.py`, or pass a config in code:

```python
from matching import MatchConfig, MatchingEngine, load_dataset

cfg = MatchConfig(version="sponsor-v2",
                  category_weights={"skills": 0.40, "culture": 0.20, "trajectory": 0.20, "logistics": 0.20})
engine = MatchingEngine(load_dataset("data/sample"), config=cfg)
for job in engine.rank_jobs(candidate_id, top_n=5):
    print(job.rank, job.title, job.company_name)
```

Every set of weights must add up to 1.0, or the config raises an error. Stored results record `config_version`, so
results from different weight settings can be told apart.

## Data notes

The diagram's gate needs FCRA consent and job search status, and the logistics category needs relocation willingness and
a start date. None of these are in the 1DGR ERD. The sample data provides them as `proposed_fcra_consent`,
`proposed_job_search_status`, `proposed_willing_to_relocate`, `proposed_employment_type`, and `proposed_start_date`.
The loader also accepts the same names without the `proposed_` prefix.
