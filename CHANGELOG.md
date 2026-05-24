# Changelog

All notable changes to claude-cold-email.

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
  - `cold-email-reviewer` — 0-100 quality scorer with line-by-line critique
  - `cold-email-deliverability-auditor` — DNS / reputation / bulk-sender compliance
- References:
  - `jmc-framework.md` — the canonical Signal → Pain → EVP → Ask framework
  - `banned-patterns.md` — banned openers, closes, follow-up patterns
  - `binary-ctas.md` — 30 binary CTA patterns
- One-line install scripts (`install.sh`, `install.ps1`)
- Claude Code plugin manifest at `.claude-plugin/plugin.json`
