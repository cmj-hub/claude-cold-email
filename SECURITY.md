# Security

## What this pack does on your machine

- Runs local Python scripts, standard library only, plus one bash script: `score_letter.py`, `spam_word_lint.py`, `score_subject_line.py`, `score_reply.py`, `score_list.py`, `check_deliverability.py`, `dig_dns.sh`. Bad input is refused (exit 2) and never echoed back.
- The scripts read only what you pass them: a draft (JSON or flags), a reply batch, or a prospect CSV / JSONL. The skills read `brand-config.json` and `SOUL.md` at your project root.
- Writes stay in your project: `brand-config.json` and `SOUL.md` (onboarding, field-level merge), draft files such as `letter.json`, and, only with `score_list.py --write`, `<list>.cleaned.csv` and `<list>.removed.csv` next to the input list.
- Network: no Python script opens a socket or HTTP connection. The one exception is DNS. `check_deliverability.py` and `dig_dns.sh` run `dig` for the sending domain you name and its mail host (TXT for SPF, DKIM, DMARC; MX; A and PTR of the MX host), and `check_deliverability.py` also queries the public blacklist DNS zones `dbl.spamhaus.org` and `multi.surbl.org`. The `cold-email-deliverability` skill may run `dig`, `host`, or `nslookup` for that same domain.
- WebFetch is allowed in the `cold-email`, `cold-email-audit`, and `cold-email-deliverability` skills and the `cold-email-deliverability-auditor` agent. It is for opening a public page you point to (a signal source, a blacklist lookup page) when you ask; no script uses it.
- No telemetry. No credentials or API keys are asked for or stored.
- Nothing is sent, posted, or published by the pack. It drafts and scores; you send.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
