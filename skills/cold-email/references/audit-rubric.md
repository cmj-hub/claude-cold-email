# 30-point outbound audit rubric

Score each point **1** (in place and working), **0.5** (in place but
partial, unmeasured, or inconsistent), or **0** (missing). If the
operator did not say, score 0 and mark it "Not in place / unknown" —
never assume a point is met.

Where a bundled script can settle a point, run it and cite the output
instead of taking the operator's word.

## Infrastructure — 8 points

| # | Point | 1 = | Evidence |
|---|---|---|---|
| I1 | Dedicated sending domain(s) | Cold mail goes from a subdomain or secondary domain, never the primary | Domain list |
| I2 | SPF | Published, includes the sending provider, ≤10 lookups | `check_deliverability.py` checks 1-3 |
| I3 | DKIM | Signing with a ≥1024-bit key (2048 preferred) | Checks 4-5 |
| I4 | DMARC | Record published with `rua=` reporting; policy moving toward `quarantine` | Checks 6-8 |
| I5 | Warm-up | Every mailbox warmed ≥21 days before cold volume | Operator answer |
| I6 | Volume per mailbox | Ramped gradually; daily cold sends per mailbox kept low (≤30 for the first 14 days) | Operator answer |
| I7 | Reputation | Not on Spamhaus DBL / SURBL; Postmaster spam rate <0.3% | Check 11 + Postmaster |
| I8 | Bounce rate | Hard bounces <2% per campaign | Sending-tool report |

## Targeting — 8 points

| # | Point | 1 = | Evidence |
|---|---|---|---|
| T1 | ICP sentence | One sentence naming stage, size, motion, region | `brand-config.icp.segment` |
| T2 | Exclusions | Written exclusion criteria, applied to lists | `icp.exclusion_criteria` |
| T3 | Signal anchors | Named signal types the program hunts for | `psp.signal_anchors` |
| T4 | Signal freshness | Signals ≤30 days old at send (≤14 ideal) | `score_list.py` freshness axis |
| T5 | Felt-pain role | Targets the role that feels the pain, not only the budget owner | `psp.felt_pain_role` vs list roles |
| T6 | List hygiene | No free-mail, role accounts, or duplicates | `score_list.py` dedup + validity axes |
| T7 | Segmentation | One sequence per signal type, not one sequence for everyone | Sequence list |
| T8 | List score | Latest list scores ≥75 | `score_list.py` |

## Messaging — 8 points

| # | Point | 1 = | Evidence |
|---|---|---|---|
| M1 | Length | T1 under 90 words | Word count |
| M2 | Signal opener | Line 1 quotes a public signal verbatim | Draft |
| M3 | Pain | One sentence, buyer's vocabulary | Draft vs `psp.vocabulary` |
| M4 | EVP | ≤22 words, one outcome with a number, one tradeoff | Draft |
| M5 | CTA | One binary, time-bound ask | Draft |
| M6 | Subject | ≤7 words, scores ≥70 | `score_subject_line.py` |
| M7 | Spam lint | Body + subject score ≥75 | `spam_word_lint.py` |
| M8 | Follow-ups | Each touch adds a new angle; no "just bumping" | Sequence |

## Operations — 6 points

| # | Point | 1 = | Evidence |
|---|---|---|---|
| O1 | Reply SLA | Buy-signal replies answered within 4 business hours | Operator answer |
| O2 | Reply routing | Every reply category has a written route | `operations.reply_routing` |
| O3 | Booking | One defined booking motion (link in reply, not in T1) | Operator answer |
| O4 | Hand-off | Sales receives signal + pain + thread, not just a name | Operator answer |
| O5 | Weekly review | Reply rate, positive rate, bounce, and complaints reviewed weekly; experiments logged | `operations.experiment_log_path` |
| O6 | Opt-outs | Opt-outs suppressed across all mailboxes within 10 business days | Operator answer |

## Totals

```
Score = (sum of points / 30) * 100
```

| Dimension | Max |
|---|---|
| Infrastructure | 8 |
| Targeting | 8 |
| Messaging | 8 |
| Operations | 6 |

Infrastructure failures (I2-I4, I7) cap the useful grade: messaging
work does not matter while mail is not landing. Say so in the top-3
levers.
