#!/usr/bin/env python3
"""
score_list.py — Deterministic prospect-list scorer for cold email.

Scores a CSV or JSONL prospect list 0-100 across six axes and names the
rows to remove and why:

    dedup             20   same email / same LinkedIn URL / same person
    role-fit          25   role vs brand-config icp.role_targets
    signal-freshness  20   signal_date age: <=14d full, 15-30d half, >30d none
    email-validity    15   shape, free-mail domain, role account, plus-address
    exclusion         10   row text vs brand-config icp.exclusion_criteria
    company-stage     10   row `stage` vs the stage named in icp.segment

An axis with no data to judge (no brand-config, no signal_date column, no
stage column) is reported as "n/a" and left out of the score instead of
being counted as a pass.

Score = half the axis points (as a share of the axes that could be judged)
plus half the share of rows that survive cleaning.

Zero dependencies. Python 3.8+. No network calls. No LLM.

USAGE:
    python3 score_list.py --input prospects.csv
    python3 score_list.py --input prospects.jsonl --brand-config brand-config.json
    python3 score_list.py --input prospects.csv --write      # also writes
        prospects.cleaned.csv and prospects.removed.csv next to the input

Columns (header names are case-insensitive): email (required), first_name,
last_name, role, company, signal, signal_date (YYYY-MM-DD), linkedin_url,
stage, industry.

EXIT CODES:
    0   score >= 75 (ship the list)
    1   score < 75  (clean before sending)
    2   bad input
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple


MAX_INPUT_BYTES = 20_000_000

AXES = [
    ("dedup", 20),
    ("role-fit", 25),
    ("signal-freshness", 20),
    ("email-validity", 15),
    ("exclusion", 10),
    ("company-stage", 10),
]

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")

FREE_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "ymail.com", "outlook.com",
    "hotmail.com", "live.com", "msn.com", "proton.me", "protonmail.com",
    "icloud.com", "me.com", "mac.com", "aol.com", "gmx.com", "gmx.net",
    "mail.com", "zoho.com", "yandex.com", "hey.com", "fastmail.com",
}

ROLE_ACCOUNTS = {
    "info", "sales", "support", "hello", "contact", "marketing", "hr",
    "jobs", "careers", "admin", "office", "team", "billing", "help",
    "noreply", "no-reply", "enquiries", "inquiries", "press", "media",
}

# Applied to both the row's role and the brand-config targets before matching.
ROLE_SYNONYMS = [
    (r"\bvice[- ]president\b", "vp"),
    (r"\bsenior vice president\b|\bsvp\b|\bevp\b", "vp"),
    (r"\bchief revenue officer\b", "cro"),
    (r"\bchief marketing officer\b", "cmo"),
    (r"\bchief executive officer\b", "ceo"),
    (r"\bchief operating officer\b", "coo"),
    (r"\bchief technology officer\b", "cto"),
    (r"\bchief financial officer\b", "cfo"),
    (r"\bdemand generation\b", "demand gen"),
    (r"\brevenue operations\b", "revops"),
    (r"\brev ops\b", "revops"),
    (r"\bsales development\b", "sdr"),
    (r"\bhead of\b", "head"),
    (r"&", " and "),
]

STAGE_RE = re.compile(
    r"\b(pre[- ]?seed|seed|series[- ]?[a-f]\+?|growth|public|bootstrapped)\b",
    re.IGNORECASE,
)


def fail_input(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------

def read_text(path: Path) -> str:
    try:
        if not path.is_file():
            fail_input(f"cannot read {path.name}")
        if path.stat().st_size > MAX_INPUT_BYTES:
            fail_input(f"{path.name} is too large")
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        fail_input(f"{path.name} is not UTF-8 text")
    except OSError:
        fail_input(f"cannot read {path.name}")
    return ""  # unreachable


def load_rows(path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    """Return (rows, original header order). Keys are lower-cased."""
    text = read_text(path)
    if path.suffix.lower() in (".jsonl", ".ndjson"):
        rows: List[Dict[str, str]] = []
        header: List[str] = []
        for n, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                fail_input(f"line {n}: bad JSON")
            if not isinstance(obj, dict):
                fail_input(f"line {n}: JSON must be an object")
            row = {str(k).strip().lower(): "" if v is None else str(v).strip() for k, v in obj.items()}
            for k in row:
                if k not in header:
                    header.append(k)
            rows.append(row)
        return rows, header

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        fail_input("CSV has no header row")
    header = [h.strip().lower() for h in reader.fieldnames]
    rows = []
    for raw in reader:
        row = {}
        for k, v in raw.items():
            if k is None:
                continue  # extra cells beyond the header
            row[k.strip().lower()] = (v or "").strip() if isinstance(v, str) else ""
        rows.append(row)
    return rows, header


def load_brand_config(path: Optional[Path]) -> dict:
    if path is None:
        return {}
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError:
        fail_input(f"{path.name} is not valid JSON")
    if not isinstance(data, dict):
        fail_input(f"{path.name} must be a JSON object")
    return data


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------

def norm_role(text: str) -> str:
    out = " " + text.lower() + " "
    for pat, repl in ROLE_SYNONYMS:
        out = re.sub(pat, repl, out)
    out = re.sub(r"[^a-z0-9 ]+", " ", out)
    return " ".join(w for w in out.split() if w not in ("of", "the", "and", "for"))


def role_matches(role: str, targets: List[str]) -> bool:
    words = set(norm_role(role).split())
    for target in targets:
        need = set(norm_role(target).split())
        if need and need <= words:
            return True
    return False


def norm_stage(text: str) -> List[str]:
    return sorted({re.sub(r"[- ]", "", m.lower()) for m in STAGE_RE.findall(text)})


def parse_date(text: str) -> Optional[dt.date]:
    text = text.strip()
    if not text:
        return None
    try:
        return dt.date.fromisoformat(text[:10])
    except ValueError:
        return None


def exclusion_keywords(criteria: List[str]) -> List[Tuple[str, str]]:
    """'Government/regulated industries' -> [('government', crit), ('regulated industries', crit)].
    Text in parentheses is a note for humans, not a match term."""
    out = []
    for crit in criteria:
        if not isinstance(crit, str):
            continue
        head = re.sub(r"\(.*?\)", "", crit).strip().lower()
        for part in re.split(r"[/,;]| or ", head):
            part = part.strip()
            if len(part) >= 3:
                out.append((part, crit))
    return out


# ----------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------

@dataclass
class RowIssue:
    row: int  # 1-based data row (header excluded)
    email: str
    axis: str
    action: str  # remove | warn
    reason: str


@dataclass
class AxisResult:
    axis: str
    max_score: int
    score: Optional[int]  # None = n/a
    issues: int
    note: str = ""


@dataclass
class ListResult:
    rows: int
    score: int
    verdict: str
    axes: List[AxisResult]
    remove: List[RowIssue] = field(default_factory=list)
    warn: List[RowIssue] = field(default_factory=list)


def score_rows(rows: List[Dict[str, str]], header: List[str], cfg: dict, today: dt.date) -> ListResult:
    icp = cfg.get("icp") if isinstance(cfg.get("icp"), dict) else {}
    targets = [t for t in icp.get("role_targets", []) if isinstance(t, str)] if isinstance(icp.get("role_targets"), list) else []
    criteria = icp.get("exclusion_criteria", []) if isinstance(icp.get("exclusion_criteria"), list) else []
    segment = icp.get("segment", "") if isinstance(icp.get("segment"), str) else ""

    issues: List[RowIssue] = []
    bad: Dict[str, set] = {name: set() for name, _ in AXES}
    n = len(rows)

    def flag(i: int, axis: str, action: str, reason: str) -> None:
        issues.append(RowIssue(i + 1, rows[i].get("email", ""), axis, action, reason))
        if action == "remove" or axis in ("signal-freshness", "company-stage"):
            bad[axis].add(i)

    # Dedup ---------------------------------------------------------------
    seen_email: Dict[str, int] = {}
    seen_li: Dict[str, int] = {}
    seen_person: Dict[Tuple[str, str, str], int] = {}
    for i, r in enumerate(rows):
        email = r.get("email", "").lower()
        if email and email in seen_email:
            flag(i, "dedup", "remove", f"duplicate of row {seen_email[email] + 1} (same email)")
            continue
        if email:
            seen_email[email] = i
        li = r.get("linkedin_url", "").lower().rstrip("/").split("?")[0]
        if li:
            if li in seen_li:
                j = seen_li[li]
                # Keep whichever row has the fresher signal.
                di, dj = parse_date(r.get("signal_date", "")), parse_date(rows[j].get("signal_date", ""))
                if di and dj and di > dj:
                    flag(j, "dedup", "remove", f"duplicate of row {i + 1} (same LinkedIn URL, older signal)")
                    seen_li[li] = i
                else:
                    flag(i, "dedup", "remove", f"duplicate of row {j + 1} (same LinkedIn URL)")
                continue
            seen_li[li] = i
        person = (r.get("first_name", "").lower(), r.get("last_name", "").lower(), r.get("company", "").lower())
        if all(person):
            if person in seen_person:
                flag(i, "dedup", "warn", f"same name + company as row {seen_person[person] + 1} — check by hand")
            else:
                seen_person[person] = i

    # Email validity ------------------------------------------------------
    for i, r in enumerate(rows):
        email = r.get("email", "")
        if not email:
            flag(i, "email-validity", "remove", "no email")
            continue
        if not EMAIL_RE.match(email):
            flag(i, "email-validity", "remove", "malformed email")
            continue
        local, domain = email.lower().rsplit("@", 1)
        if domain in FREE_EMAIL_DOMAINS:
            flag(i, "email-validity", "remove", f"free-mail domain ({domain}) on a B2B list")
        elif local.split("+")[0] in ROLE_ACCOUNTS:
            flag(i, "email-validity", "remove", f"role account ({local}@)")
        elif "+" in local:
            flag(i, "email-validity", "warn", "plus-address — confirm it is the person's real inbox")

    # Role fit ------------------------------------------------------------
    role_note = ""
    if not targets:
        role_note = "no icp.role_targets in brand-config"
    elif "role" not in header:
        role_note = "no role column"
    else:
        for i, r in enumerate(rows):
            role = r.get("role", "")
            if not role:
                flag(i, "role-fit", "warn", "no role — cannot check ICP fit")
                bad["role-fit"].add(i)
            elif not role_matches(role, targets):
                flag(i, "role-fit", "remove", f"role '{role}' is outside icp.role_targets")

    # Signal freshness ----------------------------------------------------
    fresh_note = ""
    fresh_points = 0.0
    if "signal_date" not in header:
        fresh_note = "no signal_date column"
    else:
        for i, r in enumerate(rows):
            raw = r.get("signal_date", "")
            d = parse_date(raw)
            if d is None:
                flag(i, "signal-freshness", "warn", "no signal date" if not raw else f"unreadable signal_date '{raw}' (use YYYY-MM-DD)")
                continue
            age = (today - d).days
            if age < 0:
                flag(i, "signal-freshness", "warn", f"signal_date {raw} is in the future")
            elif age <= 14:
                fresh_points += 1
            elif age <= 30:
                fresh_points += 0.5
                issues.append(RowIssue(i + 1, r.get("email", ""), "signal-freshness", "warn",
                                       f"signal is {age} days old — re-verify before sending"))
            else:
                flag(i, "signal-freshness", "remove", f"signal is {age} days old (stale past 30)")

    # Exclusion -----------------------------------------------------------
    excl_note = ""
    keywords = exclusion_keywords(criteria)
    if not keywords:
        excl_note = "no icp.exclusion_criteria in brand-config"
    else:
        fields = [h for h in header if h in ("company", "industry", "stage", "segment", "notes", "signal", "tags")]
        for i, r in enumerate(rows):
            hay = " ".join(r.get(h, "") for h in fields).lower()
            for kw, crit in keywords:
                if re.search(r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])", hay):
                    flag(i, "exclusion", "remove", f"matches exclusion '{crit}'")
                    break

    # Company stage -------------------------------------------------------
    stage_note = ""
    icp_stages = norm_stage(segment)
    if not icp_stages:
        stage_note = "icp.segment names no funding stage"
    elif "stage" not in header:
        stage_note = "no stage column"
    else:
        for i, r in enumerate(rows):
            row_stages = norm_stage(r.get("stage", ""))
            if not row_stages:
                flag(i, "company-stage", "warn", "no recognisable stage")
            elif not set(row_stages) & set(icp_stages):
                flag(i, "company-stage", "warn", f"stage '{r.get('stage')}' outside ICP ({', '.join(icp_stages)})")

    # Axis scores ---------------------------------------------------------
    notes = {
        "role-fit": role_note,
        "signal-freshness": fresh_note,
        "exclusion": excl_note,
        "company-stage": stage_note,
    }
    axes: List[AxisResult] = []
    for name, max_score in AXES:
        note = notes.get(name, "")
        if note or n == 0:
            axes.append(AxisResult(name, max_score, None, 0, note or "empty list"))
            continue
        if name == "signal-freshness":
            share = fresh_points / n
        else:
            share = (n - len(bad[name])) / n
        axes.append(AxisResult(name, max_score, int(round(max_score * share)), len(bad[name])))

    scored = [a for a in axes if a.score is not None]
    possible = sum(a.max_score for a in scored)
    axis_pct = sum(a.score for a in scored) / possible * 100 if possible else 0.0
    # Axis points alone forgive a list where most rows fail a different axis
    # each, so half the score is simply the share of rows that survive.
    removed_rows = {it.row for it in issues if it.action == "remove"}
    keep_pct = (n - len(removed_rows)) / n * 100 if n else 0.0
    score = int(round(0.5 * axis_pct + 0.5 * keep_pct))

    if score >= 90:
        verdict = "Ship the list"
    elif score >= 75:
        verdict = "Ship after removing the flagged rows"
    elif score >= 60:
        verdict = "Clean and re-pull signals before sending"
    else:
        verdict = "Rebuild the list — targeting is off"

    # One removal reason per row (first one found), warnings kept in full.
    remove: Dict[int, RowIssue] = {}
    for it in issues:
        if it.action == "remove" and it.row not in remove:
            remove[it.row] = it
    warn = [it for it in issues if it.action == "warn" and it.row not in remove]

    return ListResult(n, score, verdict, axes, sorted(remove.values(), key=lambda x: x.row), warn)


# ----------------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------------

def format_text(name: str, res: ListResult) -> str:
    lines = [
        f"# List Quality — {name}",
        "",
        f"Score: {res.score}/100 — {res.verdict}",
        f"Rows: {res.rows} | remove: {len(res.remove)} | keep: {res.rows - len(res.remove)}",
        "",
        "## Per-axis",
    ]
    for a in res.axes:
        if a.score is None:
            lines.append(f"  {a.axis.ljust(18)} n/a      ({a.note})")
        else:
            lines.append(f"  {a.axis.ljust(18)} {str(a.score).rjust(2)}/{a.max_score}    {a.issues} row(s) flagged")
    if res.remove:
        lines += ["", "## Rows to remove"]
        for it in res.remove:
            lines.append(f"  row {it.row}: {it.email or '(no email)'} — {it.reason}")
    if res.warn:
        lines += ["", "## Check by hand"]
        for it in res.warn:
            lines.append(f"  row {it.row}: {it.email or '(no email)'} — {it.reason}")
    return "\n".join(lines)


def write_split(path: Path, rows: List[Dict[str, str]], header: List[str], res: ListResult) -> Tuple[Path, Path]:
    removed_rows = {it.row: it.reason for it in res.remove}
    stem = path.with_suffix("")
    cleaned_path = Path(f"{stem}.cleaned.csv")
    removed_path = Path(f"{stem}.removed.csv")
    with cleaned_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        for i, r in enumerate(rows, start=1):
            if i not in removed_rows:
                w.writerow(r)
    with removed_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header + ["removal_reason"], extrasaction="ignore")
        w.writeheader()
        for i, r in enumerate(rows, start=1):
            if i in removed_rows:
                w.writerow(dict(r, removal_reason=removed_rows[i]))
    return cleaned_path, removed_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="Prospect list (.csv or .jsonl)")
    parser.add_argument("--brand-config", default=None, help="Path to brand-config.json (enables role / exclusion / stage axes)")
    parser.add_argument("--today", default=None, help="Override today's date (YYYY-MM-DD) for signal age")
    parser.add_argument("--write", action="store_true", help="Write <input>.cleaned.csv and <input>.removed.csv")
    parser.add_argument("--format", default="text", choices=["text", "json"])
    args = parser.parse_args()

    today = dt.date.today()
    if args.today:
        parsed = parse_date(args.today)
        if parsed is None:
            fail_input("--today must be YYYY-MM-DD")
        today = parsed

    path = Path(args.input)
    rows, header = load_rows(path)
    if "email" not in header:
        fail_input("list needs an 'email' column")
    cfg = load_brand_config(Path(args.brand_config) if args.brand_config else None)

    res = score_rows(rows, header, cfg, today)

    if args.format == "json":
        print(json.dumps(asdict(res), indent=2))
    else:
        print(format_text(path.name, res))

    if args.write:
        cleaned, removed = write_split(path, rows, header, res)
        print(f"\nWrote {cleaned} and {removed}", file=sys.stderr)

    return 0 if res.score >= 75 else 1


if __name__ == "__main__":
    sys.exit(main())
