<p align="center">
  <img src="./assets/header.svg" alt="claude-cold-email — signal-anchored cold email for B2B operators" width="100%">
</p>

# claude-cold-email

> Four jobs. Under 90 words. A job post is a signal. A job title is not.

A JMC cold email is four jobs in under 90 words: a verbatim public signal, the pain that signal implies, a 22-word EVP, and a binary ask. Demographics are not a signal.

"VP of Marketing at Series B SaaS" is a costume.
"Posted Demand Gen Lead four days ago" is something they did.

The sample T1 in this repo lints at **100**.
`URGENT! ACT NOW 🚀 FREE` is rejected.

The lexicon is Python. No LLM. No paid API.

The build guide teaches the framework to a human. This pack teaches the same framework to an agent.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/cmj-hub/claude-cold-email?style=social)](https://github.com/cmj-hub/claude-cold-email)
![No paid APIs](https://img.shields.io/badge/paid%20APIs-none-success)
![Install](https://img.shields.io/badge/install-npx%20skills-blue)

<p align="center">
  <img src="./assets/demo.gif" alt="claude-cold-email — terminal demo of the kickoff and lint loop" width="100%">
</p>

## Install

Two commands. Claude Code, Cursor, Codex, Grok, Copilot, Windsurf, Cline, OpenCode, and the rest of the [skills CLI](https://skills.sh) list.

```bash
npx skills add cmj-hub/claude-cold-email --all -g --full-depth
```

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install cold-email
```

Also: `npm install github:cmj-hub/claude-cold-email` then `npx jmc-cold-email`. Or `curl -fsSL https://raw.githubusercontent.com/cmj-hub/claude-cold-email/main/install.sh | bash`.

## What you walk out with in 15 minutes

Artifact: `examples/t1.email.md`.

```bash
python3 scripts/spam_word_lint.py \
  --subject "Pipeline gap after the Q3 hire freeze?" \
  --body "Sarah — saw you posted the Demand Gen Lead role four days ago. Pipeline gap is usually upstream of an SDR hire. Worth 15 min Thursday to walk through?"
python3 scripts/score_subject_line.py --subject "Pipeline gap after the Q3 freeze?" --framework pain
```

One T1. Lint it. Then write yours against the same four jobs.

## What this pack will not do

It will not send the email.
It will not ingest your CRM.
It will not warm a domain.

This pack drafts and scores. It will not pick this quarter's PSP, ingest your CRM, or update when Gmail changes the spam window. That is the course + Operator Pass: the catalog that keeps moving, the tools that stay calibrated, the Friday room where you bring the artifact.

## Does this send the email for me?

No. It drafts and lints. You send. Live send and reply write-back are Operator Pass + implementation.

## What is a binary CTA?

A yes/no ask.
"Worth 15 minutes Thursday?" is binary.
"Let me know if you'd like to learn more" is not.
One ask per email.

## Will this get me marked as spam?

The linter catches the word list, ALL CAPS, emoji, fake threading, and link pile-ups.
It does not promise inbox.
DNS scoring is in the pack. Running your infra is not.

## Suite, course, Operator Pass

- Suite: [gtm-operator-skills](https://github.com/cmj-hub/gtm-operator-skills) · [jaymountconsulting.com/skills](https://jaymountconsulting.com/skills)
- Course: [Cold Email & Outreach Craft](https://jaymountconsulting.com/learn/courses/cold-email-outreach-craft)
- Operator Pass: [jaymountconsulting.com/operator-pass](https://jaymountconsulting.com/operator-pass)

Founder: $97/mo billed annually ($1,164/yr), locked for life if bought before October 31, 2026. After that: $197/mo billed annually ($2,364/yr), no lock.

## Companion packs

- [claude-psp](https://github.com/cmj-hub/claude-psp) — five-part buying brief
- [claude-evp](https://github.com/cmj-hub/claude-evp) — 22-word line per Schwartz tier
- [claude-founder-brand](https://github.com/cmj-hub/claude-founder-brand) — Pillar / Proof / Process / Person
- [claude-pricing](https://github.com/cmj-hub/claude-pricing) — three-tier contrast + pocket-price leaks

## License

MIT. See [LICENSE](./LICENSE).

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
