---
name: cold-email-list-quality
description: Score a cold-email prospect list 0-100 across dedup, role-fit (vs brand-config.icp), signal freshness, email-validity heuristics, exclusion-criteria match, and company-stage match. Returns the score, list of rows to remove, and a fix recommendation. Loaded by cold-email-weekly-rhythm on Monday's list refresh. Operates on CSV or JSONL; no external services.
user-invocable: false
allowed-tools: Read Write Grep Bash(python3 scripts/score_list.py:*)
license: MIT

---

# Cold Email List Quality — list scoring + dedup

Run before any campaign. Bad lists kill reply rates more than bad
copy. This sub-skill scores the list across 6 axes, returns the rows
to remove, and surfaces fix recommendations.

## Activation

Loaded by:
- `cold-email-weekly-rhythm` — Monday's list refresh
- User invocation: "Score my list", "Check list quality", "Clean my prospect list"

## Inputs

The skill accepts:

- **CSV** with at minimum: `email`, optional `first_name`, `last_name`,
  `role`, `company`, `signal`, `signal_date` (YYYY-MM-DD), `linkedin_url`,
  `stage`, `industry`
- **JSONL** with same fields

If `brand-config.json` is loaded, the skill cross-references
`icp.segment`, `icp.role_targets`, `icp.exclusion_criteria`, and
`psp.signal_anchors` for scoring.

## Scoring (6 axes, 100 total)

| Axis | Max | What it catches |
|---|---|---|
| Dedup | 20 | Exact-match emails, near-duplicate same-company-same-person rows |
| Role-fit | 25 | Role title matches `brand-config.icp.role_targets` or known equivalents |
| Signal freshness | 20 | Signal age — fresh (≤14d) > recent (15-30d) > stale (>30d) |
| Email validity | 15 | Heuristic checks — RFC-shaped, no plus-extensions for B2B, no free-email domains, no role-account emails (info@, sales@) |
| Exclusion match | 10 | Row matches any `brand-config.icp.exclusion_criteria` → fail |
| Company-stage match | 10 | Company stage (from signal or heuristic) matches ICP segment |

## Output

```markdown
# List Quality Score — <file>

## Overall: <0-100>/100

| Axis | Score | Issues |
|---|---|---|
| Dedup | <0-20>/20 | <N> duplicate rows |
| Role-fit | <0-25>/25 | <N> rows outside ICP role targets |
| Signal freshness | <0-20>/20 | <N> stale signals (>30d) |
| Email validity | <0-15>/15 | <N> invalid / free-email / role-account |
| Exclusion match | <0-10>/10 | <N> rows hit exclusion criteria |
| Company-stage match | <0-10>/10 | <N> wrong-stage companies |

## Rows to remove (<N> total)

| Row | Email | Reason |
|---|---|---|
| 12 | sarah@gmail.com | Free-email domain (B2B) |
| 14 | info@acme.com | Role-account email |
| 22 | mike@acme.com (Engineering Manager) | Role outside ICP (target: VP+) |
| 27 | jane@beta.com | Signal stale (45 days) |
| ... |

## Fix recommendations (in order)

1. Remove the 12 free-email + role-account rows (immediate)
2. Re-pull signals for the 8 stale rows (today)
3. Tighten role-fit list — 14 rows are "Engineering Manager" / "Director"
   while ICP targets VP+. Consider adding "Director" if the ICP has
   shifted, or excluding these rows.
4. Run `cold-email-deliverability` on the sending domain before this
   list ships.

## Send-volume recommendation

With cleaning, the deliverable list is: <N - removed> rows.

Given warm-up state (`<warm_up_status>`), recommended weekly send
volume: <X> per day across <M> mailboxes = <X*M> per day = <X*M*5>
per week.

## Send the cleaned list

With `--write`, the script writes `<file>.cleaned.csv` and
`<file>.removed.csv` (with a `removal_reason` column) next to the input.
Ask before writing. The operator reviews both before importing into
Smartlead / Instantly / etc.
```

## What gets flagged automatically

### Dedup
- Same email → duplicate (keep the first row, remove the rest)
- Same `linkedin_url` → duplicate (remove all but most-recent signal)
- Same `first_name + last_name + company` → near-duplicate (warn,
  don't auto-remove — might be father/son etc.)

### Role-fit
- Compare each `role` against `brand-config.icp.role_targets`
- Apply role-equivalent map (built-in):
  - "Demand Gen Lead" ↔ "Head of Demand Generation" ↔ "VP Demand Gen"
  - "CRO" ↔ "Chief Revenue Officer" ↔ "VP Revenue"
  - etc.
- Rows where role doesn't match any target → flag with severity

### Signal freshness
- Compare `signal_date` to today
- Score:
  - 0-7 days = full score
  - 8-14 days = full score
  - 15-30 days = half score + warn
  - >30 days = zero score + recommend removal

### Email validity heuristics
- RFC-shape (`@`, `.`, no spaces)
- Free-email domains (gmail.com, yahoo.com, outlook.com, hotmail.com,
  proton.me, icloud.com, aol.com, gmx.com)
- Role-account patterns (info@, sales@, support@, hello@, contact@,
  marketing@, hr@, jobs@, careers@, admin@)
- Plus-extension addresses (alex+marketing@acme.com) — flag as warn

### Exclusion match
- Each row scored against each `exclusion_criteria` entry
- Examples: "Pre-PMF (<$2M ARR)", "Enterprise-only ACV >$100k",
  "Government/regulated industries"
- Matches whole words from each criterion (text in parentheses is ignored)
  against the row's `company`, `industry`, `stage`, `segment`, `notes`,
  `signal`, and `tags` columns

### Company-stage match
- Read the row's `stage` column (Seed, Series A-F, Growth, Public)
- Match against the stage named in `icp.segment` ("Series-B SaaS" → Series B)
- Out-of-stage rows are a warning, not an automatic removal
- Out-of-stage rows flagged

## Implementation

Backed by `scripts/score_list.py` (Python 3.8+, stdlib only, no network).
`scripts/` is at the pack root — `<skill-dir>/../../scripts/`.

```bash
python3 scripts/score_list.py \
    --input prospects.csv \
    --brand-config brand-config.json \
    --format json
# add --write to produce prospects.cleaned.csv + prospects.removed.csv
```

Try it on the bundled sample: `examples/prospects.csv`.

How the script scores:

- Each axis earns its points in proportion to the rows that pass it.
  An axis with nothing to judge (no brand-config, no `signal_date` or
  `stage` column) is `n/a` and left out — never counted as a pass.
- The overall score is half the axis points and half the share of rows
  that survive cleaning, so a list where most rows fail *something*
  cannot score well.
- Exit 0 at 75+, 1 below, 2 on bad input.
- Signal freshness uses today's date; pass `--today YYYY-MM-DD` to
  re-score against a fixed date.

What the script does **not** do: stage inference from free-text signals,
external enrichment, or SMTP mailbox verification. Say so when those
matter for the decision.

## References

- `brand-config.json` — ICP, exclusion, role targets, PSP signal anchors
- `../cold-email-weekly-rhythm/SKILL.md` — Monday's caller
- `../../scripts/score_list.py` — the scorer
- Send-volume math: warm-up rows in `../cold-email-deliverability/SKILL.md`
