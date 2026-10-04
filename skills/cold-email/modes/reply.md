# Reply — classify one reply or a batch

Classifies replies as buy-signal, positive, neutral, not-interested, or auto-reply with `score_reply.py` (regex and features, no LLM), then routes each per `brand-config.operations.reply_routing`.

## Contents

- Activation
- Output categories
- Feature set (what the classifier uses)
- Output format
- Batch mode
- Why deterministic > LLM here
- False-positive handling
- Calibration
- References

## Activation

Loaded by:
- `rhythm` mode — Wednesday + Friday reply triage
- User invocation: "Score this reply", "Classify this response"

## Output categories

The classifier returns one of 4 categories with a confidence score:

| Category | Signal | Routing (per brand-config) |
|---|---|---|
| `buy-signal` | Explicit ask to talk, calendar request, price question, decision-maker tag | `brand-config.operations.reply_routing.buy_signal` |
| `positive` | Curious, asking follow-up Qs, expressing interest, asking for proof | `positive` |
| `neutral` | "Not now", "circle back later", "send more info" without commitment | `neutral` (often → nurture stream) |
| `not-interested` | Explicit no, unsubscribe ask, hostile, out-of-office on repeat | `not-interested` |

## Feature set (what the classifier uses)

Pure feature engineering — no LLM, no vendor APIs:

1. **Intent keywords** — regex over 50+ patterns per category
   - buy-signal: "send the calendar", "what's the price", "demo", "case study", "intro"
   - positive: "tell me more", "interesting", "curious", "send the deck"
   - neutral: "not the right time", "Q4", "send more info", "in a few months"
   - not-interested: "unsubscribe", "stop emailing", "not a fit", "no thanks"

2. **Time-to-reply** — minutes since send
   - <15 min after send → likely auto-reply (out-of-office, etc.)
   - <60 min → high-intent (operator was working, saw it, replied immediately)
   - 60 min - 24h → engaged reply
   - >24h → background reply

3. **Reply length** — chars
   - <20 chars → 1-word answer, usually not-interested or short positive
   - 20-200 → typical engaged reply
   - >200 → often a substantive response (rare; high-signal)

4. **Question count** — # of "?" in the body
   - 0 → declarative (could be any category)
   - 1-2 → engaged with specific questions
   - 3+ → either highly engaged or asking-for-everything (lower convert)

5. **Calendar / asset ask** — regex
   - "send <calendar link>", "let's get a time", "what dates work" → buy-signal
   - "send the case study", "send the deck" → positive (could be buy-signal if combined with other features)

6. **Out-of-office indicators** — regex
   - "out of office", "OOO", "auto-reply", "I'm currently away" → exclude from scoring
   - These get marked `auto-reply` (5th category) and not routed

## Output format

```markdown
# Reply scoring

From: <sender>
Subject: Re: <original subject>
Time-to-reply: <minutes since send>
Length: <N chars>

## Classification
Category: **buy-signal** (confidence: 0.87)

## Why
- "send me a calendar link" → buy-signal +0.5
- "what's the price for Series-B teams" → buy-signal +0.4
- Reply within 27 minutes → buy-signal +0.2
- Length 142 chars → engaged-length +0.1
- No not-interested patterns matched

## Recommended routing
Per your brand-config.operations.reply_routing.buy_signal:
→ Slack #pipeline + create HS deal
→ Reply within 4 hours

## Suggested reply opener (not generated; use your own voice)
"Sent — calendar link [here]. <Specific qualifying Q to set the agenda>"
```

## Batch mode

For triaging the Wednesday/Friday batch of replies:

```bash
# gtm/replies.jsonl: one {"id": "...", "body": "...", "minutes_since_send": N} per line
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score_reply.py --file gtm/replies.jsonl --json
```

(Create `gtm/` if missing. `--batch` is the old name for `--file`. Bad
lines are reported on stderr by line number and skipped; the rest still
score.) Every result carries a `next` step for its category: buy-signal
and positive replies get an answer within 4 hours, and a prospect who
opts in moves to the email-sequence pack (`/email-sequence:lifecycle-email`);
neutral goes to `/cold-email:cold-email nurture`; not-interested is
suppressed.

Output:

```
# Batch reply scoring — <date>

| # | From | Category | Confidence | Route |
|---|---|---|---|---|
| 1 | sarah@acme.com | buy-signal | 0.87 | Slack + HS deal |
| 2 | mike@beta.io | positive | 0.74 | Reply <4h |
| 3 | hr@autoresponder.co | auto-reply | 1.00 | Skip |
| 4 | bob@churn.com | not-interested | 0.92 | Suppress + log |
| ... |
```

## Why deterministic > LLM here

Reply classification is high-throughput (50-200/week per operator).
LLM classification:
- Costs money per reply
- Adds 1-3 seconds latency per reply
- Drifts as LLMs version
- Hard to audit

Feature-based classification:
- Zero cost per reply
- <10ms per reply
- Stable across years
- Fully auditable (every score has a feature contribution list)

For a 100-reply week, the deterministic classifier runs in <1 second
and gives the same answer in 6 months as it does today.

## False-positive handling

The script flags **low-confidence** classifications (confidence <0.6)
for human review. These are usually:
- Short replies (1-3 words) that could go either way
- Replies in non-English (the lexicon is English-only)
- Sarcasm / context-dependent meaning

Low-confidence replies surface as:

```
# Manual review needed

<sender>: "<reply body>"
Category candidates: positive (0.42) | neutral (0.38)
→ Read carefully before routing
```

## Calibration

The patterns are hand-tuned. No accuracy figure ships with the pack, so
don't quote one. Two rules keep mistakes cheap:

- A reply that matches no pattern is `neutral` with confidence 0 and
  `needs_review: true`. Length and reply time alone never decide a
  category, so "Who is this?" goes to a human, not the suppression list.
- Anything under 0.6 confidence is flagged for review.

When a reply is scored wrong, add it as a test case and adjust the
pattern lists — see CONTRIBUTING.md.

## References

- `${CLAUDE_PLUGIN_ROOT}/scripts/score_reply.py` — the actual classifier
- The `*_PATTERNS` lists at the top of `score_reply.py` — the lexicon
- [rhythm.md](rhythm.md) — where batch triage runs
- `brand-config.operations.reply_routing` — the routing rules
