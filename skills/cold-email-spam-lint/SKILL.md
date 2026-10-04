---
name: cold-email-spam-lint
description: "Deterministic spam-trigger scanner for cold email drafts. Scans subject and body against a 200-word spam-trigger lexicon, checks link and image ratios, ALL CAPS, emoji, clickbait, and fake Re: patterns, and returns a 0-100 risk score with line-by-line flags. Backed by a Python script, no LLM. Use when the operator asks to spam-check a draft, before any send, and on Wednesday's ship-day batch; loaded by the main cold-email skill."
user-invocable: false
allowed-tools: Read Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spam_word_lint.py:*) Grep
license: MIT
models: ""

---

# Cold Email Spam Lint — deterministic spam-trigger scanner

A real scanner, not vibes. Backs onto `scripts/spam_word_lint.py` for
deterministic scoring against a maintained 200-word spam-trigger
lexicon.

## Activation

Loaded by:
- `cold-email-craft` — final self-check before delivering a draft
- `cold-email-weekly-rhythm` — Wednesday ship-day batch lint
- User invocation: "spam-lint this email"

## How it scores

Each draft gets a 0-100 deliverability-risk score across 6 axes:

| Axis | Weight | What it catches |
|---|---|---|
| Spam-trigger words | 25 | "URGENT", "ACT NOW", "Limited time", "free money", "guaranteed" — 200+ patterns |
| ALL CAPS | 15 | Subject or body lines in caps |
| Emoji | 10 | Emoji in subject (high B2B spam signal) |
| Clickbait patterns | 15 | "You won't believe...", "This one trick...", "Doctors hate..." |
| Fake threading | 10 | "Re:" / "Fwd:" in subject when there's no prior thread |
| Link / image ratio | 25 | >1 link or image-to-text >40% — B2B threshold |

Output:

```markdown
# Spam Lint — <subject>

## Deliverability risk score: <0-100>/100

| Axis | Score | Issues |
|---|---|---|
| Spam-trigger words | <0-25>/25 | Found: <words> |
| ALL CAPS | <0-15>/15 | Caps in: <lines> |
| Emoji | <0-10>/10 | Subject has 🚀 |
| Clickbait | <0-15>/15 | "You won't believe..." in line 2 |
| Fake threading | <0-10>/10 | Subject starts with "Re:" |
| Link/image ratio | <0-25>/25 | 3 links found |

## Line-by-line flags

[Line 1 — Subject] "Re: URGENT — pipeline update 🚀"
  - Fake threading: subject begins with "Re:"
  - Spam-trigger: "URGENT"
  - ALL CAPS in subject
  - Emoji in subject

[Line 5 — Body] "You won't believe what we shipped this quarter."
  - Clickbait pattern: "You won't believe"

## Verdict
| Score | Verdict |
|---|---|
| 90-100 | Ship |
| 75-89 | Ship after fixes — flagged items have alternatives below |
| 60-74 | Rewrite — too many deliverability flags |
| <60 | Do not send — will land in spam |
```

## Implementation

The skill shells out to a Python script:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spam_word_lint.py --subject "<subject>" --body "<body>" --format json
```

The script returns structured JSON. The skill formats it into the
table above.

## Script location

`../../scripts/spam_word_lint.py` — relative to this skill's base
directory. From the pack root that is `scripts/spam_word_lint.py`.

Exit code 0 means score ≥75, 1 means below 75, 2 means bad input.

Trigger words match as whole words: "credit" fires on "credit line",
not "accredited". A lone 3-4 letter acronym (SDR, CRM, ARR) is not
"ALL CAPS"; a 5+ letter capitalised word or two capitalised words in a
row is.

The script is zero-dependency Python 3.8+. No external libraries, no
network calls.

## Lexicon source

The 200-word lexicon lives in the script itself — the `*_TRIGGERS`
and `CLICKBAIT_PATTERNS` lists at the top of `spam_word_lint.py`. Edit
it there. Sources:

- Google Postmaster Tools 2024 bulk-sender guidance
- Yahoo + Microsoft 2024 bulk-sender rules
- Litmus / Email on Acid public spam-trigger lists
- JMC's own list from reviewing 1000+ campaigns

The lexicon is versioned with the pack. When Gmail/Yahoo update
guidance, the lexicon updates in a release.

## Why this matters

Vibes-based spam-checking is inconsistent. A deterministic lint
catches every instance of the known triggers, every time. The
script runs in <100ms per email — Wednesday's batch ship-day check
runs through 100 emails in under 10 seconds.

## References

- `../../scripts/spam_word_lint.py` — the actual scanner
- `../cold-email/references/banned-patterns.md` — JMC-specific bans
  (separate from generic spam triggers — these are voice + framework
  bans, not deliverability bans)
