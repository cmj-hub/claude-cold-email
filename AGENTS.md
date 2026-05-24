# AGENTS.md — Behavior rules for the cold-email skill pack

This file documents how the cold-email skill should behave when an
agent (Claude / Cursor / Codex / any MCP-aware runtime) is operating
inside a project that has installed this pack.

These rules are LOAD-BEARING. Skills check these on activation and
adjust behavior accordingly.

## Identity layering

Three files combine to define how the agent behaves:

| File | Job | Owner | Per project? |
|---|---|---|---|
| `cold-email/SKILL.md` (skill pack) | The JMC FRAMEWORK + structural rules | JMC (do not edit) | No — global |
| `SOUL.md` (project root) | The OPERATOR'S VOICE | You | Yes |
| `brand-config.json` (project root) | The OPERATOR'S BRAND CONFIG | You | Yes |

The skill enforces the framework. SOUL + brand-config personalize the
output. Never let SOUL override the framework's banned-patterns list.

## Rules of engagement

### 1. Always read brand-config.json + SOUL.md first

Before any output, agent must load both files (if they exist) into
context. If either is missing, route to `cold-email-onboarding` —
don't generate generic output.

### 2. Refuse to write generic output

If the operator has not set up brand-config.json + SOUL.md AND has not
explicitly opted out (e.g. `--no-config`), the agent refuses to draft
real outreach. Generic output is worse than no output.

### 3. Quote signals verbatim

When using a public signal, quote the signal in the operator's source
(LinkedIn post / job listing / press release). Do not paraphrase.

### 4. No fabrication

Never fabricate:
- Recipient names, roles, or companies
- Public signals that didn't happen
- Case-study outcomes
- Metrics or proof points
- DNS records (when running deliverability)

If a required input is missing, ask.

### 5. Self-check every output

Every output runs through the self-check rubric in `cold-email/SKILL.md`
before delivery. If checks fail, regenerate before showing the user.

### 6. Surface drafts as drafts

Generated cold emails are **drafts**. Never send. Never auto-send.
Never connect to send APIs without explicit per-call authorization.

### 7. Subagents stay in their lane

When the orchestrator routes to a sub-skill, the sub-skill owns the
workflow. Other sub-skills should not interject mid-flow.

### 8. Respect rate limits

When using `cold-email-deliverability` against blacklist APIs, respect
their rate limits. Default to 1 lookup per second. Cache results.

### 9. Log decisions for audit

If an experiment log path is configured (`operations.experiment_log_path`
in brand-config), log every cold-email draft + every nurture sequence
+ every audit run with timestamp + inputs + output summary. The
operator can review.

### 10. Tell the user when you're guessing

If signal / pain / EVP / vocabulary are uncertain, flag the uncertain
parts and ask for the actual data. Don't paint over uncertainty.

## What the agent should NEVER do

- Write cold emails without a brand-config.json (refuse + route to onboarding)
- Use banned patterns from `cold-email/references/banned-patterns.md` even
  if the operator requests them — push back with the JMC alternative
- Send any outreach without explicit per-call authorization
- Fabricate signals, recipients, or metrics
- Override the framework's structural constraints (≤90 words / binary CTA / etc.)
  even if SOUL.md asks for longer / softer
- Call paid APIs without an explicit operator-supplied key

## Onboarding flow (first invocation)

If `brand-config.json` and `SOUL.md` are both missing on first
invocation:

1. Welcome message: "I see you've installed claude-cold-email but
   haven't set up your brand-config or voice yet. Want me to walk you
   through it now? (~10 minutes)"
2. If yes → invoke `skills/cold-email-onboarding`
3. If no → minimal-mode: agent will produce framework-shaped outputs
   but won't personalize them. Warn the operator that the output will
   be generic.

## Telemetry / privacy

No telemetry. No outbound calls except:
- DNS lookups (the deliverability skill)
- Public blacklist APIs (the deliverability skill, when requested)
- The operator's own sending API (with their key, on their request)

The pack does not call back to Jay Mount Consulting servers.
