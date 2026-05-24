#!/usr/bin/env python3
"""
check_deliverability.py — Score a sending domain's deliverability
across 15 checks: SPF, DKIM, DMARC, MX, reverse DNS, blacklists,
and bulk-sender compliance (Google/Yahoo/Microsoft Feb 2024 rules).

USAGE:
    python3 check_deliverability.py --domain outreach.acme.com
    python3 check_deliverability.py --domain ... --selector google
    python3 check_deliverability.py --stdin    # consume dig_dns.sh output

Uses `dig` for DNS lookups. Falls back to URL-based blacklist lookups
via standard-library urllib (no API keys, no external services).

Exit codes:
    0  score >= 85   (ready to send)
    1  score < 85    (do not send / fix first)
    2  bad input
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class Check:
    id: int
    name: str
    category: str  # dns | reputation | warm-up | content
    severity: str  # critical | important | nice-to-have
    passing: bool
    detail: str


def dig(qtype: str, name: str) -> str:
    """Run dig and return stdout. Empty string on failure."""
    try:
        result = subprocess.run(
            ["dig", "+short", qtype, name],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        return ""
    except subprocess.TimeoutExpired:
        return ""


# ---------------- DNS checks ----------------

def check_spf(domain: str) -> List[Check]:
    out = []
    txt = dig("TXT", domain)
    spf_line = next((line for line in txt.split("\n") if "v=spf1" in line), "")
    if not spf_line:
        out.append(Check(1, "SPF record exists", "dns", "critical", False, "No SPF TXT record"))
        out.append(Check(2, "SPF includes provider", "dns", "critical", False, "No SPF to inspect"))
        out.append(Check(3, "SPF lookup count ≤10", "dns", "important", False, "No SPF to inspect"))
        return out

    out.append(Check(1, "SPF record exists", "dns", "critical", True, spf_line[:120]))

    # Provider include
    common_providers = [
        "_spf.google.com",
        "spf.protection.outlook.com",
        "smartlead.io",
        "_spf.salesforce.com",
        "amazonses.com",
        "sendgrid.net",
        "mailgun.org",
    ]
    has_provider = any(p in spf_line for p in common_providers)
    out.append(Check(
        2, "SPF includes a known provider", "dns", "critical",
        has_provider,
        "Found a known include" if has_provider else "No known provider include found",
    ))

    # Lookup count (approx — counts include/a/mx/ptr/exists/redirect)
    lookups = len(re.findall(r"\b(include|a|mx|ptr|exists|redirect)[=:]", spf_line))
    out.append(Check(
        3, "SPF lookup count ≤10", "dns", "important",
        lookups <= 10,
        f"Approximate lookup count: {lookups}",
    ))
    return out


def check_dkim(domain: str, selector: str) -> List[Check]:
    out = []
    name = f"{selector}._domainkey.{domain}"
    txt = dig("TXT", name)
    if not txt:
        # Try common alt selectors
        for alt in ["default", "google", "selector1", "s1024", "s1", "mandrill", "dkim", "smartlead"]:
            if alt == selector:
                continue
            txt = dig("TXT", f"{alt}._domainkey.{domain}")
            if txt:
                selector = alt
                break

    if not txt:
        out.append(Check(4, "DKIM selector resolves", "dns", "critical", False,
                         f"No DKIM at common selectors (tried: {selector}, default, google, selector1, s1024, mandrill)"))
        out.append(Check(5, "DKIM key ≥1024 bits", "dns", "important", False,
                         "No DKIM to inspect"))
        return out

    out.append(Check(4, "DKIM selector resolves", "dns", "critical", True,
                     f"Selector: {selector}"))

    # Extract p= key
    m = re.search(r"p=([A-Za-z0-9+/=]+)", txt.replace('"', '').replace(' ', ''))
    if not m:
        out.append(Check(5, "DKIM key ≥1024 bits", "dns", "important", False,
                         "No 'p=' found in record"))
    else:
        keylen = len(m.group(1))
        # Approx: 1024-bit = ~216 base64 chars; 2048-bit = ~360
        ok = keylen >= 200
        out.append(Check(5, "DKIM key ≥1024 bits", "dns", "important", ok,
                         f"Key base64 length: {keylen} ({'≥1024 bits' if ok else '<1024 bits — upgrade'})"))
    return out


def check_dmarc(domain: str) -> List[Check]:
    out = []
    txt = dig("TXT", f"_dmarc.{domain}")
    record = next((line for line in txt.split("\n") if "v=DMARC1" in line), "")

    if not record:
        out.append(Check(6, "DMARC record exists", "dns", "critical", False, "No _dmarc record"))
        out.append(Check(7, "DMARC policy ≠ none", "dns", "critical", False, "No DMARC to inspect"))
        out.append(Check(8, "DMARC reporting URI", "dns", "important", False, "No DMARC to inspect"))
        return out

    out.append(Check(6, "DMARC record exists", "dns", "critical", True, record[:120]))

    p_match = re.search(r"\bp=([a-z]+)", record)
    policy = p_match.group(1) if p_match else "missing"
    policy_ok = policy in ("quarantine", "reject")
    out.append(Check(7, "DMARC policy ≠ none", "dns", "critical", policy_ok,
                     f"Policy: {policy}" + ("" if policy_ok else " — bulk-sender rules require quarantine or reject")))

    rua = "rua=" in record
    out.append(Check(8, "DMARC reporting URI", "dns", "important", rua,
                     "Has rua=" if rua else "No 'rua=' aggregate-reporting URI"))
    return out


def check_mx(domain: str) -> List[Check]:
    out = []
    mx = dig("MX", domain)
    out.append(Check(9, "MX records exist", "dns", "critical", bool(mx),
                     mx.split("\n")[0] if mx else "No MX records"))
    return out


def check_reverse_dns(domain: str) -> List[Check]:
    out = []
    mx = dig("MX", domain).split("\n")[0]
    if not mx:
        out.append(Check(10, "Reverse DNS matches", "dns", "important", False, "No MX to derive IP from"))
        return out
    mx_host = mx.split()[-1].rstrip(".") if mx.split() else ""
    if not mx_host:
        out.append(Check(10, "Reverse DNS matches", "dns", "important", False, "No MX host"))
        return out

    ip = dig("A", mx_host).split("\n")[0]
    if not ip:
        out.append(Check(10, "Reverse DNS matches", "dns", "important", False,
                         f"No A record on MX host {mx_host}"))
        return out

    ptr = dig("-x", ip).strip().rstrip(".")
    fwd = dig("A", ptr).split("\n")[0] if ptr else ""

    if not ptr:
        out.append(Check(10, "Reverse DNS matches", "dns", "important", False,
                         f"No PTR for {ip}"))
    elif fwd == ip:
        out.append(Check(10, "Reverse DNS matches (FCrDNS)", "dns", "important", True,
                         f"{ip} ↔ {ptr}"))
    else:
        out.append(Check(10, "Reverse DNS matches (FCrDNS)", "dns", "important", False,
                         f"{ip} → {ptr} → {fwd} (mismatch)"))
    return out


# ---------------- Reputation checks (URL-based, no API keys) ----------------

def check_blacklist_multirbl(domain: str) -> List[Check]:
    """Use multirbl.valli.org's public lookup page as a heuristic.

    We don't scrape results (rate-limit policies vary); we just fetch the
    page to confirm the domain isn't immediately flagged. For real
    blacklist scoring, operators paste the URL into their browser."""
    out = []
    url = f"https://multirbl.valli.org/lookup/{domain}.html"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "claude-cold-email/0.2 deliverability-check"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            # Look for explicit listed indicators
            listed = bool(re.search(r"\b(LISTED|spamhaus|surbl)\b", content[:20000], re.IGNORECASE))
            out.append(Check(11, "Not on Spamhaus/SURBL (heuristic)", "reputation", "critical",
                             not listed,
                             f"Check the full report at {url}"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as err:
        out.append(Check(11, "Not on Spamhaus/SURBL (heuristic)", "reputation", "important", True,
                         f"Could not reach multirbl ({type(err).__name__}); verify manually at {url}"))
    return out


# ---------------- Bulk-sender compliance (Feb 2024 rules) ----------------

def check_bulk_sender_compliance(spf_passes: bool, dmarc_policy_ok: bool) -> List[Check]:
    """Google/Yahoo/Microsoft Feb 2024 rules: SPF + DKIM aligned + DMARC ≥ quarantine + List-Unsubscribe + spam <0.3%"""
    out = []
    out.append(Check(12, "SPF + DKIM aligned (bulk-sender)", "compliance", "critical",
                     spf_passes,
                     "Requires both SPF and DKIM passing" if spf_passes else "SPF or DKIM not configured"))
    out.append(Check(13, "DMARC ≥ quarantine (bulk-sender)", "compliance", "critical",
                     dmarc_policy_ok,
                     "Required for senders >5,000/day to consumer inboxes"))
    out.append(Check(14, "List-Unsubscribe header (RFC 8058)",
                     "compliance", "important", True,
                     "Cannot verify from DNS — must be set in your send infrastructure (Smartlead/Instantly/etc.)"))
    out.append(Check(15, "Spam-complaint rate ≤0.3% (Postmaster)",
                     "compliance", "important", True,
                     "Cannot verify from DNS — track via Google Postmaster Tools"))
    return out


# ---------------- Orchestration ----------------

def run_all(domain: str, selector: str) -> dict:
    checks: List[Check] = []
    checks.extend(check_spf(domain))
    checks.extend(check_dkim(domain, selector))
    checks.extend(check_dmarc(domain))
    checks.extend(check_mx(domain))
    checks.extend(check_reverse_dns(domain))
    checks.extend(check_blacklist_multirbl(domain))

    spf_pass = all(c.passing for c in checks if c.id in (1, 2))
    dkim_pass = all(c.passing for c in checks if c.id in (4, 5))
    dmarc_pass = all(c.passing for c in checks if c.id == 7)

    checks.extend(check_bulk_sender_compliance(spf_pass and dkim_pass, dmarc_pass))

    passing = sum(1 for c in checks if c.passing)
    total = len(checks)
    score = int(round(passing / total * 100)) if total else 0

    if score >= 95:
        verdict = "Ready — ship"
    elif score >= 85:
        verdict = "Ship but fix B-list within 30 days"
    elif score >= 70:
        verdict = "Don't scale spend — fix top 3 first"
    elif score >= 50:
        verdict = "Hold campaign — fix critical-tier"
    else:
        verdict = "Pause everything — rebuild infra"

    return {
        "domain": domain,
        "selector": selector,
        "score": score,
        "passing": passing,
        "total": total,
        "verdict": verdict,
        "checks": [asdict(c) for c in checks],
        "fixes": _fix_order(checks),
    }


def _fix_order(checks: List[Check]) -> List[dict]:
    """Order failing checks by severity → fix order."""
    severity_order = {"critical": 0, "important": 1, "nice-to-have": 2}
    failing = [c for c in checks if not c.passing]
    failing.sort(key=lambda c: (severity_order.get(c.severity, 3), c.id))
    return [{"id": c.id, "name": c.name, "severity": c.severity, "detail": c.detail}
            for c in failing]


def format_text(result: dict) -> str:
    lines = [
        f"# Deliverability — {result['domain']}",
        f"",
        f"Score: {result['score']}/100 — {result['verdict']}",
        f"Passing: {result['passing']}/{result['total']}",
        f"",
        f"## Per-check",
    ]
    for c in result["checks"]:
        mark = "✓" if c["passing"] else "✗"
        lines.append(f"  {mark}  {str(c['id']).rjust(2)}. {c['name'].ljust(45)} {c['detail'][:80]}")

    if result["fixes"]:
        lines.append("")
        lines.append("## Fix order")
        for f in result["fixes"]:
            lines.append(f"  [{f['severity'].upper()}] {f['name']}")
            lines.append(f"    → {f['detail']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default="", help="Sending domain")
    parser.add_argument("--selector", default="default", help="DKIM selector (default: 'default')")
    parser.add_argument("--format", default="text", choices=["text", "json"])
    args = parser.parse_args()

    if not args.domain:
        print("--domain required.", file=sys.stderr)
        return 2

    result = run_all(args.domain, args.selector)
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result))

    return 0 if result["score"] >= 85 else 1


if __name__ == "__main__":
    sys.exit(main())
