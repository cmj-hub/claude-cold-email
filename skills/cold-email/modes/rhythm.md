# Rhythm — this week's Mon / Wed / Fri queue

Walks the operator through the weekly cadence (Monday list refresh, Wednesday ship and triage, Friday review) and surfaces what is due today. The framework and the infrastructure are necessary; the cadence is what ships.

## Contents

- Activation
- The default rhythm (Mon / Wed / Fri)
- Friday review — quarterly meta
- Why cadence beats tactics
- References

## Activation

Loaded by `status` mode when the operator is in iteration mode
(reply data available, brand-config set up).

User-invocable on demand:
- "What's my cold-email rhythm this week"
- "Run the weekly rhythm"
- "Monday queue"
- "Friday review"

## The default rhythm (Mon / Wed / Fri)

### Monday — PSP signals + list refresh

Goals:
- Refresh the list with this week's signals (≤14 days old)
- Score list quality (dedup, role-fit, freshness)
- Set the week's send target (volume × personalization depth)

Tasks the skill runs:

1. **Pull signals**: For each anchor in `brand-config.psp.signal_anchors`,
   surface 5-10 new candidates from the operator's sources (LinkedIn job
   search, Crunchbase, RSS, etc.)
2. **Score the list**: run the `list` mode on `gtm/send-list.csv` for dedup +
   role-fit + freshness scoring
3. **Set the queue**: Recommend send volume based on:
   - Warm-up state (`brand-config.infrastructure.warm_up_status`)
   - Reply-rate trend from last week
   - Available personalization time

Output:

```markdown
# Monday — <date>

## This week's send queue
- Volume: <N> sends across <M> sequences
- Personalization depth: deep (≤30/seq) / medium (≤80/seq) / light (≤200/seq)

## Signal hunt (top 5 to verify by Wednesday)
1. <Company> — <signal>
2. <Company> — <signal>
3. ...

## List quality
- Score: <0-100>
- Dedup: <N> removed
- Role-fit: <N> outside ICP — flagged for removal
- Freshness: <N> stale signals removed

## Next: Wednesday ship + Friday review
```

### Wednesday — sequence ship + reply triage

Goals:
- Ship this week's sequence (T1 for new prospects, T2/T3/T4 for in-flight)
- Triage reply pile from earlier in the week

Tasks:

1. **Draft sequences** via `craft` mode using the operator's
   brand-config + SOUL.md voice
2. **Self-check each draft** via `cold-email-reviewer` agent
3. **Spam-lint** via `lint` mode
4. **Route to send infrastructure** (the operator's actual sending stack)
5. **Triage replies** received since Monday:
   - Save them to `gtm/replies.jsonl` and score the batch via `reply` mode
   - Route per `brand-config.operations.reply_routing`

Output:

```markdown
# Wednesday — <date>

## Sequences shipping today
- T1 (new): <N> drafts, <N> passed self-check
- T2/T3/T4 (in-flight): <N> sends

## Reply triage (since Monday)
- Buy-signal: <N> (route to sales)
- Positive: <N> (reply within 4 hours per ops)
- Neutral: <N> (add to nurture stream)
- Not-interested: <N> (suppress + log reason)

## Flagged for review
- <draft> failed self-check on <reason>
- <reply> ambiguous — needs human read
```

### Friday — score + adjust

Goals:
- Compute this week's metrics
- Compare to last week
- Surface 1 adjustment for next week (just one — don't compound changes)

Tasks:

1. **Compute weekly metrics** from logs:
   - Sends, opens (if tracked), replies, positive-reply rate, buy-signal rate
   - Time-to-reply distribution
   - Top-performing subject lines / first-line patterns
2. **Compare to last week** + last 4-week trend
3. **Surface 1 lever to adjust** next week — the highest-leverage
   single change

Output:

```markdown
# Friday — <date>

## This week's numbers
| Metric | This week | Last week | 4-wk trend |
|---|---|---|---|
| Sends | <N> | <N> | ↑ / ↓ / → |
| Reply rate | <%> | <%> | ↑ / ↓ / → |
| Positive-reply rate | <%> | <%> | ↑ / ↓ / → |
| Buy-signal rate | <%> | <%> | ↑ / ↓ / → |

## What worked
- Top subject pattern: "<pattern>" — <N>% open
- Top first-line: signal-quoted opener with <pattern>

## What didn't
- <observation with data>

## Single lever for next week
<ONE specific change. Not a list. One.>
Reason: <one sentence>
Verify by: <metric to watch>
```

## Friday review — quarterly meta

Every 13 weeks (quarter), the skill also runs a meta-review:

- ICP precision check — has it tightened or drifted?
- PSP refresh — have signals decayed? Is the vocabulary still current?
- EVP review — is the line still landing, or has the market caught up?
- Infrastructure age check — is the sending domain still in good shape?
- Banned-phrases list — any new patterns the operator should add?

The meta-review surfaces a single Q-level adjustment, not weekly-level
tweaks.

## Why cadence beats tactics

The framework is 80% of the lever. The remaining 20% is whether the
operator runs it weekly without skipping. Skipping a week is fine.
Skipping two compounds — the list goes stale, signals decay, replies
get cold, the sender's confidence drops.

The skill enforces the cadence by surfacing what's due TODAY when
invoked. No project-management software, no big planning ritual —
just "here's what Monday needs from you."

## References

- [list.md](list.md) — Monday list scoring
- [craft.md](craft.md) — Wednesday drafting
- [reply.md](reply.md) — Wednesday + Friday triage
- [lint.md](lint.md) — Wednesday pre-send gate
- [audit.md](audit.md) — quarterly meta-review
- `${CLAUDE_PLUGIN_ROOT}/scripts/` — Python scoring scripts the skills shell out to
