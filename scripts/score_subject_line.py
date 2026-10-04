#!/usr/bin/env python3
"""
score_subject_line.py — Deterministic subject-line scorer.

Scores a subject line 0-100 across 5 axes: length, spam-trigger words,
clickbait, personalization, framework-fit (pain/curiosity/proof/direct).

USAGE:
    python3 score_subject_line.py --subject "<line>"
    python3 score_subject_line.py --subject "<line>" --framework direct
    python3 score_subject_line.py --file examples/t1.email.md [--json]
    python3 score_subject_line.py --stdin   # JSON {"subject":"","framework":"..."}

--file takes a JSON object ("subject", optional "framework") or a
plain-text email whose first line is "Subject: ...". --format json is
the same as --json.

EXIT CODES:
    0   score >= 70 (ship)
    1   score < 70; every flag reads "- what is wrong → what to change"
    2   bad input (never echoed)

NO network calls. NO LLM.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict

# Sibling script; both ship together in scripts/. Still stdlib only.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from spam_word_lint import load_draft_file, phrase_pattern, shouty_caps  # noqa: E402


MAX_INPUT_BYTES = 2_000_000


def fail_input(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def parse_json(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        fail_input("invalid JSON")
    if not isinstance(data, dict):
        fail_input("JSON must be an object")
    return data


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


# Subject-specific subset of the spam_word_lint.py lexicon. Matching uses
# the same whole-word rule (phrase_pattern), so "earn" does not hit "learn".
SPAM_WORDS = [
    "act now", "act fast", "limited time", "limited offer", "expires today",
    "deadline", "hurry", "urgent", "free money", "free cash", "earn",
    "double your income", "no investment", "no risk", "100% free",
    "100% guaranteed", "risk-free", "no obligation", "amazing", "incredible",
    "you won't believe", "this one trick", "guaranteed",
]

CLICKBAIT_PATTERNS = [
    r"you won['’]t believe",
    r"this one (trick|secret|tip|hack)",
    r"doctors hate",
    r"will (shock|amaze|surprise) you",
]

FAKE_THREAD = ["re:", "re :", "fwd:", "fw:"]

# Framework families and their hallmark words.
FRAMEWORK_SIGNALS = {
    "pain": ["pipeline", "gap", "broken", "stuck", "missed", "leak", "drop", "decay"],
    "curiosity": ["tried", "after", "saw", "noticed", "before", "without"],
    "social-proof": ["how", "hit", "shipped", "reached", "case", "results"],
    "direct": ["15 min", "10 min", "20 min", "quick call", "intro", "demo"],
}

EMOJI_RE = re.compile(
    r"[\U0001F300-\U0001F9FF\U00002702-\U000027B0]+",
    flags=re.UNICODE,
)


@dataclass
class SubjectScore:
    subject: str
    score: int
    length_chars: int
    length_words: int
    framework_fit: Optional[str]
    axes: Dict[str, int]
    flags: List[str]
    verdict: str


def axis_length(subject: str) -> tuple:
    chars = len(subject)
    words = len(subject.split())
    score = 20
    flags = []
    if chars > 50:
        score -= 12
        flags.append(f"Subject {chars} chars — Gmail truncates around 30 mobile, 60 desktop")
    if words > 7:
        score -= 8
        flags.append(f"{words} words — best cold subjects are ≤7 words")
    return max(0, score), flags


def axis_spam(subject: str) -> tuple:
    score = 25
    flags = []
    for w in SPAM_WORDS:
        if phrase_pattern(w).search(subject):
            score -= 5
            flags.append(f"Spam-trigger: '{w}'")
    caps = shouty_caps(subject)
    if caps:
        score -= 8
        flags.append(f"ALL CAPS: {caps}")
    if EMOJI_RE.search(subject):
        score -= 10
        flags.append("Emoji in subject (B2B deliverability hit)")
    for prefix in FAKE_THREAD:
        if subject.lstrip().lower().startswith(prefix):
            score -= 15
            flags.append(f"Fake threading: subject starts with '{prefix}'")
            break
    return max(0, score), flags


def axis_clickbait(subject: str) -> tuple:
    score = 15
    flags = []
    for pat in CLICKBAIT_PATTERNS:
        if re.search(pat, subject, flags=re.IGNORECASE):
            score -= 10
            flags.append(f"Clickbait pattern: {pat}")
    return max(0, score), flags


def axis_personalization(subject: str) -> tuple:
    """Looks for unmerged tokens (bad), or specific company/person refs (good)."""
    score = 15
    flags = []
    if re.search(r"\{\{?[a-zA-Z_]+\}?\}", subject):
        score -= 15
        flags.append("Unmerged personalization token (e.g., {{firstName}}) — will land as-is")
    # Reward presence of a proper-noun-shaped token (very rough heuristic)
    if re.search(r"\b[A-Z][a-z]+\b", subject) and not re.search(r"^(The|A|An|Re|Fwd)\b", subject):
        score = min(15, score + 5)  # bonus, cap at 15
    return max(0, score), flags


def axis_framework_fit(subject: str, requested: Optional[str]) -> tuple:
    """Detect which framework family this subject fits. If user requested a
    specific framework, score 25 if matched, 10 if mismatched."""
    score = 25
    flags = []
    matches = []
    for family, words in FRAMEWORK_SIGNALS.items():
        if any(phrase_pattern(w).search(subject) for w in words):
            matches.append(family)

    detected = matches[0] if matches else None

    if requested:
        if requested in matches:
            score = 25
        else:
            score = 10
            flags.append(f"Requested framework '{requested}' but subject signals '{detected or 'none'}'")
    elif not detected:
        score = 12
        flags.append("No clear framework signal (pain / curiosity / proof / direct)")

    return max(0, score), flags, detected


BANNED_CAP = 49


def verdict_for(score: int) -> str:
    if score >= 85:
        return "Ship — strong subject"
    if score >= 70:
        return "Ship after small fix"
    if score >= 50:
        return "Iterate — multiple flags"
    return "Rewrite — too many issues"


def score_subject(subject: str, framework: Optional[str] = None) -> SubjectScore:
    length_score, length_flags = axis_length(subject)
    spam_score, spam_flags = axis_spam(subject)
    cb_score, cb_flags = axis_clickbait(subject)
    pers_score, pers_flags = axis_personalization(subject)
    fw_score, fw_flags, detected = axis_framework_fit(subject, framework)

    total = length_score + spam_score + cb_score + pers_score + fw_score

    # Banned subject patterns (references/banned-patterns.md) never ship,
    # however well the other axes score.
    banned = cb_flags or any(
        f.startswith(("Fake threading", "Emoji", "ALL CAPS")) for f in spam_flags
    )
    if banned and total > BANNED_CAP:
        total = BANNED_CAP

    return SubjectScore(
        subject=subject,
        score=total,
        length_chars=len(subject),
        length_words=len(subject.split()),
        framework_fit=detected,
        axes={
            "length": length_score,
            "spam": spam_score,
            "clickbait": cb_score,
            "personalization": pers_score,
            "framework-fit": fw_score,
        },
        flags=length_flags + spam_flags + cb_flags + pers_flags + fw_flags,
        verdict=verdict_for(total),
    )


NEXT_OK = "Next: check the sending domain (/cold-email:cold-email deliverability), then send."
NEXT_FIX = "Next: fix the lines above and run this again."

FLAG_FIXES = [
    ("Subject ", "cut it to under 40 characters"),
    ("Spam-trigger", "swap that word for a plain one"),
    ("ALL CAPS", "write it in sentence case"),
    ("Emoji", "remove the emoji"),
    ("Fake threading", "drop the prefix; there is no prior thread"),
    ("Clickbait", "cut the hook; name the specific thing"),
    ("Unmerged personalization", "merge the token or cut it"),
    ("Requested framework", "rewrite it for the framework you asked for, or pass the one it fits"),
    ("No clear framework", "lead with the pain, a peer, a question, or the ask"),
]


def fix_for(flag: str) -> str:
    for prefix, fix in FLAG_FIXES:
        if flag.startswith(prefix):
            return fix
    if " words" in flag:
        return "cut it to 7 words or fewer"
    return "rewrite the subject"


def next_step(s: SubjectScore) -> str:
    return NEXT_OK if s.score >= 70 else NEXT_FIX


def format_text(s: SubjectScore) -> str:
    lines = [
        f"# Subject Line Score",
        f"",
        f"Subject: {s.subject}",
        f"Score: {s.score}/100 — {s.verdict}",
        f"Length: {s.length_words} words / {s.length_chars} chars",
        f"Framework fit: {s.framework_fit or 'none'}",
        f"",
        f"## Per-axis",
    ]
    for axis, value in s.axes.items():
        lines.append(f"  {axis.ljust(20)} {value}")
    if s.flags:
        lines.append("")
        lines.append("## Flags")
        for f in s.flags:
            lines.append(f"- {f} → {fix_for(f)}")
    lines.append("")
    lines.append(next_step(s))
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: python3 scripts/score_subject_line.py --file examples/t1.email.md --framework pain   # exit 0",
    )
    parser.add_argument("--file", default=None, help="Draft file: JSON object or plain-text email")
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--subject", default="", help="Subject line to score")
    parser.add_argument(
        "--framework",
        default=None,
        choices=["pain", "curiosity", "social-proof", "direct", None],
        help="If you targeted a specific framework, score the match",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help='Read JSON {"subject":"","framework":"..."} from stdin',
    )
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
    )
    args = parser.parse_args()

    if args.file and args.stdin:
        fail_input("pass --file or --stdin, not both")
    if args.file:
        draft = load_draft_file(args.file)
        subject = draft["subject"]
        framework = args.framework or draft["framework"]
    elif args.stdin:
        payload = parse_json(read_stdin_text())
        subject = payload.get("subject", "")
        if not isinstance(subject, str):
            subject = ""
        framework = payload.get("framework")
        if framework is not None and not isinstance(framework, str):
            framework = None
    else:
        subject = args.subject
        framework = args.framework

    if not subject:
        print("No subject. Use --subject, --file, or --stdin.", file=sys.stderr)
        return 2

    result = score_subject(subject, framework)
    if args.json or args.format == "json":
        payload = asdict(result)
        payload["fixes"] = [fix_for(f) for f in result.flags]
        payload["next"] = next_step(result)
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(result))

    return 0 if result.score >= 70 else 1


if __name__ == "__main__":
    sys.exit(main())
