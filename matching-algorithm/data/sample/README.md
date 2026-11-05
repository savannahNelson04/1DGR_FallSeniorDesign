# Sample Data — AI Matching Buildout Prototype

Fictional test data in the shape of the 1DGR platform schema, used by the prototype's Data Input Adapter (SED Section 5.3).
**All people and companies are invented.** Emails use `example.com` / `.example` domains and phone numbers use the reserved
`555-01xx` range. Universities and their IPEDS `unitid` values are real; verify them against IPEDS before production use.

## What's here

| File | Rows | Maps to 1DGR table |
|---|---|---|
| `users` | 200 | `users` (100 candidates + 100 company accounts) |
| `student_profiles` | 100 | `student_profiles` |
| `student_higher_education` | 122 | `student_higher_education` |
| `company_profiles` | 100 | `company_profiles` |
| `job_postings` | 192 | `job_postings` (1–3 per company) |
| `expected_matches` | 59 | — test cases for the evaluation harness |

Each file comes in two formats with identical content: `csv/` (easy to open and diff on GitHub) and `json/` (nested fields stay as real objects).

## What the data covers

- **Companies:** 18 industries, 25 US metro areas, all company sizes and ages; work arrangements are Hybrid, On-site, and Remote.
- **Job postings:** 133 full-time, 51 internships, 4 part-time, 4 contract. 164 are open, 15 are paused, and 13 are closed.
- **Candidates:** 20 current students (highest education `HIGH_SCHOOL`, degree in progress), 58 with bachelor's degrees,
  16 with master's, 6 with PhDs, plus a few career changers. 8 are not open to work and about 6 have mostly empty profiles.
- **Messy fields on purpose:** `salary` uses mixed formats (`$65,000 - $75,000 per year`, `$82K-$120K`, `$24/hr`, `Competitive`, `DOE`)
  so the Normalizer can be tested against realistic input.

## Conventions

- **IDs** are UUIDs and are consistent across files: `company_profiles.user_id` = `job_postings.company_id` = `users.id`;
  `student_profiles.user_id` = `student_higher_education.user_id` = `users.id`.
- **Arrays and JSON fields** (for example `hard_skills`, `skills`, `work_history`, `locations`) are JSON-encoded strings in the CSV files.
- **Booleans** are `true` / `false`. **Empty values** are blank cells in CSV and `""` or `null` in JSON.
- **`work_type`** is the work arrangement (Remote / Hybrid / On-site). **`work_preference`** is the employment type (Full-time / Internship / Part-time / Contract).
  These interpretations are assumptions to confirm with 1DGR.
- **`residency`** uses the `residency_status` enum and **`experience`** uses the `industry_exp` enum from the ERD.
- Media keys (`avatar_image_key`, `resume_key`, logos) are placeholder paths; no files exist.
- `account_kind` in `users` is a helper column, not part of the 1DGR schema.
- The 13 `show_*` flags on `company_profiles` are omitted because their names are not in the ERD.

## Proposed fields (not in the 1DGR schema)

The ERD has no candidate relocation field and no job start date, but FR-01 needs both (SED risk R-07). These columns are included
so the scorers can be tested, and are prefixed `proposed_` so a loader can drop them:

- `student_profiles.proposed_willing_to_relocate`
- `job_postings.proposed_employment_type`
- `job_postings.proposed_start_date`

## Expected matches (evaluation harness)

`expected_matches` lists cases with a known correct answer:

| `expected_fit` | Count | Meaning |
|---|---|---|
| `strong` | 20 | Candidate built from this posting: all required skills, same city or remote, same employment type and work arrangement, pay target in range, industry interest. Should rank in the candidate's top results. |
| `poor` | 5 | Same field as the posting, but only one required skill, opposite work arrangement, different city with no relocation, and a pay target far above the range. Should score low. |
| `sparse_profile` | 6 | Mostly empty profile. Should still receive results (FR-09) with a low criteria count. |
| `never_shown` | 28 | Closed or paused posting (`candidate_profile_id` = `*`). Should never appear for anyone. |
