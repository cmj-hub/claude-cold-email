<p align="center">
  <img src="./assets/header.svg" alt="claude-cold-email — signal-anchored cold email for B2B operators" width="100%">
</p>

# claude-cold-email

> Replace an $80K SDR's drafting stack with the JMC framework + ~$130/mo in sending tools — as an agent skill pack.

A JMC cold email is four jobs in under 90 words: a verbatim public signal, the pain that signal implies, a 22-word EVP, and a binary ask. Demographics are not a signal.

The build guide teaches the framework to a human. This pack teaches the same framework to an agent.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/cmj-hub/claude-cold-email?style=social)](https://github.com/cmj-hub/claude-cold-email)
![No paid APIs](https://img.shields.io/badge/paid%20APIs-none-success)
![Install](https://img.shields.io/badge/install-npx%20skills-blue)

<p align="center">
  <img src="./assets/demo.gif" alt="claude-cold-email — terminal demo of the kickoff and lint loop" width="100%">
</p>

Clean T1 (signal + pain + EVP + binary ask) lints clean. `URGENT! ACT NOW 🚀 FREE` is rejected. The spam lexicon is deterministic Python — no LLM, no paid API.

## Install

Two commands. Works in Claude Code, Cursor, Codex, Grok, Copilot, Windsurf, Cline, OpenCode, Antigravity, Goose, Continue, Roo, and the rest of the [skills CLI](https://skills.sh) agent list.

```bash
npx skills add cmj-hub/claude-cold-email --all -g --full-depth
```

```text
/plugin marketplace add cmj-hub/claude-cold-email
/plugin install cold-email
```

The first line is the cross-harness install. The second is Claude Code's plugin (slash commands + reviewer agents).

npm (from GitHub — this pack is not on npmjs.com):

```bash
npm install github:cmj-hub/claude-cold-email
npx jmc-cold-email
```

`npx jmc-cold-email` runs the same installer as `curl` below.

```bash
curl -fsSL https://raw.githubusercontent.com/cmj-hub/claude-cold-email/main/install.sh | bash
```

Windows: `iwr https://raw.githubusercontent.com/cmj-hub/claude-cold-email/main/install.ps1 -useb | iex`

## What you walk out with in 15 minutes

Artifact: `examples/t1.email.md`. Lint the sample T1, then write yours against the same four jobs.

```bash
python3 scripts/spam_word_lint.py \
  --subject "Pipeline gap after the Q3 hire freeze?" \
  --body "Sarah — saw you posted the Demand Gen Lead role four days ago. Pipeline gap is usually upstream of an SDR hire. Worth 15 min Thursday to walk through?"
python3 scripts/score_subject_line.py --subject "Pipeline gap after the Q3 freeze?" --framework pain
```

One loop. One ICP. Example data. Then do yours.

## What this pack will not do

- It will not send the email.
- It will not ingest your CRM or hunt live signals.
- It will not keep a weekly ship cadence for you.
- It will not update when Gmail changes the spam window.

This pack drafts and scores. It will not pick this quarter's PSP, ingest your CRM, or update when Gmail changes the spam window. That is the course + Operator Pass: the catalog that keeps moving, the tools that stay calibrated, the Friday room where you bring the artifact.

## Also in the pack

| Piece | Job |
|---|---|
| `cold-email` orchestrator | Route to write / sequence / audit / lint |
| `scripts/spam_word_lint.py` | 200+ lexicon + clickbait + fake-thread |
| `scripts/score_subject_line.py` | Length, spam, personalization, framework-fit |
| Banned-pattern list | No Hope-you're-well, no Just-bumping-this |
| Craft / audit / nurture / deliverability | After the first T1, if you want them |

Sub-skills stay in the repo. First run is the loop above, not the operating system.

## Does this send the email for me?

No. It drafts and lints. You (or your sequencer) send. Live send, reply write-back, and CRM ingest are Operator Pass + implementation.

## What is a binary CTA?

A yes/no ask. "Worth 15 minutes Thursday?" is binary. "Let me know if you'd like to learn more" is not. One ask per email.

## Will this get me marked as spam?

The linter catches the word list, ALL CAPS, emoji, fake threading, and link pile-ups. It does not warm a domain, set SPF/DKIM/DMARC, or promise inbox. Deliverability sub-skills score DNS; they do not run your infra.

## Suite, course, Operator Pass

- Suite: [https://jaymountconsulting.com/skills](https://jaymountconsulting.com/skills)
- Course: [Cold Email & Outreach Craft](https://jaymountconsulting.com/learn/courses/cold-email-outreach-craft)
- Operator Pass: [https://jaymountconsulting.com/operator-pass](https://jaymountconsulting.com/operator-pass)

Founder: $97/mo billed annually ($1,164/yr), locked for life if bought before October 31, 2026. After that: $197/mo billed annually ($2,364/yr), no lock.

## Companion packs

- **[Pain Signal Profile](https://github.com/cmj-hub/claude-psp)** — `claude-psp`
- **[Early Value Proposition](https://github.com/cmj-hub/claude-evp)** — `claude-evp`
- **[Four-pillar founder brand](https://github.com/cmj-hub/claude-founder-brand)** — `claude-founder-brand`
- **[Pricing surgery](https://github.com/cmj-hub/claude-pricing)** — `claude-pricing`
- **[Breakthrough Advertising (Schwartz)](https://github.com/cmj-hub/claude-breakthrough-advertising)** — `claude-breakthrough-advertising`
- **[Johanson / Stanley tutorial email](https://github.com/cmj-hub/claude-johanson-stanley)** — `claude-johanson-stanley`

## License

MIT. See [LICENSE](./LICENSE).

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com). Public build: [https://jaymountconsulting.com/build](https://jaymountconsulting.com/build). Skill suite: [https://jaymountconsulting.com/skills](https://jaymountconsulting.com/skills).
