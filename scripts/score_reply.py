#!/usr/bin/env python3
"""
score_reply.py — Deterministic cold-email reply classifier.

Classifies replies into 5 categories: buy-signal | positive | neutral |
not-interested | auto-reply. Uses regex + feature engineering — no LLM,
no external services.

USAGE:
    python3 score_reply.py --body "..." [--minutes-since-send 27]
    python3 score_reply.py --stdin             # JSON {"body":"","minutes_since_send":N}
    python3 score_reply.py --batch path.jsonl  # one JSON object per line

EXIT CODES:
    0  success
    2  bad input

NO network calls. NO LLM. NO external libraries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Tuple, Optional, Iterable


MAX_INPUT_BYTES = 2_000_000


def fail_input(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def read_text(path: str) -> str:
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_BYTES + 1)
    except IsADirectoryError:
        fail_input(f"not a file: {path}")
    except FileNotFoundError:
        fail_input(f"file not found: {path}")
    except OSError:
        fail_input(f"cannot read file: {path}")
    if len(raw) > MAX_INPUT_BYTES:
        fail_input(f"file is too large: {path}")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        fail_input(f"file is not UTF-8 text: {path}")


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


def _as_text(value: object) -> str:
    return value if isinstance(value, str) else ""


def _as_minutes(value: object):
    if value is None or isinstance(value, bool):
        return None
    return value if isinstance(value, int) else None


# ----------------------------------------------------------------------------
# Lexicons
# ----------------------------------------------------------------------------

BUY_SIGNAL_PATTERNS = [
    (r"\bsend (me )?(the |your )?(calendar|cal link|availability)", 0.50),
    (r"\bwhat (dates|times|days) (work|suit)", 0.45),
    (r"\blet's (get|set up|find) (a |the |some )?(time|call|meeting|chat)", 0.40),
    (r"\bsend (the |a )?(demo|walkthrough)", 0.35),
    (r"\bwhat('s| is| are| does| do) (the |your )?(price|pricing|cost|rates?)\b", 0.40),
    (r"\b(how much (does|do|is|would)|what would it cost)", 0.40),
    (r"\b(pricing|price|quote)\b[^.?!]*\?", 0.25),
    (r"\bcan (you|we) (do|set up) (a |an )?(intro|introduction)", 0.40),
    (r"\b(book|schedule) (a |the )?(call|meeting|demo)", 0.45),
    (r"\bsend (the |a |me the |me a )?(deck|proposal|case stud(y|ies)|one[- ]pager)", 0.30),
    (r"\b(decision[- ]?maker|economic buyer|approver)", 0.25),
    (r"\bready to (buy|move|sign|start)\b", 0.40),
    (r"\b(my|our) calendar is (here|at)", 0.45),
    (r"\b(send|share) (the |an? )?intro\b", 0.30),
    (r"\b(monday|tuesday|wednesday|thursday|friday) (works|is good|is fine|at \d)", 0.35),
]

POSITIVE_PATTERNS = [
    (r"\b(tell|give) me (more|some more)\b", 0.30),
    (r"\b(this|that) (is|looks|sounds) (interesting|cool|relevant|useful)", 0.30),
    (r"\b(curious|interested) (about|in)\b", 0.25),
    (r"\bhow (does|do) (this|that|you|it) work", 0.25),
    (r"\bsend (the |me |a )?(info|details|info on)\b", 0.25),
    (r"\bwould love (to|the)\b", 0.25),
    (r"\bhappy to (chat|connect|learn|talk)\b", 0.30),
    (r"\b(yes|sure|sounds good|let me know more)\b", 0.25),
]

NEUTRAL_PATTERNS = [
    (r"\bnot (the |a )?(right |great |good )?time\b", 0.40),
    (r"\bnot right now\b", 0.40),
    (r"\bin (a few |several |a couple of )?(months|quarters)\b", 0.35),
    (r"\b(q[1-4]|next year|next quarter)\b", 0.30),
    (r"\b(circle back|reach out|follow up) (in|later|next)\b", 0.35),
    (r"\bsend (me )?(some |more )?info\b", 0.20),  # mild — could be positive or neutral
    (r"\bkeep me (in mind|posted)\b", 0.30),
    (r"\b(maybe |perhaps )(later|next)\b", 0.30),
    (r"\b(who is this|who are you|what is this about)\b", 0.30),
    (r"\b(forward(ed|ing)?|loop(ed|ing)? in|right person (is|would be))\b", 0.25),
]

NOT_INTERESTED_PATTERNS = [
    (r"\b(no|not) (thanks|thank you|interested)\b", 0.45),
    (r"\bstop (emailing|messaging|reaching out|contacting)\b", 0.55),
    (r"\b(remove|take) me (off|out of|from)\b", 0.55),
    (r"\bunsubscribe\b", 0.60),
    (r"\b(not a fit|not right for us|not relevant)\b", 0.45),
    (r"\b(we|i) (already )?(have|use|work with) (a |an |our )?(competitor|existing|vendor|agency|partner|solution)\b", 0.40),
    (r"\bwe('re| are) (all set|covered|good)\b", 0.40),
    (r"\bdon't (email|message|contact|reach out to) me\b", 0.55),
    (r"\bdon't (email|message|contact|reach out) again\b", 0.55),
    (r"\bhow did you get my (email|address)\b", 0.35),
    (r"\bcease and desist\b", 0.55),
    (r"^\W*stop\W*$", 0.55),
    (r"\b(this is |that's )?(spam|harassment)\b", 0.55),
]

AUTO_REPLY_PATTERNS = [
    r"\bout of (the )?office\b",
    r"\bOOO\b",
    r"\bauto[- ]?(reply|response|responder)\b",
    r"\bi'm currently (away|out|traveling|on leave)\b",
    r"\bi am currently (away|out|traveling|on leave)\b",
    r"\bi will be (out|away|traveling) (from|until|through)\b",
    r"\blimited (access to )?email\b",
    r"\bi'll (respond|reply|be back) (when|on|after|upon)\b",
    r"\bthank you for your email\.? i (am|will be) (away|out)\b",
    r"\b(i am|i'm|is) no longer (with|at|employed)\b",
]


# ----------------------------------------------------------------------------
# Data shapes
# ----------------------------------------------------------------------------

@dataclass
class FeatureContribution:
    pattern: str
    category: str
    weight: float


@dataclass
class ReplyScore:
    category: str  # buy-signal | positive | neutral | not-interested | auto-reply
    confidence: float
    category_scores: Dict[str, float]
    contributions: List[FeatureContribution] = field(default_factory=list)
    length_chars: int = 0
    question_count: int = 0
    minutes_since_send: Optional[int] = None
    needs_review: bool = False


# ----------------------------------------------------------------------------
# Classifier
# ----------------------------------------------------------------------------

def detect_auto_reply(body: str) -> bool:
    for pat in AUTO_REPLY_PATTERNS:
        if re.search(pat, body, flags=re.IGNORECASE):
            return True
    return False


def score_category(body: str, patterns: List[Tuple[str, float]], category: str) -> Tuple[float, List[FeatureContribution]]:
    total = 0.0
    contributions: List[FeatureContribution] = []
    for pat, weight in patterns:
        if re.search(pat, body, flags=re.IGNORECASE):
            total += weight
            contributions.append(FeatureContribution(pat, category, weight))
    return total, contributions


def time_adjustment(minutes: Optional[int]) -> Dict[str, float]:
    """Time-to-reply produces small adjustments per category."""
    adj = {"buy-signal": 0.0, "positive": 0.0, "neutral": 0.0, "not-interested": 0.0}
    if minutes is None:
        return adj
    if minutes < 15:
        # Likely auto-reply; small neutral bump (will be caught elsewhere if real auto)
        adj["neutral"] += 0.05
    elif minutes < 60:
        # Immediate engaged reply
        adj["buy-signal"] += 0.10
        adj["positive"] += 0.05
    elif minutes < 1440:  # <24h
        adj["positive"] += 0.05
    # >24h adds nothing
    return adj


def length_adjustment(body: str) -> Dict[str, float]:
    """Length signal — short = often not-interested or short positive."""
    adj = {"buy-signal": 0.0, "positive": 0.0, "neutral": 0.0, "not-interested": 0.0}
    chars = len(body.strip())
    if chars < 20:
        # 1-2 word replies — slight bump to not-interested
        adj["not-interested"] += 0.10
    elif chars > 200:
        # Substantive reply — bump positive + buy-signal
        adj["positive"] += 0.05
        adj["buy-signal"] += 0.05
    return adj


def classify(body: str, minutes_since_send: Optional[int] = None) -> ReplyScore:
    # Phone keyboards send curly apostrophes; the patterns are written straight.
    body = body.replace("\u2019", "'").strip()
    length = len(body)
    qcount = body.count("?")

    if detect_auto_reply(body):
        return ReplyScore(
            category="auto-reply",
            confidence=1.0,
            category_scores={"auto-reply": 1.0},
            length_chars=length,
            question_count=qcount,
            minutes_since_send=minutes_since_send,
            needs_review=False,
        )

    scores: Dict[str, float] = {
        "buy-signal": 0.0,
        "positive": 0.0,
        "neutral": 0.0,
        "not-interested": 0.0,
    }
    all_contribs: List[FeatureContribution] = []

    for (patterns, name) in [
        (BUY_SIGNAL_PATTERNS, "buy-signal"),
        (POSITIVE_PATTERNS, "positive"),
        (NEUTRAL_PATTERNS, "neutral"),
        (NOT_INTERESTED_PATTERNS, "not-interested"),
    ]:
        s, c = score_category(body, patterns, name)
        scores[name] += s
        all_contribs.extend(c)

    # Time + length adjustments
    for cat, delta in time_adjustment(minutes_since_send).items():
        scores[cat] += delta
    for cat, delta in length_adjustment(body).items():
        scores[cat] += delta

    # Pick winner
    category = max(scores, key=lambda k: scores[k])

    # Confidence: how dominant is the winner over the runner-up?
    sorted_scores = sorted(scores.values(), reverse=True)
    if not all_contribs:
        # Length and timing alone never decide a category. "Who is this?"
        # or "ok" goes to a human, not to the suppression list.
        confidence = 0.0
        category = "neutral"
    else:
        runner_up = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
        margin = sorted_scores[0] - runner_up
        confidence = min(1.0, sorted_scores[0] + margin * 0.5)

    needs_review = confidence < 0.6

    return ReplyScore(
        category=category,
        confidence=round(confidence, 2),
        category_scores={k: round(v, 2) for k, v in scores.items()},
        contributions=all_contribs,
        length_chars=length,
        question_count=qcount,
        minutes_since_send=minutes_since_send,
        needs_review=needs_review,
    )


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------

def format_text(result: ReplyScore) -> str:
    lines = [
        f"# Reply scoring",
        f"",
        f"Length: {result.length_chars} chars",
        f"Questions: {result.question_count}",
    ]
    if result.minutes_since_send is not None:
        lines.append(f"Time-to-reply: {result.minutes_since_send} min")
    lines.append("")
    lines.append(f"## Classification")
    lines.append(f"Category: **{result.category}** (confidence: {result.confidence})")
    if result.needs_review:
        lines.append(f"⚠️  Low confidence — flagged for human review")
    lines.append("")
    lines.append(f"## Per-category scores")
    for cat, sc in result.category_scores.items():
        lines.append(f"  {cat.ljust(20)} {sc}")
    if result.contributions:
        lines.append("")
        lines.append("## Why")
        for c in result.contributions:
            lines.append(f"  [{c.category}] +{c.weight} from pattern: {c.pattern}")
    return "\n".join(lines)


def format_json(result: ReplyScore) -> str:
    return json.dumps(asdict(result), indent=2)


def iter_batch(path: str) -> Iterable[Tuple[Optional[str], ReplyScore]]:
    """Yield (line_id, ReplyScore) for each line in a JSONL file."""
    text = read_text(path)
    for idx, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            print(f"line {idx}: bad JSON", file=sys.stderr)
            continue
        if not isinstance(obj, dict):
            print(f"line {idx}: JSON must be an object", file=sys.stderr)
            continue
        body = _as_text(obj.get("body", ""))
        mins = _as_minutes(obj.get("minutes_since_send"))
        label = obj.get("id") or obj.get("sender") or str(idx)
        yield label, classify(body, mins)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body", default="", help="Reply body")
    parser.add_argument(
        "--minutes-since-send",
        type=int,
        default=None,
        help="Minutes since the original send",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help='Read JSON {"body":"","minutes_since_send":N} from stdin',
    )
    parser.add_argument(
        "--batch",
        default=None,
        help="JSONL file with one reply per line",
    )
    parser.add_argument(
        "--format",
        default="text",
        choices=["text", "json"],
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    if args.batch:
        results = []
        for label, score in iter_batch(args.batch):
            results.append({"id": label, **asdict(score)})
        if args.format == "json":
            print(json.dumps(results, indent=2))
        else:
            print(f"# Batch reply scoring — {len(results)} replies")
            print("")
            print(f"{'#'.ljust(4)} {'ID'.ljust(36)} {'Category'.ljust(18)} {'Conf'.ljust(6)} Review?")
            for i, r in enumerate(results, start=1):
                print(
                    f"{str(i).ljust(4)} {str(r['id'])[:36].ljust(36)} "
                    f"{r['category'].ljust(18)} {str(r['confidence']).ljust(6)} "
                    f"{'⚠️' if r['needs_review'] else '✓'}"
                )
        return 0

    if args.stdin:
        payload = parse_json(read_stdin_text())
        body = _as_text(payload.get("body", ""))
        mins = _as_minutes(payload.get("minutes_since_send"))
    else:
        body = args.body
        mins = args.minutes_since_send

    if not body:
        print("No body provided. Use --body, --stdin, or --batch.", file=sys.stderr)
        return 2

    result = classify(body, mins)
    if args.format == "json":
        print(format_json(result))
    else:
        print(format_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
