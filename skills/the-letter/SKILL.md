---
name: the-letter
description: "Write one cold letter from a public signal. Use when the draft must stay under 90 words and must refuse a demographic email or a missing public signal."
models: ""
---

# The letter

One letter, under 90 words, plus the lint. The letter names a public signal the reader can check. A role title, a funding stage, or an industry is not that signal.

The build guide teaches a human. This pack teaches an agent.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Name the public signal in the reader's own words.
- [ ] 2. Fill the letter shell: public signal, then the letter.
- [ ] 3. Run `python3 scripts/score.py --file draft.json`.

Check again until the script exits 0.

Go back to step 2 if step 3 fails.

## Run

```bash
python3 scripts/score.py --file examples/letter-good.json
python3 scripts/score.py --file examples/letter-demographic.json
```

The good file exits 0 and prints the letter and the lint. The demographic file exits 1. A blank public signal exits 1 with a missing public signal. Broken JSON exits non-zero and does not echo the raw input.

Python 3 standard library only. No network. No send.

## Shell

```json
{
  "public_signal": "Acme posted a Demand Gen Lead role four days ago.",
  "letter": "Acme posted a Demand Gen Lead role four days ago. That post is the only reason for this note. I cut a one-page version of the first email around that role. Want the page?"
}
```

## Pack notes

- [bug report](../../.github/ISSUE_TEMPLATE/bug_report.md)
- [feature request](../../.github/ISSUE_TEMPLATE/feature_request.md)
- [agents](../../AGENTS.md)
- [changelog](../../CHANGELOG.md)
- [contributing](../../CONTRIBUTING.md)
- [soul](../../SOUL.md)
- [deliverability auditor](../../agents/cold-email-deliverability-auditor.md)
- [reviewer](../../agents/cold-email-reviewer.md)
- [banned patterns](../../cold-email/references/banned-patterns.md)
- [binary calls](../../cold-email/references/binary-ctas.md)
- [framework](../../cold-email/references/jmc-framework.md)
- [spam sample](../../examples/spam.email.md)
- [sample letter](../../examples/t1.email.md)
