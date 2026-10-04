# Status — where the program is and the one next step

Reads the operator's project state and names the single next step. Runs on a bare `/cold-email:cold-email`, `status`, "where do I start", or "what's next".

## Contents

- State detection
- Welcome flow
- Status report
- Resume from a specific step
- Why one next step

## State detection

Check the project before recommending anything:

```python
# Pseudo-code
state = {
    "has_brand_config":   file_exists("brand-config.json"),
    "has_soul":           file_exists("SOUL.md"),
    "has_shared_setup":   brand_config.operator.name != "" and brand_config.icp.segment != "",
    "has_psp":            "psp" in brand_config and brand_config.psp.primary_pain != "",
    "has_evp":            "evp" in brand_config and brand_config.evp.primary != "",
    "has_infrastructure": brand_config.infrastructure.sending_domain != "",
    "deliverability_audited_recently": days_since(brand_config.infrastructure.deliverability_last_audited) < 30,
    "has_send_list":      file_exists("gtm/send-list.csv"),
    "has_letter":         file_exists("gtm/letter.json"),
    "has_replies":        file_exists("gtm/replies.jsonl") or has_logged_replies(brand_config.operations.experiment_log_path),
}
```

Map state to the next step. Name the command, not the internals:

| State condition | Next step |
|---|---|
| `!has_brand_config OR !has_shared_setup` | "Run `/gtm:setup` once for the whole suite, then `/cold-email:cold-email setup`." If the gtm plugin is not installed, go straight to `/cold-email:cold-email setup`; it asks the shared questions inline. |
| `!has_soul` or no cold-email fields (`tone`, `infrastructure`, `operations`) | `/cold-email:cold-email setup` |
| `!has_psp` | "No `psp` block. Install the psp pack (`/plugin install psp@gtm-operator-skills`), run `/psp:psp`, then come back." |
| `has_psp AND !has_evp` | "No `evp` block. Install the evp pack (`/plugin install evp@gtm-operator-skills`), run `/evp:evp`, then come back." |
| `!has_infrastructure OR !deliverability_audited_recently` | `/cold-email:cold-email deliverability` (baseline, or re-audit after 30+ days) |
| `!has_send_list` | "Pick who to contact with `/prospect-list:who-to-contact`, or save your list as `gtm/send-list.csv` and run `/cold-email:cold-email list`." |
| `!has_letter` | `/cold-email:cold-email write` (or `sequence` for all four touches) |
| `has_letter AND !has_replies` | "First touch drafted. Send it from your own tool; paste replies or save them to `gtm/replies.jsonl`, then `/cold-email:cold-email reply`." |
| `has_replies` | `/cold-email:cold-email rhythm` for this week's queue; `/cold-email:cold-email audit` once a quarter. A reply that opts in moves to `/email-sequence:lifecycle-email`. |

## Welcome flow

On first run with no state:

```
> /cold-email:cold-email

Welcome. Let's figure out where you are.

[Detected state: brand-config.json missing]

You're at step 1 of 7:

1. [ ] Shared setup + cold-email setup (10 min)   <- YOU ARE HERE
2. [ ] Pain Signal Profile (psp pack)
3. [ ] EVP for your primary tier (evp pack)
4. [ ] Sending infrastructure + 15-point deliverability check
5. [ ] Send list scored (gtm/send-list.csv)
6. [ ] First signal-anchored sequence drafted (gtm/letter.json)
7. [ ] Replies scored + weekly rhythm

Step 1 is required for everything else. Run it now? (y/n)
```

If yes, read [setup.md](setup.md) and follow it. If no, say what minimum mode produces (framework-shaped, generic) and stop.

## Status report

`/cold-email:cold-email status` returns:

```
# Cold email program status

Brand config:      yes  brand-config.json (operator, icp, tone, infrastructure, operations)
Voice (SOUL.md):   yes  8 phrases used, 6 refused, 5 stories
PSP:               yes  Series-B SaaS pipeline-gap pain
EVP:               yes  Tier 3: "For Series-B SaaS, in a pipeline gap, we ship 14+ SQLs/month without hiring 2 SDRs"
Infrastructure:    yes  outreach.acmecloud.com (ramped 60+ days, DMARC quarantine)
Deliverability:    yes  last audited 2026-09-20 — 94/100
Send list:         yes  gtm/send-list.csv — 82/100
First touch:       yes  gtm/letter.json — passes score_letter.py
Replies:           yes  gtm/replies.jsonl — 11 (4 positive, 2 buy-signal, 5 neutral)

Next: /cold-email:cold-email rhythm
```

Only report what you read. A field you could not find is "missing", never guessed. End with exactly one `Next:` line.

## Resume from a specific step

`/cold-email:cold-email status resume <step>`, where step is `setup | psp | evp | deliverability | list | write | reply | rhythm`. Jump to that step regardless of detected state.

## Why one next step

A menu of eleven modes overwhelms. State-aware routing surfaces the one step that matters given where the operator actually is.
