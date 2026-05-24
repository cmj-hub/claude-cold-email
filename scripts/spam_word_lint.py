#!/usr/bin/env python3
"""
spam_word_lint.py — Deterministic spam-trigger scanner for cold email.

Scans subject + body against a 200+ word spam-trigger lexicon, plus
structural patterns (ALL CAPS, emoji, fake threading, clickbait,
link/image ratio). Returns a 0-100 deliverability-risk score with
line-by-line flags.

Zero dependencies. Python 3.8+.

USAGE:
    python3 spam_word_lint.py --subject "Re: URGENT" --body "..." [--format json|text]
    python3 spam_word_lint.py --stdin   # read JSON {"subject":"","body":""} from stdin

EXIT CODES:
    0   score >= 75 (ship or ship-after-fix)
    1   score < 75  (rewrite or do-not-send)
    2   bad input

NO network calls. NO LLM. NO external libraries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple


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
    "guaranteed income", "lifetime", "100% free", "100% guaranteed",
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
    r"you won['']t believe",
    r"this one (trick|secret|tip|hack)",
    r"doctors hate",
    r"what \w+ don['']t want you to know",
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
    sub_lower = subject.lower()
    body_lower = body.lower()

    for word in ALL_TRIGGER_WORDS:
        if word in sub_lower:
            score -= 3
            flags.append(Flag("trigger-words", "subject", word, "critical"))
        # Count body matches (cap one per word).
        if word in body_lower:
            score -= 1
            flags.append(Flag("trigger-words", "body", word, "warning"))

    return AxisScore("trigger-words", max(0, score), 25, flags)


def scan_all_caps(subject: str, body: str) -> AxisScore:
    """15 points. -10 if subject has CAPS sequences ≥3 chars, -1 per body line."""
    score = 15
    flags: List[Flag] = []

    if re.search(r"[A-Z]{3,}", subject):
        score -= 10
        flags.append(Flag("all-caps", "subject", "≥3 consecutive caps", "critical"))

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
    if result.flagged_lines:
        lines.append("")
        lines.append("## Flags")
        for f in result.flagged_lines:
            lines.append(f"  - {f}")
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
                "flags": [asdict(f) for f in a.flags],
            }
            for a in result.axes
        ],
    }
    return json.dumps(payload, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--subject", default="", help="Email subject line")
    parser.add_argument("--body", default="", help="Email body")
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

    if args.stdin:
        try:
            payload = json.load(sys.stdin)
            subject = payload.get("subject", "")
            body = payload.get("body", "")
        except json.JSONDecodeError as err:
            print(f"Bad JSON on stdin: {err}", file=sys.stderr)
            return 2
    else:
        subject = args.subject
        body = args.body

    if not subject and not body:
        print("No input. Provide --subject + --body, or --stdin.", file=sys.stderr)
        return 2

    result = lint(subject, body)

    if args.format == "json":
        print(format_json(result))
    else:
        print(format_text(result))

    return 0 if result.total_score >= 75 else 1


if __name__ == "__main__":
    sys.exit(main())
