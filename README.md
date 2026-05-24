# claude-cold-email

A Claude Code skill for cold email & outreach craft. Signal-anchored
openers, 3-touch sequences, 30-point program audits, 5-email nurture
streams, 15-point pre-campaign deliverability checks, and 25
subject-line patterns — all anchored on a Pain Signal Profile, not
demographics.

Based on the **[Cold Email & Outreach Craft](https://jaymountconsulting.com/learn/courses/cold-email-outreach-craft)**
course from The Compounding Engine. No LLM API calls inside the skill,
no paid services, no remote dependencies.

## What it does

| Sub-skill | Job |
|---|---|
| `cold-email-craft` | Draft a single signal-anchored cold email or a 3-touch follow-up sequence |
| `cold-email-audit` | 30-point audit of an outbound program (infra / targeting / messaging / ops) |
| `cold-email-nurture` | 5-email nurture stream with route-to-sales triggers |
| `cold-email-deliverability` | 15-point pre-campaign domain health (SPF, DKIM, DMARC, blacklists, warm-up, content) |
| `cold-email-subject-lines` | Generate or critique subject lines across 4 framework families |

Plus two specialist agents:

- `cold-email-reviewer` — scores any draft 0-100 against the framework
- `cold-email-deliverability-auditor` — runs DNS + reputation lookups via native tools (no paid APIs)

## Why this isn't another prompt library

Most operator prompt libraries are 200 entries of vague one-liners.
This is one skill (with sub-skills) hand-tuned around a single
framework: every output anchors on a Pain Signal Profile, names the
constraint, and forces the shape into something you can ship.

The framework, in one diagram:

```
Signal  →  Pain  →  EVP  →  Ask
  ↓         ↓       ↓       ↓
 What     What     What     What
 they      that    you do   you want
 just     means    about    them to
 did                it       do next
```

Every line of every email this skill produces exists to serve one of
those four jobs. If a line doesn't, the skill cuts it.

## Install

### Claude Code (recommended)

```bash
/plugin marketplace add cmj-hub/claude-cold-email
/plugin install cold-email
```

### One-line install (any project, manual)

```bash
curl -fsSL https://raw.githubusercontent.com/cmj-hub/claude-cold-email/main/install.sh | bash
```

This clones the repo and copies `cold-email/`, `skills/cold-email-*`,
and `agents/cold-email-*.md` into `~/.claude/skills/` and
`~/.claude/agents/`.

### Windows

```powershell
iwr https://raw.githubusercontent.com/cmj-hub/claude-cold-email/main/install.ps1 -useb | iex
```

## Usage

In any Claude Code session:

```
> Write a cold email to Sarah, VP Demand Gen at Acme. She just posted a Senior Demand Gen Lead role 4 days ago.
```

Claude routes to `cold-email-craft`, asks for your EVP if not in
context, generates a <90-word signal-anchored email with a binary CTA,
and offers the "rewrite the weakest line" pass.

Or:

```
> Audit our outbound program
```

→ Loads `cold-email-audit`. Asks for the 4 dimensions of context.
Returns a 0-100 score, top 3 levers, 90-day remediation order.

Or:

```
> Is outreach.mycompany.com ready to send?
```

→ Loads `cold-email-deliverability` + the deliverability auditor agent.
Runs DNS lookups (SPF, DKIM, DMARC, MX, reverse DNS), checks public
blacklists, validates Feb-2024 bulk-sender compliance, returns a fix
order.

## Banned patterns

The skill refuses to produce any of these. Full list at
[`cold-email/references/banned-patterns.md`](./cold-email/references/banned-patterns.md):

- "Hope you're well" / "Hope this finds you well"
- "Just bumping this" / "Following up on my last email"
- "Let me know your thoughts" / "Happy to chat whenever"
- "Quick question" as an opener
- Multi-paragraph value-prop monologues
- Stacked questions
- Demographics-as-signal ("I noticed you're a VP of Marketing…")

If a draft contains any of these, the skill flags them with a
JMC-shaped alternative.

## Repo structure

```
claude-cold-email/
├── .claude-plugin/plugin.json
├── README.md
├── LICENSE
├── CHANGELOG.md
├── install.sh
├── install.ps1
├── cold-email/                    # Main orchestrator skill
│   ├── SKILL.md
│   └── references/
│       ├── jmc-framework.md       # The full framework
│       ├── banned-patterns.md
│       └── binary-ctas.md
├── skills/                        # Sub-skills (orchestrator-invoked)
│   ├── cold-email-craft/
│   ├── cold-email-audit/
│   ├── cold-email-nurture/
│   ├── cold-email-deliverability/
│   └── cold-email-subject-lines/
└── agents/                        # Specialist scoring agents
    ├── cold-email-reviewer.md
    └── cold-email-deliverability-auditor.md
```

## Course alignment

This skill is the agent-form of the JMC **Cold Email & Outreach Craft**
course. The full course covers:

- Pain Signal Profiles in depth (8 lessons)
- Infrastructure: domains, warm-up, sending architecture (6 lessons)
- Sequence architecture at scale (5 lessons)
- Deliverability forensics (4 lessons)
- Program economics: CPM, CAC, payback (3 lessons)

→ **[jaymountconsulting.com/learn/courses/cold-email-outreach-craft](https://jaymountconsulting.com/learn/courses/cold-email-outreach-craft)**

Want it all-access? **[Operator Pass](https://jaymountconsulting.com/operator-pass)**
unlocks every course in The Compounding Engine plus the 52-tool API
that wraps Cold Email Linter, EVP Generator, Pipeline Calculator, and
14 more — for Claude / Cursor / any MCP-aware agent.

## License

MIT. See [LICENSE](./LICENSE).

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com) as
part of the JMC public-build spine. See
[/build](https://jaymountconsulting.com/build) for what's shipping
this week.
