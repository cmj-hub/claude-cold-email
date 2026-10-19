# Craft — write one cold email or the full sequence

Drafts a signal-anchored first touch under 90 words, or T1 plus the Day 3 / 7 / 14 follow-ups. Modes `write` and `sequence` both run this file.

## Contents

- Activation
- Workflow
- 3-touch sequence mode
- Output format
- Reference

## Activation

The main skill routes here when the user says any of:

- "Write a cold email to..."
- "Draft an outreach to..."
- "Build a 3-touch sequence for..."
- "Follow-up to <name> at <company>"
- "Rewrite this cold email"

## Workflow

### 1. Gather the six framework variables

Required:

| Variable | Source | Ask if missing |
|---|---|---|
| `firstName` | User-provided | "What's the recipient's first name?" |
| `role` | User-provided or LinkedIn | "What's their role?" |
| `company` | User-provided | "Which company?" |
| `signal` | Public, recent, verifiable | "What did they just do publicly? (Job post, funding, launch, hire, content)" |
| `pain` | What the signal implies operationally | "What does that signal imply about their pipeline / motion / stack?" |
| `evp` | One-line value prop | "What's your one-line EVP for this segment? (≤22 words)" |
| `senderName` | User | "Who are you signing as?" |

**Do not fabricate.** If any are missing, ask. Never assume role,
company, or signal — wrong assumptions kill cold email.

### 2. Validate the framework

Before generating, validate:

- **Signal** is something they DID, not who they ARE. If user provides
  "VP of Marketing at Series B SaaS", push back: "That's a demographic,
  not a signal. What did they post/announce/ship in the last 30 days?"
- **Pain** uses their language, not yours. No "synergy" / "optimize" /
  "leverage".
- **EVP** is ≤22 words, has one specific outcome, one tradeoff.
  Use only an outcome and a tradeoff the operator gave (or `evp.outcome` / `evp.tradeoff`). If none was given, drop the tradeoff clause; do not add a note about it. Never write one in to fill the shape.

### 3. Generate

Use the canonical template (the full prompt is in
`../references/jmc-framework.md`):

```
Subject: <from the subject mode>

{firstName},

<The signal, in the source's own words, 1 sentence.>

<Pain in their language, 1 sentence.>

<EVP, ≤22 words. One proof line only if the operator gave one.>

<One yes/no question.>

{senderName}
```

Rules the template does not show:

- **Quote marks mean quoted.** Put words in quotation marks only when
  the source shows them as the prospect's exact words. Otherwise name
  where it came from and use its words without quote marks ("Your AP
  Specialist posting says the team processes roughly 400 invoices a
  week by hand").
- **The ask.** Default to an interest question tied to the pain
  ("Worth a look?", "Is the 12-day close on your list this
  quarter?"). Ask for a meeting with a day or time only when the
  operator gave availability; never invent one. Never offer a sample,
  write-up or case study the operator has not said exists.
- **Missing sender.** Sign `[Your name]` and move on. Do not add notes
  explaining what was missing; add one line only if you refused or
  changed the task.
- **No em dashes** in the greeting, sign-off or body.

### 4. Self-check against constraints

After generating, verify:

- [ ] Total word count <90
- [ ] No banned openers ("Hope you're well", "Just wanted to")
- [ ] No banned closes ("Let me know your thoughts", "Happy to chat")
- [ ] Binary CTA (yes/no answerable), with no invented day or time
- [ ] Signal is named in the source's words; quote marks only around
      words the source really contains
- [ ] No congratulation or compliment opener
- [ ] Pain uses recipient's language
- [ ] EVP ≤22 words
- [ ] Subject ≤7 words, no clickbait

If any check fails, regenerate that block before showing the user.

When Bash is available, also run the deterministic gates from the
main skill's self-check rubric, in this order. First the letter gate:
write `gtm/letter.json` (create `gtm/` if missing) with
`public_signal` (the signal as the operator gave it), `subject`, and
`letter` (the body), then run `score_letter.py`. It
refuses, listing every reason, when the signal is missing, no 3-word
run of it is quoted verbatim, the letter leans on demographics
("VPs of Marketing at Series B companies", "companies like yours",
"hope you're well"), the body is 90 words or more, or the ask is not
one yes/no question. Each refusal line reads `- what is wrong → what
to change`; apply every change, then lint the same file:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score_letter.py --file gtm/letter.json             # need exit 0
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spam_word_lint.py --file gtm/letter.json --json    # need score ≥75
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score_subject_line.py --file gtm/letter.json --json # need score ≥70
```

Before drafting, check the draft against `brand-config.tone.banned_phrases`
and the SOUL.md "never" list, not just the framework bans.

### 5. Offer the "rewrite the weakest line" pass

After delivering the draft, offer:

> "Want me to identify the single weakest line and rewrite it? (1
> sentence + rationale, no full rewrite.)"

This is the canonical ship-or-cut decision aid.

## 3-touch sequence mode

When the user asks for a sequence, generate all four touches at once:

| Day | Touch | Length | Shape |
|---|---|---|---|
| 0 | T1 | <90 words | Full signal-anchored opener (above) |
| 3 | T2 | <70 words | A second signal or a 1-line case study the operator gave, + binary close |
| 7 | T3 | <70 words | Different angle on same PSP (cost / risk / opportunity-cost) |
| 14 | T4 | <60 words | Binary close: continue or close the loop |

Each touch references the same signal but reframes the pain. If the
operator gave a second signal (a post, a contract win), the follow-up
opens on it plainly, not with "Congratulations on". Each touch asks a
different yes/no question; never repeat the T1 ask. No "following up
on my last email" anywhere. If the user asks for a follow-up on a
different day than the table, use their day.

## Output format

Default: plain text with clearly labeled subject + body.

If user requests JSON: `{ subject, preheader, body, touchNumber,
wordCount, framework: { signal, pain, evp, ask } }`.

End with one line: `Next: /cold-email:cold-email deliverability` if the
sending domain has not been checked in 30 days, otherwise "Next: send
it from your own tool, then score replies with `/cold-email:cold-email reply`."

## Reference

- [../references/jmc-framework.md](../references/jmc-framework.md) — full framework
- [../references/banned-patterns.md](../references/banned-patterns.md) — what NOT to write
- [../references/binary-ctas.md](../references/binary-ctas.md) — 30 binary CTA patterns
