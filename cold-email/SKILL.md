---
description: "Use when this skill runs."
models: ""
name: cold-email
description: >
  Cold email & outreach craft for B2B teams. Write signal-anchored openers
  (90-word constraint, binary CTA), design 3-touch follow-up sequences (Day
  3 case study, Day 7 different angle, Day 14 binary close), run 30-point
  audits across infrastructure / targeting / messaging / operations, plan
  5-email nurture streams with route-to-sales triggers, validate
  pre-campaign domain health (15 checks across DNS, reputation, warm-up,
  content), and pick subject lines from 25 framework-organized patterns
  (pain, curiosity, social proof, direct). Anchors every output on a Pain
  Signal Profile — not demographics. Based on the JMC Cold Email &
  Outreach Craft course (jaymountconsulting.com/learn). Triggers on:
  "cold email", "write a cold email", "cold outreach", "follow-up sequence",
  "deliverability", "SPF", "DKIM", "DMARC", "domain health", "outbound audit",
  "subject line", "nurture sequence", "outreach craft".
allowed-tools: Read Write Grep Glob Bash
  - WebFetch
license: MIT

---

# Cold Email — JMC Outreach Craft Skill

Comprehensive cold email orchestrator for B2B operators. Anchors every
output on a Pain Signal Profile (not demographics) and forces the output
into a shape you can ship.

## Contents

- Checklist
- Quick Reference
- Core principles (the JMC stance)
- Workflow router
- Variables (sub-skills inherit these)
- References
- Sub-skills
- Specialist agents
- Free hosted version

## Quick Reference

| Slash | What it does |
|---|---|
| `/cold-email` | Interactive mode — detect intent, route to a sub-skill |
| `/cold-email write` | Draft a single signal-anchored cold email (<90 words, binary CTA) |
| `/cold-email sequence` | Design a 3-touch or 5-touch follow-up sequence |
| `/cold-email audit` | 30-point outbound program audit (infra / targeting / messaging / ops) |
| `/cold-email nurture` | 5-email nurture stream with route-to-sales trigger |
| `/cold-email deliverability` | 15-point pre-campaign domain health check |
| `/cold-email subject` | Subject-line patterns by framework (pain / curiosity / proof / direct) |

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
| "Write a cold email to..." | `skills/cold-email-craft` |
| "Build a 3-touch / follow-up sequence" | `skills/cold-email-craft` (sequence mode) |
| "Audit my outbound program" | `skills/cold-email-audit` |
| "Design a nurture stream" | `skills/cold-email-nurture` |
| "Is my domain ready to send?" | `skills/cold-email-deliverability` |
| "Suggest subject lines" | `skills/cold-email-subject-lines` |

If intent is ambiguous, ask one clarifying question — never two.

## Variables (sub-skills inherit these)

The core framework operates on six variables. Capture them once, reuse
across all sub-skills:

| Variable | Source | Example |
|---|---|---|
| `firstName` | Recipient list | Sarah |
| `role` | LinkedIn / CRM | VP of Demand Gen |
| `company` | Same | Acme Cloud |
| `signal` | Public signal — job post, funding, product launch, leadership change | "Just posted 'Senior Demand Gen Lead' role on LinkedIn 4 days ago" |
| `pain` | Pain Signal Profile — what the signal implies | "Pipeline gap; existing demand gen motion isn't producing enough SQLs" |
| `evp` | Your one-line value prop in their words | "We help Series-B SaaS hit pipeline targets without hiring 2 more SDRs" |
| `senderName` | You | Jay |

If any are missing, ask the user — don't fabricate.

## References

Load these on demand for deeper context:

- `references/jmc-framework.md` — The full JMC cold email framework
- `references/banned-patterns.md` — Lines / openers / closes that fail
- `references/binary-ctas.md` — 30 binary CTA patterns
- `references/psp-anchors.md` — How to derive signal → pain → EVP

## Sub-skills

- [`skills/cold-email-craft`](../skills/cold-email-craft) — Single email + 3-touch sequence drafting
- [`skills/cold-email-audit`](../skills/cold-email-audit) — 30-point outbound program audit
- [`skills/cold-email-nurture`](../skills/cold-email-nurture) — 5-email nurture stream design
- [`skills/cold-email-deliverability`](../skills/cold-email-deliverability) — 15-point pre-campaign domain health
- [`skills/cold-email-subject-lines`](../skills/cold-email-subject-lines) — Subject-line patterns by framework

## Specialist agents

- [`agents/cold-email-reviewer`](../agents/cold-email-reviewer.md) — Quality scorer (0-100) against framework
- [`agents/cold-email-deliverability-auditor`](../agents/cold-email-deliverability-auditor.md) — DNS/reputation specialist

## Free hosted version

The same job runs in a browser, no install and no key:
[Cold Email Linter](https://jaymountconsulting.com/tools/cold-email-linter)


## Checklist

Copy this list and tick it in order.

- [ ] 1. Do the step this skill names.
- [ ] 2. Review the draft against that step.

Check again until the draft holds.

Go back to step 1 if step 2 fails.
