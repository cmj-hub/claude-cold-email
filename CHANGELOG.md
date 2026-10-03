# Changelog

## [Unreleased]

### Fixed
- Plugin directory review: single-line `allowed-tools` with specific commands only (no bare shell), installer no longer copies into home-directory skill paths, and skills/agents no longer ask for a machine credential.

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
