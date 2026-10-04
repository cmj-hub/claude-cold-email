# Contributing

Thanks for opening this repo. A few notes on how this project works
before you contribute.

## What kinds of contributions land

- **Bug reports** — open an issue with a reproducible case. The
  scripts in `scripts/` are deterministic, so bugs there are usually
  one-line fixes.
- **New modes** that extend the existing framework. Discuss in
  an issue first if it's a substantial addition.
- **Calibration improvements** to the scoring scripts — if you can
  show a case where the script scores wrong, that's gold.
- **Cross-runtime ports** (Cursor, Gemini CLI, Codex) — see the
  Install section of the README.
- **Translation** of the framework reference docs.

## What doesn't land

- Renaming the JMC framework concepts (Signal → Pain → EVP → Ask, the
  5 Schwartz tiers, the 4 content pillars) — these are course-anchored.
- Adding LLM calls inside the skills. The whole point is that the
  skills are deterministic.
- Adding paid-API dependencies to scripts. Scripts must work zero-dep.
- Renaming `claude-*` → `<other-runtime>-*`. We ship per-runtime ports
  as separate plugins instead.

## Development setup

```bash
git clone https://github.com/cmj-hub/<this-repo>.git
cd <this-repo>
# Test the install locally
./install.sh   # or install.ps1 on Windows
```

For Python scripts:

```bash
# All scripts are zero-dep Python 3.8+ — just run them
python3 scripts/<script>.py --help

# What CI runs
python3 scripts/validate-skill-frontmatter.py
python3 scripts/check_refs.py
python3 -m unittest discover -s tests
bash scripts/smoke-test.sh          # needs `dig` and network for the DNS checks
```

Layout: the pack has one skill, `skills/cold-email/SKILL.md`. Each job is
a mode in `skills/cold-email/modes/<mode>.md` (plain markdown, no
frontmatter, read on demand), routed from the SKILL.md table. Shared
references live in `skills/cold-email/references/`. Trigger evals live in
`evals/<case>/` (`prompt.md` + `graders/*.md`); run them by hand with the
Evals workflow, never in normal CI.

Scorer CLI: every script takes `--file PATH` or `--stdin`, prints text by
default and one JSON object with `--json`, exits 0 pass / 1 refused / 2
bad input (never echoing the input), writes each refusal as `- what is
wrong → what to change`, and ends with a `Next:` line.

## Pull-request checklist

- [ ] Skill names follow the spec (lowercase, hyphens, ≤64 chars,
      directory matches `name:` in frontmatter)
- [ ] New trigger phrases go in the SKILL.md routing table
- [ ] If you touch a script, add or update a case in `tests/` and paste
      the smoke-test output in the PR
- [ ] Every path a skill tells the agent to load or run exists
      (`python3 scripts/check_refs.py`)
- [ ] A new mode gets a row in the SKILL.md routing table, a word in
      `argument-hint`, and a link from SKILL.md
- [ ] CHANGELOG.md updated
- [ ] No new dependencies (any of: pip packages, npm packages, API
      keys, paid services)

## Reporting calibration issues with scoring scripts

If a script (`spam_word_lint.py` / `score_subject_line.py` /
`score_reply.py` / `score_list.py` / `check_deliverability.py`) scores
something obviously wrong:

1. Paste the input that produced the wrong score
2. State your expected score + actual score
3. Note which axis is mis-calibrated

Each calibration fix lands with a test in `tests/test_scoring.py` that
pins the input and the expected category or score. Lexicons are the
lists at the top of each script; change those before changing scoring
logic, and keep the deterministic path stable.

## License

By contributing, you agree your contributions ship under the MIT
license already on this repo.

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
Part of the JMC public-build spine — see [/build](https://jaymountconsulting.com/build).
