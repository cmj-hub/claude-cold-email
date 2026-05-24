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


# ----------------------------------------------------------------------------
# Lexicons
# ----------------------------------------------------------------------------

BUY_SIGNAL_PATTERNS = [
    (r"send (me )?(the |your )?(calendar|cal link|availability)", 0.50),
    (r"what (dates|times) work", 0.45),
    (r"let['']s (get|set up) (a |the )?(time|call|meeting|chat)", 0.40),
    (r"send (the |a )?(demo|walkthrough)", 0.35),
    (r"what['']s (the |your )?(price|pricing|cost)", 0.40),
    (r"can (you|we) (do|set up) (a |an )?(intro|introduction)", 0.40),
    (r"(book|schedule) (a |the )?(call|meeting|demo)", 0.45),
    (r"send (the |a )?(deck|proposal|case stud(y|ies)|one[- ]pager)", 0.30),
    (r"(decision[- ]?maker|economic buyer|approver)", 0.25),
    (r"(buy[- ]?signal|ready to (buy|move))", 0.40),
    (r"(my|our) calendar is (here|at)", 0.45),
    (r"(send|share) (the |an? )?intro", 0.30),
]

POSITIVE_PATTERNS = [
    (r"(tell|give) me (more|some more)", 0.30),
    (r"(this|that) (is|looks) (interesting|cool|relevant)", 0.30),
    (r"(curious|interested) (about|in)", 0.25),
    (r"how (does|do) (this|that|you|it) work", 0.25),
    (r"send (the |me |a )?(?:info|details|info on)", 0.25),
    (r"would love (to|the)", 0.25),
    (r"happy to (chat|connect|learn)", 0.30),
    (r"(yes|sure|sounds good|let me know more)", 0.25),
]

NEUTRAL_PATTERNS = [
    (r"not (the |a )?(right |great )?time", 0.40),
    (r"in (a few |several )?(months|quarters)", 0.35),
    (r"(q[1234]|next year|next quarter)", 0.30),
    (r"(circle back|reach out) (in|later|next)", 0.35),
    (r"send (me )?(some |more )?info", 0.20),  # mild — could be positive or neutral
    (r"keep me (in mind|posted)", 0.30),
    (r"(maybe |perhaps )(later|next)", 0.30),
]

NOT_INTERESTED_PATTERNS = [
    (r"(no |not )(thanks|thank you|interested)", 0.45),
    (r"stop (emailing|messaging|reaching out)", 0.55),
    (r"(remove|take) me (off|out of)", 0.55),
    (r"unsubscribe", 0.60),
    (r"(not a fit|not right for us)", 0.45),
    (r"(we|i) (have|use) (a |our )?(competitor|existing|vendor)", 0.40),
    (r"don['']t (email|message|reach out) (again|me)", 0.55),
    (r"how did you get my email", 0.35),
    (r"(stop|cease)( and desist)?", 0.50),
    (r"(this is |that['']s )?(spam|harassment)", 0.55),
]

AUTO_REPLY_PATTERNS = [
    r"out of (the )?office",
    r"\bOOO\b",
    r"auto[- ]?reply",
    r"i['']m currently (away|out|traveling)",
    r"i will be (out|away|traveling) (from|until)",
    r"limited (access to |)email",
    r"i['']ll (respond|reply|be back) (when|on|after)",
    r"thank you for your email\.? i (am|will be) (away|out)",
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
    body = body.strip()
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
    winning = scores[category]

    # Confidence: how dominant is the winner over the runner-up?
    sorted_scores = sorted(scores.values(), reverse=True)
    if sorted_scores[0] == 0:
        confidence = 0.0
        category = "neutral"  # nothing matched → default neutral
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
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as err:
                print(f"line {idx}: bad JSON: {err}", file=sys.stderr)
                continue
            body = obj.get("body", "")
            mins = obj.get("minutes_since_send")
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
        try:
            payload = json.load(sys.stdin)
            body = payload.get("body", "")
            mins = payload.get("minutes_since_send")
        except json.JSONDecodeError as err:
            print(f"Bad JSON on stdin: {err}", file=sys.stderr)
            return 2
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
