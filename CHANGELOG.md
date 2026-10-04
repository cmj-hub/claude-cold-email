# Changelog

## [0.4.0] — 2026-10-04

Plugin loading, honest scoring, and the missing pieces the skills
already promised.

### Fixed
- **The main `cold-email` skill now loads as a plugin skill.** It lived at
  `cold-email/`, outside `skills/`, so the plugin loader never saw it.
  Moved to `skills/cold-email/`; shared references are now in
  `skills/cold-email/references/`.
- **Nine dead references.** Skills told the agent to load files that did
  not exist (`psp-anchors.md`, `audit-rubric.md`, `bulk-sender-rules.md`,
  `copy-frameworks.md`, `subject-line-patterns.md`, three lexicon files,
  and `score_list.py`). Each one now exists or points at the real source.
- **Orchestrator routed to 5 of 11 sub-skills.** Kickoff, onboarding,
  spam-lint, list-quality, reply-scoring, and weekly-rhythm were
  unreachable from the router. The orchestrator also gains the preflight
  and self-check rubric that `AGENTS.md` already referenced.
- `check_deliverability.py` reported "No SPF / DKIM / DMARC / MX" for every
  domain when `dig` was missing or a lookup timed out. It now exits 2 when
  `dig` is missing and marks unverifiable checks `unknown` (left out of
  the score) instead of passing or failing them.
- Blacklist check matched the words "spamhaus" / "surbl" on the
  multirbl page, so it could not tell listed from clean. It now queries
  `dbl.spamhaus.org` and `multi.surbl.org` over DNS and probes each
  zone's test entry first, so a refused resolver reads as unknown.
- DMARC: the pack said Google / Yahoo require `p=quarantine`. They require
  a DMARC record; `p=none` is the minimum. Enforcement is now scored as
  "important", not "critical", in the script, skill, and agent.
- Spam lint and subject scorer matched trigger words inside other words
  ("earn" in "learn", "credit" in "accredited", "urgent" in "insurgent").
  Matching is now whole-word.
- Any 3-letter acronym (SDR, CRM, ARR) counted as an ALL CAPS subject.
  Shouting is now a 5+ letter capitalised word, two in a row, or a
  mostly-capitals line.
- A fake `Re:` / `Fwd:`, emoji, ALL CAPS, or clickbait subject could still
  score "Ship after small fix". Banned subject patterns now cap at 49.
- Reply scorer: "sure" matched "ensure" / "pressure", pricing questions
  missed buy-signal, curly apostrophes defeated every `'` pattern, a bare
  "stop" anywhere meant not-interested, and short unmatched replies
  ("Who is this?") were routed as not-interested. Unmatched replies now
  go to human review as neutral.
- Release workflow interpolated CHANGELOG text straight into a shell
  command; notes now go through a file.
- Removed unverifiable accuracy figures from the reply-scoring skill.

### Added
- `scripts/score_list.py` — the list scorer `cold-email-list-quality`
  described but did not ship: dedup, role-fit, signal freshness, email
  validity, exclusions, company stage; `--write` splits cleaned / removed
  CSVs. Sample input: `examples/prospects.csv`.
- `brand-config.schema.json` (the example's `$schema` pointed at a file
  that did not exist).
- `references/psp-anchors.md`, `references/bulk-sender-rules.md`,
  `cold-email-audit/references/audit-rubric.md`.
- `tests/test_scoring.py` (21 cases) and `scripts/check_refs.py`; CI now
  runs the unit tests, the reference check, and a guard that every
  `SKILL.md` sits under `skills/`.
- Skills that drive a script now allow-list it and say where `scripts/`
  is relative to the skill directory.

### Fixed (plugin directory review)
- Plugin directory review: single-line `allowed-tools` with specific commands only (no bare shell), installer no longer copies into home-directory skill paths, and skills/agents no longer ask for a machine credential.
- Allow-lists use repo-relative `python3 scripts/…` paths (no host-env interpolation). `install.sh` and `install.ps1` point at the repo and do not fetch a remote installer.

## [0.3.0] — 2026-09-08

Public magnet pass. Instrument stays public. First loop is 15 minutes.

### Added
- Definition-first README (GEO paragraph, 15-minute artifact, FAQ H2s, current Pass price).
- Cross-agent installer: `npx skills add cmj-hub/claude-cold-email --all -g --full-depth` (Claude Code, Cursor, Codex, Grok, Copilot, Windsurf, Cline, OpenCode, Antigravity, Goose, and the rest of the skills CLI list). Fallback copies into well-known `*/skills` dirs.
- `package.json` (`jmc-cold-email`) so `npm install github:cmj-hub/claude-cold-email` and `npx jmc-cold-email` work. Not published to npmjs.com.
- `examples/` golden good/bad pair for the first loop.

### Changed
- Removed pricing copy from the public pack; CTAs point at the free hosted tools.
- `plugin.json` description is the definition, homepage is /skills.

## [0.2.1] — 2026-05-24

Marketplace-submission compliance pass. No functional changes.

### Fixed
- `plugin.json` `author` field now an object `{ "name": "..." }` per Claude Code plugin manifest schema (was a string).
- `skills/cold-email-spam-lint/SKILL.md` frontmatter `description` now quoted so the embedded `fake-Re:` colon-space pattern parses cleanly under YAML.

Both gates required for submission to the `claude-community` marketplace via [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit). `claude plugin validate` now passes.

## [0.2.0] — 2026-05-23

Substantial polish pass. Adds onboarding + adaptive routing + deterministic
scripts + 3-tier config + cost-replacement positioning. Doubles the
sub-skill count and adds real Python/Bash scoring (not pure prose).

### Added
- **3-tier config** at the repo root:
  - `brand-config.example.json` — ICP / PSP / EVP / tone / infrastructure / ops
  - `SOUL.md` — operator voice template (phrases used, phrases banned, stories)
  - `AGENTS.md` — behavior rules (refuses generic output, refuses banned patterns, etc.)
- **6 new sub-skills**:
  - `cold-email-onboarding` — 10-minute interactive setup → writes brand-config + SOUL
  - `cold-email-kickoff` — state-aware router (7-step path: onboarding → PSP → EVP → infra → deliv → ship → iterate)
  - `cold-email-weekly-rhythm` — Mon (signals + list) / Wed (ship + triage) / Fri (score + adjust) cadence
  - `cold-email-spam-lint` — 200+ word spam-trigger scan via Python script
  - `cold-email-reply-scoring` — buy-signal / positive / neutral / not-interested / auto-reply classifier via Python
  - `cold-email-list-quality` — 6-axis list scoring (dedup / role-fit / freshness / validity / exclusion / stage)
- **5 deterministic scripts** in `scripts/`:
  - `spam_word_lint.py` — calibrated 200+ lexicon + clickbait + ALL CAPS + emoji + fake-thread + link/image ratio
  - `score_subject_line.py` — 5-axis subject scoring with framework-fit detection
  - `score_reply.py` — regex + feature-engineered reply classifier (no LLM, <10ms per reply)
  - `dig_dns.sh` — POSIX bash for SPF / DKIM / DMARC / MX / reverse DNS lookups
  - `check_deliverability.py` — 15-check deliverability scoring with public blacklist heuristic
- README rewrite with cost-replacement positioning ("Replace an $80K SDR with the JMC framework + ~$130/mo in tools")
- Cross-skill dependency mermaid diagram
- Repo-structure table showing the full layout

### Verified
- All 5 scripts run end-to-end with zero deps (Python stdlib only; `dig` for DNS)
- `spam_word_lint.py` correctly scores test cases (URGENT/CAPS/emoji → 67/100)
- `score_reply.py` correctly classifies "send me the case study and what dates work" → buy-signal 0.8
- `score_subject_line.py` correctly identifies "Pipeline gap after the Q3 freeze?" → 100/100, pain framework
- `check_deliverability.py` against jaymountconsulting.com → 87/100, surfaced 2 real findings


## [0.1.0] — 2026-05-23

Initial release. Wave 1 of the JMC public-build spine.

### Added
- Main `cold-email/` orchestrator skill (Claude Code Agent Skills spec)
- 5 sub-skills:
  - `cold-email-craft` — single email + 3-touch sequence drafting
  - `cold-email-audit` — 30-point outbound program audit
  - `cold-email-nurture` — 5-email nurture stream designer
  - `cold-email-deliverability` — 15-point pre-campaign domain health
  - `cold-email-subject-lines` — 4-framework subject-line library
- 2 specialist agents:
  - `cold-email-reviewer`
  - `cold-email-deliverability-auditor`
- References: `jmc-framework.md`, `banned-patterns.md`, `binary-ctas.md`
- One-line install (`install.sh`, `install.ps1`)
- Claude Code plugin manifest
