#!/usr/bin/env python3
"""
score_letter.py — Refuse a first touch that is not anchored on a signal.

Checks one letter (the email body) against the public signal it claims
to answer. Refuses, listing every reason, when:

  1. `public_signal` is missing
  2. no run of 3+ words from the signal appears verbatim in the letter
     (the signal is paraphrased, not quoted)
  3. the letter leans on demographics or template filler
     ("VPs of Marketing at Series B companies", "companies like yours",
     "hope you're well", "just bumping")
  4. the letter is 90 words or more
  5. the ask is not binary: no question, more than one question, or an
     open question ("what do you think?", "let me know your thoughts?")

USAGE:
    python3 score_letter.py --file draft.json [--json]
    python3 score_letter.py --stdin < draft.json

Draft JSON: {"public_signal": "...", "letter": "..."}

EXIT CODES:
    0   ok — prints the letter and the lint line
    1   refused — prints every reason
    2   bad input (never echoed)

NO network calls. NO LLM. Does not send.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List


MAX_INPUT_BYTES = 2_000_000
MAX_WORDS = 90
SIGNAL_SPAN = 3

# Demographics and template filler. A role on its own ("your VP of Sales
# posted...") is not flagged; a role pinned to a segment is.
_ROLE = r"(?:vps?|heads?|directors?|managers?|founders?|c[a-z]os?|chief [a-z]+ officers?)"
_SEGMENT = (
    r"(?:series[ -][a-e]\b|seed[ -]stage|early[ -]stage|growth[ -]stage|"
    r"late[ -]stage|mid[ -]market|fast[ -]growing|high[ -]growth|"
    r"\d+[ -](?:person|people|employee)|b2b|saas|enterprise)"
)
DEMOGRAPHIC_RE = re.compile(
    r"\bhope (?:you(?:'|’)re|you are|this finds you|your week)\b"
    r"|\bjust (?:bumping|checking in|following up)\b"
    r"|\bfollowing up on my last\b"
    rf"|\b{_ROLE}(?: of [\w&-]+(?: [\w&-]+)?)? (?:at|in|from) (?:an? )?{_SEGMENT}"
    r"|\bseries[ -][a-e] (?:companies|startups|founders|teams|leaders)\b"
    r"|\b(?:companies|teams|people|leaders|founders|folks|businesses) like (?:yours|you)\b"
    r"|\bin your (?:industry|space|vertical|sector)\b"
    r"|\bprofessionals in\b"
    r"|\b(?:marketing|sales|revenue|growth|ops|operations|it|hr|finance) leaders (?:like|at|in)\b"
    r"|\bi (?:noticed|see|saw) you(?:'|’)re an? \b",
    re.IGNORECASE,
)

# A yes/no ask does not open with an open interrogative, and does not
# borrow a banned close (references/banned-patterns.md).
OPEN_LEADS = {"what", "how", "why", "when", "where", "which", "who", "whom", "whose"}
OPEN_PHRASE_RE = re.compile(
    r"\blet me know\b|\bthoughts\b|\bhappy to chat\b|\bwould love to\b|\bwhat do you think\b",
    re.IGNORECASE,
)
SENTENCE_RE = re.compile(r"[^.!?\n]+[.!?]*")
WORD_RE = re.compile(r"[a-z0-9]+(?:['’][a-z]+)?")


def fail_input(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def read_text(path: Path) -> str:
    try:
        if not path.exists():
            fail_input("file not found")
        if not path.is_file():
            fail_input("not a file")
        if path.stat().st_size > MAX_INPUT_BYTES:
            fail_input("file is too large")
        raw = path.read_bytes()
    except SystemExit:
        raise
    except OSError:
        fail_input("cannot read file")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        fail_input("file is not UTF-8 text")


def read_stdin_text() -> str:
    raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        fail_input("input is too large")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        fail_input("input is not UTF-8 text")


def parse_json(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        fail_input("invalid JSON")
    if not isinstance(data, dict):
        fail_input("JSON must be an object")
    return data


def nonempty_text(value) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""


def words(text: str) -> List[str]:
    return WORD_RE.findall(text.lower().replace("’", "'"))


def signal_quoted(signal: str, letter: str) -> bool:
    """True when a run of SIGNAL_SPAN words from the signal appears in the
    letter in order. A signal shorter than the span must appear whole."""
    sig, body = words(signal), words(letter)
    n = min(SIGNAL_SPAN, len(sig))
    if n == 0:
        return False
    body_runs = {tuple(body[i:i + n]) for i in range(len(body) - n + 1)}
    return any(tuple(sig[i:i + n]) in body_runs for i in range(len(sig) - n + 1))


def questions(letter: str) -> List[str]:
    return [s.strip() for s in SENTENCE_RE.findall(letter) if s.strip().endswith("?")]


def ask_problem(letter: str) -> str:
    """'' when there is exactly one yes/no ask; otherwise the reason."""
    asks = questions(letter)
    if not asks:
        return "no binary ask: no sentence ends in '?'"
    if len(asks) > 1:
        return f"more than one ask: {len(asks)} questions"
    ask = asks[0]
    # "If it's not a priority, no worries — should I follow up in Q4?"
    # The ask is the clause after the last comma or dash.
    clause = re.split(r"[,;:—–]| - ", ask)[-1]
    lead = (words(clause) or [""])[0]
    if lead in OPEN_LEADS or OPEN_PHRASE_RE.search(ask):
        return "ask is open-ended, not yes/no"
    return ""


def check(data: dict) -> dict:
    signal = nonempty_text(data.get("public_signal"))
    letter = nonempty_text(data.get("letter"))
    count = len(letter.split())

    reasons: List[str] = []
    if not signal:
        reasons.append("missing public signal")
    if not letter:
        reasons.append("missing letter")
    else:
        if signal and not signal_quoted(signal, letter):
            reasons.append(
                f"signal not quoted: no {SIGNAL_SPAN}-word run of public_signal appears in the letter"
            )
        demo = DEMOGRAPHIC_RE.search(letter)
        if demo:
            reasons.append(f"demographic email: '{demo.group(0).lower()}'")
        if count >= MAX_WORDS:
            reasons.append(f"letter is {count} words; must be under {MAX_WORDS}")
        problem = ask_problem(letter)
        if problem:
            reasons.append(problem)

    return {"ok": not reasons, "reasons": reasons, "word_count": count}


def main() -> int:
    parser = argparse.ArgumentParser(description="Score one signal-anchored letter")
    parser.add_argument("--file", help="Path to a JSON draft")
    parser.add_argument("--stdin", action="store_true", help="Read the JSON draft from stdin")
    parser.add_argument("--json", action="store_true", help="Print the result as JSON")
    args = parser.parse_args()

    if args.file and args.stdin:
        fail_input("pass --file or --stdin, not both")
    if args.stdin:
        data = parse_json(read_stdin_text())
    elif args.file:
        data = parse_json(read_text(Path(args.file)))
    else:
        fail_input("pass --file or --stdin")

    result = check(data)
    if args.json:
        print(json.dumps(result, indent=2))
    elif result["ok"]:
        print(nonempty_text(data.get("letter")))
        print(f"lint: {result['word_count']} words")
    else:
        print("refused:")
        for reason in result["reasons"]:
            print(f"  - {reason}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
