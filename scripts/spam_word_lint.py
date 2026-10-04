#!/usr/bin/env python3
"""
spam_word_lint.py — Deterministic spam-trigger scanner for cold email.

Scans subject + body against a 200+ word spam-trigger lexicon, plus
structural patterns (ALL CAPS, emoji, fake threading, clickbait,
link/image ratio). Returns a 0-100 deliverability-risk score with
line-by-line flags.

Zero dependencies. Python 3.8+.

USAGE:
    python3 spam_word_lint.py --file examples/t1.email.md [--json]
    python3 spam_word_lint.py --file gtm/letter.json      # {"subject": "", "body" or "letter": ""}
    python3 spam_word_lint.py --subject "Re: URGENT" --body "..."
    python3 spam_word_lint.py --stdin   # read JSON {"subject":"","body":""} from stdin

--file takes a JSON object (keys "subject" and "body", or "letter" for the
body) or a plain-text email whose first line may be "Subject: ...".
--format json is the same as --json.

EXIT CODES:
    0   score >= 75 (ship or ship-after-fix)
    1   score < 75  (rewrite or do-not-send); every flag reads
        "- what is wrong → what to change"
    2   bad input (never echoed)

NO network calls. NO LLM. NO external libraries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple


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


def read_file_text(path: str) -> str:
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except FileNotFoundError:
        fail_input("file not found")
    except IsADirectoryError:
        fail_input("not a file")
    except OSError:
        fail_input("cannot read file")
    if len(raw) > MAX_INPUT_BYTES:
        fail_input("file is too large")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        fail_input("file is not UTF-8 text")
    return ""  # unreachable


def split_email_text(text: str) -> Tuple[str, str]:
    """(subject, body) from a plain-text email: an optional first line
    "Subject: ..." then the body."""
    lines = text.strip().splitlines()
    subject = ""
    if lines and lines[0].lower().startswith("subject:"):
        subject = lines[0].split(":", 1)[1].strip()
        lines = lines[1:]
    return subject, "\n".join(lines).strip()


def load_draft_file(path: str) -> dict:
    """A draft file as {"subject", "body", "framework"}. JSON objects use
    "body" (or "letter"); anything else is read as a plain-text email."""
    text = read_file_text(path)
    if path.lower().endswith(".json") or text.lstrip().startswith("{"):
        data = parse_json(text)
        body = data.get("body", data.get("letter", ""))
        return {
            "subject": data.get("subject", "") if isinstance(data.get("subject", ""), str) else "",
            "body": body if isinstance(body, str) else "",
            "framework": data.get("framework") if isinstance(data.get("framework"), str) else None,
        }
    subject, body = split_email_text(text)
    return {"subject": subject, "body": body, "framework": None}


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


# ----------------------------------------------------------------------------
# Spam-trigger lexicon (sourced from Google Postmaster, Yahoo, Microsoft 2024
# bulk-sender rules; Litmus + Email on Acid public lists; JMC's review of
# 1000+ campaigns).
# ----------------------------------------------------------------------------

URGENCY_TRIGGERS = [
    "act now", "act fast", "limited time", "limited offer", "expires today",
    "expires soon", "deadline", "hurry", "urgent", "immediate action",
    "don't miss", "last chance", "today only", "while supplies last",
    "for a limited time", "buy now", "order now", "click now",
]

FREE_MONEY_TRIGGERS = [
    "free money", "free cash", "make money fast", "earn extra cash",
    "double your income", "make $", "no investment", "no risk",
    "guaranteed income", "lifetime deal", "lifetime access", "100% free", "100% guaranteed",
    "risk-free", "no obligation", "no catch", "no hidden costs",
    "free gift", "free trial", "free preview", "free access",
    "free leads", "free consultation",
]

EXAGGERATED_TRIGGERS = [
    "amazing", "incredible", "unbelievable", "you won't believe",
    "this one trick", "the secret to", "doctors hate", "shocking",
    "miracle", "guaranteed results", "no other product", "best ever",
    "game-changing", "revolutionary", "breakthrough", "life-changing",
]

PUSHY_TRIGGERS = [
    "buy direct", "click here", "click below", "click this link",
    "subscribe now", "sign up now", "register now", "apply now",
    "call now", "call free", "as seen on", "satisfaction guaranteed",
    "satisfaction or", "money back",
]

FINANCIAL_TRIGGERS = [
    "$$$", "cash bonus", "earn $", "extra income", "financial freedom",
    "credit", "debt", "loan", "mortgage", "refinance",
    "easy money", "fast cash", "investors", "stock pick", "stocks",
    "make money working from home", "pre-approved", "compare rates",
]

CLICKBAIT_PATTERNS = [
    r"you won['’]t believe",
    r"this one (trick|secret|tip|hack)",
    r"doctors hate",
    r"what \w+ don['’]t want you to know",
    r"the (secret|truth) (about|behind|to)",
    r"will (shock|amaze|surprise) you",
    r"\d+ (things|ways|reasons|tricks) (you|that) (need|must|should)",
    r"number \d+ will (shock|surprise|amaze)",
]

# Phrases that fake email threading (subject lines starting with these
# without an actual prior thread are a bulk-sender violation).
FAKE_THREAD_PREFIXES = [
    "re:", "re :", "fwd:", "fw:", "fw :", "fwd :",
]

ALL_TRIGGER_WORDS = (
    URGENCY_TRIGGERS + FREE_MONEY_TRIGGERS + EXAGGERATED_TRIGGERS
    + PUSHY_TRIGGERS + FINANCIAL_TRIGGERS
)

# Emoji range (covers most emoji codepoints).
EMOJI_RE = re.compile(
    r"["
    r"\U0001F300-\U0001F5FF"  # symbols & pictographs
    r"\U0001F600-\U0001F64F"  # emoticons
    r"\U0001F680-\U0001F6FF"  # transport & map
    r"\U0001F700-\U0001F77F"
    r"\U0001F780-\U0001F7FF"
    r"\U0001F800-\U0001F8FF"
    r"\U0001F900-\U0001F9FF"
    r"\U0001FA00-\U0001FA6F"
    r"\U0001FA70-\U0001FAFF"
    r"\U00002702-\U000027B0"
    r"\U000024C2-\U0001F251"
    r"]+",
    flags=re.UNICODE,
)


def phrase_pattern(phrase: str) -> "re.Pattern[str]":
    """Match a lexicon phrase as whole words, so "credit" does not fire on
    "accredited" and "urgent" does not fire on "insurgent". Edges that are
    punctuation ("make $", "$$$") are matched as-is."""
    left = r"(?<![a-z0-9])" if phrase[:1].isalnum() else ""
    right = r"(?![a-z0-9])" if phrase[-1:].isalnum() else ""
    return re.compile(left + re.escape(phrase) + right, flags=re.IGNORECASE)


def shouty_caps(text: str) -> Optional[str]:
    """Return a reason if `text` shouts, else None.

    Short acronyms are normal in B2B (SDR, CRM, ARR, GTM), so a single
    3-4 letter all-caps word does not count. Shouting is: an all-caps word
    of 5+ letters, two all-caps words in a row, or a line that is mostly
    capitals."""
    words = text.split()
    for i, word in enumerate(words):
        letters = re.sub(r"[^A-Za-z]", "", word)
        if len(letters) >= 5 and letters.isupper():
            return f"all-caps word '{letters}'"
        if len(letters) >= 3 and letters.isupper() and i + 1 < len(words):
            nxt = re.sub(r"[^A-Za-z]", "", words[i + 1])
            if len(nxt) >= 2 and nxt.isupper():
                return f"all-caps run '{letters} {nxt}'"
    letters = re.sub(r"[^A-Za-z]", "", text)
    if len(letters) >= 8 and sum(c.isupper() for c in letters) / len(letters) > 0.6:
        return "mostly capitals"
    return None


# ----------------------------------------------------------------------------
# Data shapes
# ----------------------------------------------------------------------------

@dataclass
class Flag:
    axis: str
    location: str  # "subject" | "body:line-N"
    pattern: str
    severity: str  # "critical" | "warning"


@dataclass
class AxisScore:
    axis: str
    score: int
    max_score: int
    flags: List[Flag] = field(default_factory=list)


@dataclass
class LintResult:
    total_score: int
    max_score: int
    verdict: str
    axes: List[AxisScore]
    flagged_lines: List[str] = field(default_factory=list)


# ----------------------------------------------------------------------------
# Axis scanners
# ----------------------------------------------------------------------------

def scan_trigger_words(subject: str, body: str) -> AxisScore:
    """25 points. -3 per trigger word (subject), -1 per body trigger."""
    score = 25
    flags: List[Flag] = []
    for word in ALL_TRIGGER_WORDS:
        pattern = phrase_pattern(word)
        if pattern.search(subject):
            score -= 3
            flags.append(Flag("trigger-words", "subject", word, "critical"))
        # Count body matches (cap one per word).
        if pattern.search(body):
            score -= 1
            flags.append(Flag("trigger-words", "body", word, "warning"))

    return AxisScore("trigger-words", max(0, score), 25, flags)


def scan_all_caps(subject: str, body: str) -> AxisScore:
    """15 points. -10 if the subject shouts (see shouty_caps), -1 per all-caps body line."""
    score = 15
    flags: List[Flag] = []

    reason = shouty_caps(subject)
    if reason:
        score -= 10
        flags.append(Flag("all-caps", "subject", reason, "critical"))

    for i, line in enumerate(body.splitlines(), start=1):
        # Skip lines with mostly punctuation / whitespace
        letters = re.sub(r"[^A-Za-z]", "", line)
        if len(letters) >= 5 and letters.isupper():
            score -= 1
            flags.append(Flag("all-caps", f"body:{i}", "line all caps", "warning"))

    return AxisScore("all-caps", max(0, score), 15, flags)


def scan_emoji(subject: str, body: str) -> AxisScore:
    """10 points. -10 for emoji in subject, -1 per emoji in body (max -5)."""
    score = 10
    flags: List[Flag] = []

    sub_matches = EMOJI_RE.findall(subject)
    if sub_matches:
        score -= 10
        flags.append(Flag("emoji", "subject", "".join(sub_matches), "critical"))

    body_matches = EMOJI_RE.findall(body)
    if body_matches:
        deduction = min(5, len(body_matches))
        score -= deduction
        flags.append(Flag("emoji", "body", "".join(body_matches), "warning"))

    return AxisScore("emoji", max(0, score), 10, flags)


def scan_clickbait(subject: str, body: str) -> AxisScore:
    """15 points. -8 per clickbait pattern in subject, -3 per body match."""
    score = 15
    flags: List[Flag] = []
    combined = f"{subject}\n{body}".lower()

    for pat in CLICKBAIT_PATTERNS:
        for match in re.finditer(pat, combined, flags=re.IGNORECASE):
            loc = "subject" if match.start() < len(subject) else "body"
            if loc == "subject":
                score -= 8
            else:
                score -= 3
            flags.append(Flag("clickbait", loc, match.group(), "critical"))

    return AxisScore("clickbait", max(0, score), 15, flags)


def scan_fake_thread(subject: str, body: str) -> AxisScore:
    """10 points. -10 if subject starts with Re:/Fwd: (since these can't be
    verified by the lint as legit, they're flagged for human review)."""
    score = 10
    flags: List[Flag] = []

    sub_lower = subject.lstrip().lower()
    for prefix in FAKE_THREAD_PREFIXES:
        if sub_lower.startswith(prefix):
            score = 0
            flags.append(Flag(
                "fake-thread",
                "subject",
                f"starts with '{prefix}' — bulk-sender rules require legitimate threading",
                "critical",
            ))
            break

    return AxisScore("fake-thread", score, 10, flags)


def scan_link_image_ratio(body: str) -> AxisScore:
    """25 points. Penalize multiple links + image-to-text imbalance."""
    score = 25
    flags: List[Flag] = []

    # Count URLs
    url_re = re.compile(r"https?://[^\s<>\"]+|www\.[^\s<>\"]+", flags=re.IGNORECASE)
    urls = url_re.findall(body)
    if len(urls) > 1:
        deduction = min(15, (len(urls) - 1) * 5)
        score -= deduction
        flags.append(Flag(
            "link-image-ratio", "body",
            f"{len(urls)} links (cold-email best practice: 1)",
            "warning",
        ))

    # Count images (loose detection)
    img_count = len(re.findall(r"<img\b|!\[", body, flags=re.IGNORECASE))
    text_chars = len(re.sub(r"<[^>]+>", "", body))
    if img_count > 0 and text_chars > 0:
        # Rough proxy: image bytes are not in the input, but each <img> reference
        # is treated as adding ~300 visual chars.
        approx_image_weight = img_count * 300
        ratio = approx_image_weight / (approx_image_weight + text_chars)
        if ratio > 0.40:
            score -= 10
            flags.append(Flag(
                "link-image-ratio", "body",
                f"image-to-text ratio ~{int(ratio * 100)}% (>40%)",
                "warning",
            ))

    return AxisScore("link-image-ratio", max(0, score), 25, flags)


# ----------------------------------------------------------------------------
# Orchestration
# ----------------------------------------------------------------------------

def lint(subject: str, body: str) -> LintResult:
    # Phone keyboards send curly apostrophes; the lexicon is written straight.
    subject = subject.replace("\u2019", "'")
    body = body.replace("\u2019", "'")
    axes = [
        scan_trigger_words(subject, body),
        scan_all_caps(subject, body),
        scan_emoji(subject, body),
        scan_clickbait(subject, body),
        scan_fake_thread(subject, body),
        scan_link_image_ratio(body),
    ]
    total = sum(a.score for a in axes)
    max_total = sum(a.max_score for a in axes)

    if total >= 90:
        verdict = "Ship"
    elif total >= 75:
        verdict = "Ship after fixes"
    elif total >= 60:
        verdict = "Rewrite"
    else:
        verdict = "Do not send"

    flagged_lines: List[str] = []
    for a in axes:
        for f in a.flags:
            flagged_lines.append(f"[{f.location}] {f.axis}: {f.pattern}")

    return LintResult(
        total_score=total,
        max_score=max_total,
        verdict=verdict,
        axes=axes,
        flagged_lines=flagged_lines,
    )


NEXT_OK = "Next: score the subject line (/cold-email:cold-email subject)."
NEXT_FIX = "Next: fix the lines above and run this again."

AXIS_FIX = {
    "trigger-words": "swap it for a plain word or cut it",
    "all-caps": "write it in sentence case",
    "emoji": "remove the emoji",
    "clickbait": "cut the hook; say the specific thing",
    "fake-thread": "drop the Re:/Fwd: prefix; there is no prior thread",
    "link-image-ratio": "keep one link at most and no images",
}


def fix_for(flag: Flag) -> str:
    return AXIS_FIX.get(flag.axis, "rewrite that line")


def next_step(result: LintResult) -> str:
    return NEXT_OK if result.total_score >= 75 else NEXT_FIX


def format_text(result: LintResult) -> str:
    lines = [
        f"# Spam Lint",
        f"",
        f"Score: {result.total_score}/{result.max_score} — {result.verdict}",
        f"",
        f"## Per-axis",
    ]
    for axis in result.axes:
        lines.append(f"  {axis.axis.ljust(20)} {axis.score}/{axis.max_score}")
    flags = [f for a in result.axes for f in a.flags]
    if flags:
        lines.append("")
        lines.append("## Flags")
        for f in flags:
            lines.append(f"- [{f.location}] {f.axis}: {f.pattern} → {fix_for(f)}")
    lines.append("")
    lines.append(next_step(result))
    return "\n".join(lines)


def format_json(result: LintResult) -> str:
    payload = {
        "score": result.total_score,
        "max_score": result.max_score,
        "verdict": result.verdict,
        "axes": [
            {
                "axis": a.axis,
                "score": a.score,
                "max": a.max_score,
                "flags": [dict(asdict(f), fix=fix_for(f)) for f in a.flags],
            }
            for a in result.axes
        ],
        "next": next_step(result),
    }
    return json.dumps(payload, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="example: python3 scripts/spam_word_lint.py --file examples/t1.email.md   # exit 0, Score: 100/100",
    )
    parser.add_argument("--file", default=None, help="Draft file: JSON object or plain-text email")
    parser.add_argument("--subject", default="", help="Email subject line")
    parser.add_argument("--body", default="", help="Email body")
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help='Read JSON {"subject":"","body":""} from stdin',
    )
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    if args.file and args.stdin:
        fail_input("pass --file or --stdin, not both")
    if args.file:
        draft = load_draft_file(args.file)
        subject, body = draft["subject"], draft["body"]
    elif args.stdin:
        payload = parse_json(read_stdin_text())
        subject = payload.get("subject", "")
        body = payload.get("body", "")
        if not isinstance(subject, str):
            subject = ""
        if not isinstance(body, str):
            body = ""
    else:
        subject = args.subject
        body = args.body

    if not subject and not body:
        print("No input. Provide --file, --subject + --body, or --stdin.", file=sys.stderr)
        return 2

    result = lint(subject, body)

    if args.json or args.format == "json":
        print(format_json(result))
    else:
        print(format_text(result))

    return 0 if result.total_score >= 75 else 1


if __name__ == "__main__":
    sys.exit(main())
