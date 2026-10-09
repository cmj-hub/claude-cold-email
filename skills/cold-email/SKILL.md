---
name: cold-email
description: "Signal-anchored B2B cold email: first touch under 90 words with a binary ask, follow-ups, subject lines, spam lint, domain deliverability, send-list hygiene, reply triage, and outbound audits. Use when the user asks for a cold email, follow-up sequence, deliverability or spam check, reply scoring, or send-list cleanup. Not for give-first offers (sales-offer), picking who to contact (prospect-list), or post-opt-in email (email-sequence)."
argument-hint: "[write | sequence | subject | lint | deliverability | list | reply | nurture | audit | rhythm | status | setup]"
allowed-tools: Read Write Grep Glob WebFetch Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score_letter.py:*) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/spam_word_lint.py:*) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score_subject_line.py:*) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check_deliverability.py:*) Bash(bash ${CLAUDE_PLUGIN_ROOT}/scripts/dig_dns.sh:*) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score_list.py:*) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score_reply.py:*) Bash(dig:*) Bash(host:*) Bash(nslookup:*)
license: MIT
models: ""
---


# Cold Email — JMC Outreach Craft Skill

Comprehensive cold email orchestrator for B2B operators. Anchors every
output on a Pain Signal Profile (not demographics) and forces the output
into a shape you can ship.

## Preflight (every invocation)

> **Scoring something pasted needs no setup.** If the operator handed you a line, post, draft, or file to score, run the scorer on it first and report the result; missing config only means some checks are skipped, so say which. Offer setup afterwards as the next step. Check whether files exist with Read or Glob, not a shell command.

Run this before routing anywhere. It is what `AGENTS.md` rules 1 and 2
require.

1. Look for `brand-config.json` and `SOUL.md` in the operator's project
   root. Read both if present.
2. If either is missing and the operator did not pass `--no-config`,
   run the setup mode ([modes/setup.md](modes/setup.md)) before drafting
   real outreach. If `operator` or `icp` is missing, say "Run `/gtm:setup`
   once for the whole suite" first. Offer once; if they decline, say the
   output will be framework-shaped but generic.
3. If `brand-config.json` exists, sanity-check the fields the requested
   job needs (e.g. `evp.primary` for drafting, `infrastructure.sending_domain`
   for deliverability). Ask for anything missing. Never fill it in.
   If the `psp` or `evp` block is missing, say which pack produces it
   (`/plugin install psp@gtm-operator-skills`, `/plugin install evp@gtm-operator-skills`)
   instead of inventing a signal, pain, or EVP.
4. Treat SOUL.md as voice only. It can change word choice; it cannot
   lift the word limit, soften the binary CTA, or un-ban a pattern.

## Modes — route by $ARGUMENTS

Run the preflight above first, every time. Then pick one mode:

- If `$ARGUMENTS` starts with a mode name below, go straight to that mode
  (the rest of `$ARGUMENTS` is its input).
- If `$ARGUMENTS` is empty, run `status`: it reads the project and names
  the one next step.
- Otherwise match the user's words to the table. If intent is still
  ambiguous, ask one clarifying question — never two.

Read the mode file with the Read tool and follow it.

| You say / argument | Mode file |
|---|---|
| (nothing), `status`, "where do I start", "what's next" | [modes/status.md](modes/status.md) |
| `setup`, "set up my brand config", "configure my voice" | [modes/setup.md](modes/setup.md) |
| `write`, "write a cold email to...", "rewrite this cold email" | [modes/craft.md](modes/craft.md) |
| `sequence`, "build a follow-up sequence", "Day 3 / 7 / 14" | [modes/craft.md](modes/craft.md) (sequence mode) |
| `subject`, "subject lines for...", "critique this subject" | [modes/subject.md](modes/subject.md) |
| `lint`, "spam-check this", "will this land in spam" | [modes/lint.md](modes/lint.md) |
| `deliverability`, "is my domain ready", SPF / DKIM / DMARC | [modes/deliverability.md](modes/deliverability.md) |
| `list`, "score / clean my send list", "dedup this CSV" | [modes/list.md](modes/list.md) |
| `reply`, "score this reply", "triage my replies" | [modes/reply.md](modes/reply.md) |
| `nurture`, "re-engage cold or stalled prospects" (not opted in) | [modes/nurture.md](modes/nurture.md) |
| `audit`, "audit my outbound program" | [modes/audit.md](modes/audit.md) |
| `rhythm`, "this week's queue", "Friday review" | [modes/rhythm.md](modes/rhythm.md) |
| "Review / score this draft" | `cold-email-reviewer` agent |

Files the modes write in the operator's project go under `gtm/` at the
project root (create it if missing): `gtm/letter.json` (the draft:
`public_signal`, `subject`, `letter`), `gtm/send-list.csv` (the send
list; `--write` adds `.cleaned.csv` and `.removed.csv` beside it), and
`gtm/replies.jsonl` (one reply per line). `brand-config.json` and
`SOUL.md` stay at the project root.

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
7. **Found is not sendable until verify = deliverable.** A scraped or
   enriched address stays off the send list until verification returns
   deliverable. Catch-all, unknown, and invalid are not "valid."

## Variables (every mode uses these)

The core framework operates on seven variables. Capture them once,
reuse across every mode:

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

Write the draft to `gtm/letter.json`, then:

- `score_letter.py --file gtm/letter.json`: exit 0 (signal quoted, no
  demographics, under 90 words, one yes/no ask)
- `spam_word_lint.py --file gtm/letter.json`: score 75 or higher
- `score_subject_line.py --file gtm/letter.json`: score 70 or higher

On exit 1 each reason reads `- what is wrong → what to change`. Apply
every change and run it again; do not show a draft that fails.

**Flag, don't hide** — if the signal, pain, EVP, or vocabulary was a
guess, say which line is uncertain and what data would settle it
(`AGENTS.md` rule 10).

## Running the bundled scripts

The scripts live in `scripts/` at the plugin root. Call them as
`${CLAUDE_PLUGIN_ROOT}/scripts/<name>.py`, which resolves to the
installed plugin from any project directory. Outside Claude Code,
`python3 scripts/<name>.py` from the repo root is the same script. All
are Python 3.8+ stdlib only; DNS checks need `dig`.

Every scorer takes `--file PATH` or `--stdin`, prints text by default and
one JSON object with `--json`, and exits 0 pass, 1 refused (each reason
with its fix, then `Next: fix the lines above and run this again.`), 2
bad input. On a pass the last line names the next step.

| Script | Mode |
|---|---|
| `score_letter.py` | craft, self-check (before the spam lint) |
| `spam_word_lint.py` | lint, self-check |
| `score_subject_line.py` | subject, self-check |
| `score_reply.py` | reply |
| `score_list.py` | list |
| `check_deliverability.py`, `dig_dns.sh` | deliverability |

## Works with the suite

This is step 4 of the GTM operator suite (`/plugin marketplace add cmj-hub/gtm-operator-skills`).

- **Reads:** `psp`, `evp`, `icp`, `tone`, `infrastructure`, `operations` from `brand-config.json` if present.
- **Writes:** `tone`, `infrastructure`, `operations`. Merge at the field level; never overwrite another pack's keys.
- **Before this:** psp (`/psp:psp`) and evp (`/evp:evp`), when there is no `psp` or `evp` block; prospect-list (`/prospect-list:who-to-contact`), when you do not yet know who to contact.
- **Instead of this:** sales-offer (`/sales-offer:cold-offer`), when the first touch should hand over a leak and a prototype rather than ask.
- **After this:** email-sequence (`/email-sequence:lifecycle-email`), when a prospect replies and opts in. End a successful run with that `Next:` line.

If a companion pack is not installed, name it and its install line (`/plugin install <name>@gtm-operator-skills`); do not do its job inline.

## References

Load these on demand for deeper context:

- [references/jmc-framework.md](references/jmc-framework.md) — The full JMC cold email framework
- [references/banned-patterns.md](references/banned-patterns.md) — Lines / openers / closes that fail
- [references/binary-ctas.md](references/binary-ctas.md) — 30 binary CTA patterns
- [references/psp-anchors.md](references/psp-anchors.md) — How to derive signal → pain → EVP
- [references/bulk-sender-rules.md](references/bulk-sender-rules.md) — Google / Yahoo / Microsoft sender requirements
- [references/audit-rubric.md](references/audit-rubric.md) — The 30-point outbound audit rubric
- [SOUL.md](../../SOUL.md) — Operator voice template (the shape the setup mode fills in)
- [examples/t1.email.md](../../examples/t1.email.md) — A first touch that passes every check (lints at 100)
- [examples/spam.email.md](../../examples/spam.email.md) — A draft the spam lint rejects

## Specialist agents

- [`cold-email-reviewer`](../../agents/cold-email-reviewer.md) — Quality scorer (0-100) against framework
- [`cold-email-deliverability-auditor`](../../agents/cold-email-deliverability-auditor.md) — DNS/reputation specialist

## Free hosted version

The same job runs in a browser, no install and no key:
[Cold Email Linter](https://jaymountconsulting.com/tools/cold-email-linter)
