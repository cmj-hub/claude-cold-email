<p align="center">
  <img src="./assets/lockup.png" width="880" alt="Cold email skill for Claude Code. A cold email is a short note to someone who has not asked to hear from you, anchored to a public signal.">
</p>

# Cold email skill for Claude Code

A cold email is a short note to someone who has not asked to hear from you, anchored to a public signal.

## In 60 seconds

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install cold-email@gtm-operator-skills
/cold-email:cold-email
```

Or score the sample without an agent:

```bash
python3 scripts/score_letter.py --file examples/letter-good.json          # exit 0, prints the letter, "lint: 34 words", and the next step
python3 scripts/score_letter.py --file examples/letter-demographic.json   # exit 1: - signal not quoted: no 3-word run of public_signal appears in the letter → quote at least 3 words of the signal verbatim in the first line
```

Part of the GTM operator suite — `/plugin install gtm@gtm-operator-skills` installs all ten.

Add the [gtm-operator mod](https://github.com/cmj-hub/gtm-operator-claude-mod) to see the suite's next step above your prompt and keep `brand-config.json` from being overwritten: `/plugin install gtm-operator@gtm-operator-skills`.

One command, many modes: `/cold-email:cold-email [write | sequence | subject | lint | deliverability | list | reply | nurture | audit | rhythm | status | setup]`. With no argument it reads your project and names the next step. Moved in 0.7: the old sub-skills (`cold-email-craft`, `cold-email-spam-lint`, ...) are now modes of this one skill, so type `/cold-email:cold-email lint` instead of naming a sub-skill. Drafts and lists live in `gtm/` at your project root (`gtm/letter.json`, `gtm/send-list.csv`, `gtm/replies.jsonl`).

> "VP of Marketing at Series B" is not a reason to write. A job post four days ago is.

A cold email is four jobs in under 90 words: a verbatim public signal, the pain that signal implies, a 22-word EVP, and a binary ask. Demographics are not a signal.

You have seen the other kind. Hope you're well. Just bumping this. Let me know if you'd like to learn more. That email is a search query wearing a name. This pack will not write it.

The mechanism is Signal → Pain → EVP → Ask. Every line has to do one of those four jobs. If it does not, it gets cut. The linter is Python, not a vibe: spam lexicon, ALL CAPS, emoji, fake threading, link pile-ups.

The sample T1 in `examples/t1.email.md` lints at **100**. `URGENT! ACT NOW 🚀 FREE` is rejected. No LLM. No paid API.

The build guide teaches a human. The pack teaches an agent.

<p align="center">
  <img src="./assets/demo.gif" alt="Cold email skill — sample T1 scores 100" width="100%">
</p>

## What this replaces

The drafting stack an $80K SDR owns on a slow week — not the send, not the domain warm, not the close. Framework plus ~$130/mo in sending tools is the rest of the motion you already have.

## Install

```text
npx skills add cmj-hub/claude-cold-email --all -g --full-depth
```

`--all` writes this pack for every host the installer knows. One host:

```text
npx skills add cmj-hub/claude-cold-email --skill '*' -g --full-depth -y -a claude-code
```

Swap `claude-code` for `cursor`, `codex`, `grok`, `github-copilot`, `windsurf`, `cline`, or `opencode`. For Claude Code, use the two lines under "In 60 seconds".

## What you walk out with in 15 minutes

Artifact: `examples/t1.email.md`.

```bash
python3 scripts/spam_word_lint.py --file examples/t1.email.md                      # exit 0: Score: 100/100 — Ship
python3 scripts/spam_word_lint.py --file examples/spam.email.md                    # exit 1: every flag with its fix
python3 scripts/score_subject_line.py --file examples/t1.email.md --framework pain # exit 0: 100/100
python3 scripts/score_letter.py --file examples/letter-good.json        # exit 0: signal quoted, one yes/no ask
python3 scripts/score_letter.py --file examples/letter-demographic.json # exit 1: refused, every reason listed
```

One T1. Lint it. Then write yours against the same four jobs.

## What this pack will not do

It will not send the email. It will not ingest your CRM. It will not warm a domain.

This pack drafts and scores. It will not pick this quarter's PSP, ingest your CRM, or update when Gmail changes the spam window. Those are judgement calls and live data. This pack gives you the instrument and the rubric; you bring the account.

## Does this send the email for me?

No. It drafts and lints. You send — or your sequencer does. Live send, reply write-back, and CRM ingest are out of scope for a skill pack.

## What is a binary CTA?

A yes/no ask. "Worth 15 minutes Thursday?" is binary. "Let me know if you'd like to learn more" is not. One ask per email. Stacked asks confuse the person who has to answer at 11am.

## Will this get me marked as spam?

The linter catches the word list, ALL CAPS, emoji, fake threading, and link pile-ups. It does not promise inbox. It does not set SPF, DKIM, or DMARC. DNS scoring is in the pack. Running your infra is not.

## On the site

- [Cold Email pack](https://jaymountconsulting.com/skills/claude-cold-email) — this pack's page
- [Skill packs catalog](https://jaymountconsulting.com/skills) — install paths + every pack
- [Course twin](https://jaymountconsulting.com/learn/courses/cold-email-outreach-craft) — human build guide for this pack

## Free, no signup

- **[Cold Email Linter](https://jaymountconsulting.com/tools/cold-email-linter)** — the same job as this pack, hosted. No account, no key.
- [Cold Email & Outreach Craft framework](https://jaymountconsulting.com/frameworks/cold-email-outreach-craft)
- [Prompt Library](https://jaymountconsulting.com/resources/prompt-library)

## Free, by email

[**Growth Audit**](https://jaymountconsulting.com/growth-audit) — where your go-to-market stack is leaking, sent to your inbox.

That one does ask for an email, and it enrols you in a short follow-up on the same topic. Unsubscribe whenever.

[**The Friday Signal**](https://jaymountconsulting.com/newsletter/signal) — one free edition a week on building GTM systems that compound. No pitch in it.


## Next

Previous: [LinkedIn posts](https://github.com/cmj-hub/claude-founder-brand)

Next: [Email sequence](https://github.com/cmj-hub/claude-email-sequence)

## Privacy and security

The scripts are stdlib Python and run locally on the drafts and lists you pass them. The only network traffic is DNS: `check_deliverability.py` and `dig_dns.sh` run `dig` against the sending domain you name and its mail host, plus the Spamhaus DBL and SURBL blacklist zones. The skill and one agent may use WebFetch to open a public page you point them at. No telemetry, no credentials, and nothing is sent: you send. See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](./LICENSE).

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
