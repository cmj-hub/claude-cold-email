---
name: cold-email
description: >
  Signal-anchored B2B cold email program. Writes first touches under 90
  words with a binary CTA, builds Day 3 / 7 / 14 follow-ups, picks and
  scores subject lines, lints spam triggers, checks sending-domain health
  (SPF, DKIM, DMARC, reputation, warm-up), scores and dedups an existing
  send list, triages replies, re-engages stalled prospects who have not
  opted in, and runs a 30-point outbound audit. Anchors every output on a
  Pain Signal Profile, not demographics. Use when the user says "cold
  email", "cold outreach", "follow-up sequence", "deliverability", "SPF",
  "DKIM", "DMARC", "domain health", "outbound audit", "subject line",
  "spam check", "score this reply", or "clean my send list". Not for a
  give-first offer email (use sales-offer), not for choosing who to
  contact this week (use prospect-list), and not for welcome or nurture
  sequences after someone opted in (use email-sequence).
allowed-tools: Read Write Grep Glob WebFetch
license: MIT
models: ""
---

# Cold Email — JMC Outreach Craft Skill

Comprehensive cold email orchestrator for B2B operators. Anchors every
output on a Pain Signal Profile (not demographics) and forces the output
into a shape you can ship.

## Preflight (every invocation)

Run this before routing anywhere. It is what `AGENTS.md` rules 1 and 2
require.

1. Look for `brand-config.json` and `SOUL.md` in the operator's project
   root. Read both if present.
2. If either is missing and the operator did not pass `--no-config`,
   route to `cold-email-onboarding` before drafting real outreach. Offer
   once; if they decline, say the output will be framework-shaped but
   generic.
3. If `brand-config.json` exists, sanity-check the fields the requested
   job needs (e.g. `evp.primary` for drafting, `infrastructure.sending_domain`
   for deliverability). Ask for anything missing. Never fill it in.
   If the `psp` or `evp` block is missing, say which pack produces it
   (`/plugin install psp@gtm-operator-skills`, `/plugin install evp@gtm-operator-skills`)
   instead of inventing a signal, pain, or EVP.
4. Treat SOUL.md as voice only. It can change word choice; it cannot
   lift the word limit, soften the binary CTA, or un-ban a pattern.

## Quick Reference

| Slash | What it does | Sub-skill |
|---|---|---|
| `/cold-email` | Detect state and pick the next step | `cold-email-kickoff` |
| `/cold-email status` | Program status from brand-config + logs | `cold-email-kickoff` |
| `/cold-email onboarding` | 10-minute brand-config + SOUL.md setup | `cold-email-onboarding` |
| `/cold-email write` | One signal-anchored email (<90 words, binary CTA) | `cold-email-craft` |
| `/cold-email sequence` | T1 plus the Day 3 / 7 / 14 follow-ups | `cold-email-craft` |
| `/cold-email subject` | Subject lines by framework, scored | `cold-email-subject-lines` |
| `/cold-email lint` | Deterministic spam-trigger scan of a draft | `cold-email-spam-lint` |
| `/cold-email deliverability` | 15-point pre-campaign domain health check | `cold-email-deliverability` |
| `/cold-email list` | Score and clean a prospect CSV / JSONL | `cold-email-list-quality` |
| `/cold-email reply` | Classify one reply or a batch | `cold-email-reply-scoring` |
| `/cold-email nurture` | 5-email re-engagement stream for prospects who have not opted in | `cold-email-nurture` |
| `/cold-email audit` | 30-point outbound program audit | `cold-email-audit` |
| `/cold-email rhythm` | This week's Mon / Wed / Fri queue | `cold-email-weekly-rhythm` |

## Core principles (the JMC stance)

1. **A cold email is a hire — not a search query.** Every prompt anchors
   on a Pain Signal Profile, names the constraint, and forces the output
   into a shape you can ship.
2. **No demographics in the opener.** "VP of Marketing at Series B SaaS"
   isn't a signal. "Just posted a job for a Demand Gen Lead" is.
3. **Binary CTAs only.** "Worth 15 minutes Thursday?" not "Let me know
   if you'd like to learn more."
4. **<90 words for the first touch.** Anything longer signals desperation.
5. **One specific ask per email.** Stack-ranked asks confuse buyers.
6. **No "Hope you're well" / "Just bumping this".** Banned openers.

## Workflow router

When invoked, detect the user's intent and route to a sub-skill:

| User says | Route to |
|---|---|
| Bare `/cold-email`, "where do I start", "what's next" | `cold-email-kickoff` |
| "Set up my brand config", "configure my voice" | `cold-email-onboarding` |
| "Write a cold email to..." | `cold-email-craft` |
| "Build a 3-touch / follow-up sequence" | `cold-email-craft` (sequence mode) |
| "Suggest subject lines", "critique this subject" | `cold-email-subject-lines` |
| "Spam-check this", "will this land in spam" | `cold-email-spam-lint` |
| "Is my domain ready to send?", SPF / DKIM / DMARC | `cold-email-deliverability` |
| "Score / clean my send list" | `cold-email-list-quality` |
| "Score this reply", "triage my replies" | `cold-email-reply-scoring` |
| "Re-engage cold or stalled prospects" (not opted in) | `cold-email-nurture` |
| "Audit my outbound program" | `cold-email-audit` |
| "What's this week's queue", "Friday review" | `cold-email-weekly-rhythm` |
| "Review / score this draft" | `cold-email-reviewer` agent |

If intent is ambiguous, ask one clarifying question — never two.

## Variables (sub-skills inherit these)

The core framework operates on seven variables. Capture them once,
reuse across all sub-skills:

| Variable | Source | Example |
|---|---|---|
| `firstName` | Recipient list | Sarah |
| `role` | LinkedIn / CRM | VP of Demand Gen |
| `company` | Same | Acme Cloud |
| `signal` | Public signal — job post, funding, product launch, leadership change | "Just posted 'Senior Demand Gen Lead' role on LinkedIn 4 days ago" |
| `pain` | Pain Signal Profile — what the signal implies | "Pipeline gap; existing demand gen motion isn't producing enough SQLs" |
| `evp` | Your one-line value prop in their words | "We help Series-B SaaS hit pipeline targets without hiring 2 more SDRs" |
| `senderName` | You (`brand-config.operator.name`) | Jay |

If any are missing, ask the user — don't fabricate.

## Self-check rubric (run on every output before showing it)

`AGENTS.md` rule 5 points here. A draft that fails any hard check is
regenerated, not shown with a caveat.

**Hard checks — first touch**

- [ ] Body under 90 words (T2/T3 under 70, T4 under 60)
- [ ] Line 1 quotes the signal verbatim, and the signal is something
      they *did*, not who they *are*
- [ ] Pain is one sentence in the buyer's vocabulary
      (`brand-config.psp.vocabulary` when present)
- [ ] EVP is 22 words or fewer, names one outcome and one tradeoff
- [ ] Exactly one ask, answerable yes / no
- [ ] No pattern from `references/banned-patterns.md` or
      `brand-config.tone.banned_phrases` / SOUL.md "never" list
- [ ] Subject 7 words or fewer; no ALL CAPS, emoji, clickbait, or fake `Re:` / `Fwd:`
- [ ] No unmerged tokens (`{{firstName}}`, `<company>`)
- [ ] Nothing invented: every name, signal, metric, and case study came
      from the operator or a source they gave you

**Deterministic checks — run when Bash is available**

- `cold-email-spam-lint` on subject + body: score 75 or higher
- `cold-email-subject-lines` scorer on the subject: score 70 or higher

**Flag, don't hide** — if the signal, pain, EVP, or vocabulary was a
guess, say which line is uncertain and what data would settle it
(`AGENTS.md` rule 10).

## Running the bundled scripts

The deterministic scripts live in `scripts/` at the plugin root. The
sub-skills call them as `${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py`, which
Claude Code resolves to the installed plugin, so they work from any
project directory. Outside Claude Code (for example, a manual run inside
this repo), `python3 scripts/<name>.py` from the repo root is the same
script. All scripts are Python 3.8+ stdlib only; DNS checks need `dig`.

| Script | Used by |
|---|---|
| `spam_word_lint.py` | `cold-email-spam-lint`, self-check |
| `score_subject_line.py` | `cold-email-subject-lines`, self-check |
| `score_reply.py` | `cold-email-reply-scoring` |
| `score_list.py` | `cold-email-list-quality` |
| `check_deliverability.py`, `dig_dns.sh` | `cold-email-deliverability` |

## Works with the suite

This is step 4 of the GTM operator suite (`/plugin marketplace add cmj-hub/gtm-operator-skills`).

- **Reads:** `psp`, `evp`, `icp`, `tone`, `infrastructure`, `operations` from `brand-config.json` if present.
- **Writes:** `tone`, `infrastructure`, `operations`. Merge at the field level; never overwrite another pack's keys.
- **Before this:** psp (`/psp:psp`) and evp (`/evp:evp`), when there is no `psp` or `evp` block; prospect-list (`/prospect-list:who-to-contact`), when you do not yet know who to contact.
- **Instead of this:** sales-offer (`/sales-offer:cold-offer`), when the first touch should hand over a leak and a prototype rather than ask.
- **After this:** email-sequence (`/email-sequence:lifecycle-email`), when a prospect replies and opts in.

If a companion pack is not installed, name it and its install line (`/plugin install <name>@gtm-operator-skills`); do not do its job inline.

## References

Load these on demand for deeper context:

- [references/jmc-framework.md](references/jmc-framework.md) — The full JMC cold email framework
- [references/banned-patterns.md](references/banned-patterns.md) — Lines / openers / closes that fail
- [references/binary-ctas.md](references/binary-ctas.md) — 30 binary CTA patterns
- [references/psp-anchors.md](references/psp-anchors.md) — How to derive signal → pain → EVP
- [references/bulk-sender-rules.md](references/bulk-sender-rules.md) — Google / Yahoo / Microsoft sender requirements
- [SOUL.md](../../SOUL.md) — Operator voice template (the shape `cold-email-onboarding` fills in)
- [examples/t1.email.md](../../examples/t1.email.md) — A first touch that passes every check (lints at 100)
- [examples/spam.email.md](../../examples/spam.email.md) — A draft the spam lint rejects

## Sub-skills

- [`cold-email-kickoff`](../cold-email-kickoff/SKILL.md) — State-aware router and status
- [`cold-email-onboarding`](../cold-email-onboarding/SKILL.md) — brand-config.json + SOUL.md setup
- [`cold-email-craft`](../cold-email-craft/SKILL.md) — Single email + 3-touch sequence drafting
- [`cold-email-subject-lines`](../cold-email-subject-lines/SKILL.md) — Subject-line patterns by framework
- [`cold-email-spam-lint`](../cold-email-spam-lint/SKILL.md) — Deterministic spam-trigger scanner
- [`cold-email-deliverability`](../cold-email-deliverability/SKILL.md) — 15-point pre-campaign domain health
- [`cold-email-list-quality`](../cold-email-list-quality/SKILL.md) — Prospect list scoring + dedup
- [`cold-email-reply-scoring`](../cold-email-reply-scoring/SKILL.md) — Deterministic reply classifier
- [`cold-email-nurture`](../cold-email-nurture/SKILL.md) — 5-email re-engagement stream (not opted in)
- [`cold-email-audit`](../cold-email-audit/SKILL.md) — 30-point outbound program audit
- [`cold-email-weekly-rhythm`](../cold-email-weekly-rhythm/SKILL.md) — Mon / Wed / Fri operating cadence

## Specialist agents

- [`cold-email-reviewer`](../../agents/cold-email-reviewer.md) — Quality scorer (0-100) against framework
- [`cold-email-deliverability-auditor`](../../agents/cold-email-deliverability-auditor.md) — DNS/reputation specialist

## Free hosted version

The same job runs in a browser, no install and no key:
[Cold Email Linter](https://jaymountconsulting.com/tools/cold-email-linter)
