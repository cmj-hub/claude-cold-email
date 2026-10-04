#!/usr/bin/env python3
"""
check_deliverability.py — Score a sending domain's deliverability
across 15 checks: SPF, DKIM, DMARC, MX, reverse DNS, blacklists,
and bulk-sender compliance (Google/Yahoo/Microsoft Feb 2024 rules).

USAGE:
    python3 check_deliverability.py --domain outreach.acme.com
    python3 check_deliverability.py --domain ... --selector google

Uses `dig` for every lookup, blacklists included (Spamhaus DBL and SURBL
are DNS zones). No HTTP calls, no paid services.

A check that cannot be verified (DNS timeout, a blacklist zone that
refuses this resolver, anything DNS cannot show) is reported as
"unknown". Unknown checks are listed for manual follow-up and left out
of the score; they are never counted as a pass or a fail.

Exit codes:
    0  score >= 85   (ready to send)
    1  score < 85    (do not send / fix first)
    2  bad input, or `dig` is not installed
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple


HOST = re.compile(
    r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)"
    r"(\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$"
)
SELECTOR = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62})?$")
IPV4 = re.compile(
    r"^(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}$"
)


def plain_dns_name(name: str) -> bool:
    return bool(name) and not name.startswith("-") and not any(
        char in name for char in " \t\r\n/\\@?"
    )


@dataclass
class Check:
    id: int
    name: str
    category: str  # dns | reputation | compliance
    severity: str  # critical | important | nice-to-have
    passing: Optional[bool]  # None = could not be verified
    detail: str

    @property
    def status(self) -> str:
        if self.passing is None:
            return "unknown"
        return "pass" if self.passing else "fail"


class DigMissing(RuntimeError):
    pass


class LookupFailed(RuntimeError):
    pass


def dig_checked(qtype: str, name: str) -> str:
    """Run `dig +short` and return stdout.

    Raises LookupFailed when the query did not complete (timeout, no
    server reachable, unsafe name) so callers can report "unknown"
    instead of "no record". An empty string means the query completed
    and there is no such record."""
    if qtype == "-x":
        if not IPV4.match(name):
            raise LookupFailed("not an IPv4 address")
    elif not plain_dns_name(name):
        raise LookupFailed("not a plain DNS name")
    try:
        result = subprocess.run(
            ["dig", "+short", "+time=5", "+tries=2", qtype, name],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except FileNotFoundError:
        raise DigMissing("dig is not installed") from None
    except subprocess.TimeoutExpired:
        raise LookupFailed("timed out") from None
    out = result.stdout.strip()
    if result.returncode != 0 or out.startswith(";;"):
        raise LookupFailed(f"dig exit {result.returncode}")
    return out


def dig(qtype: str, name: str) -> str:
    """Best-effort lookup: empty string when the record is absent or the
    lookup failed. Use dig_checked where the difference matters."""
    try:
        return dig_checked(qtype, name)
    except LookupFailed:
        return ""


# ---------------- DNS checks ----------------

def check_spf(domain: str) -> List[Check]:
    out = []
    try:
        txt = dig_checked("TXT", domain)
    except LookupFailed as err:
        why = f"TXT lookup failed ({err}); retry or run: dig TXT {domain}"
        return [
            Check(1, "SPF record exists", "dns", "critical", None, why),
            Check(2, "SPF includes a known provider", "dns", "critical", None, why),
            Check(3, "SPF lookup count ≤10", "dns", "important", None, why),
        ]
    spf_line = next((line for line in txt.split("\n") if "v=spf1" in line), "")
    if not spf_line:
        out.append(Check(1, "SPF record exists", "dns", "critical", False, "No SPF TXT record"))
        out.append(Check(2, "SPF includes a known provider", "dns", "critical", False, "No SPF to inspect"))
        out.append(Check(3, "SPF lookup count ≤10", "dns", "important", False, "No SPF to inspect"))
        return out

    out.append(Check(1, "SPF record exists", "dns", "critical", True, spf_line[:120]))

    # Provider include
    common_providers = [
        "_spf.google.com",
        "spf.protection.outlook.com",
        "zoho.",
        "smartlead.io",
        "mailchimp",
        "mandrillapp.com",
        "hubspot",
        "sparkpostmail.com",
        "_spf.salesforce.com",
        "amazonses.com",
        "sendgrid.net",
        "mailgun.org",
    ]
    has_provider = any(p in spf_line.lower() for p in common_providers)
    out.append(Check(
        2, "SPF includes a known provider", "dns", "critical",
        True if has_provider else None,
        "Found a known include" if has_provider
        else "No well-known provider include; confirm your sender's include is listed",
    ))

    # Top-level DNS-querying terms only; nested includes add more (RFC 7208 §4.6.4).
    terms = spf_line.replace('"', " ").split()
    lookups = sum(
        1 for term in terms
        if re.match(r"^[+?~-]?(include:|exists:|redirect=|a$|a[:/]|mx$|mx[:/]|ptr$|ptr:)", term.lower())
    )
    out.append(Check(
        3, "SPF lookup count ≤10", "dns", "important",
        lookups <= 10,
        f"Top-level lookups: {lookups} (nested includes not expanded)",
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
        why = ("No DKIM key at the selectors tried. Find the real selector in a sent "
               "message's DKIM-Signature header (s=) and re-run with --selector")
        out.append(Check(4, "DKIM selector resolves", "dns", "critical", None, why))
        out.append(Check(5, "DKIM key ≥1024 bits", "dns", "important", None, "No DKIM to inspect"))
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
    try:
        txt = dig_checked("TXT", f"_dmarc.{domain}")
    except LookupFailed as err:
        why = f"TXT lookup failed ({err}); retry or run: dig TXT _dmarc.{domain}"
        return [
            Check(6, "DMARC record exists", "dns", "critical", None, why),
            Check(7, "DMARC policy enforcing (quarantine/reject)", "dns", "important", None, why),
            Check(8, "DMARC reporting URI", "dns", "important", None, why),
        ]
    record = next((line for line in txt.split("\n") if "v=DMARC1" in line), "")

    if not record:
        out.append(Check(6, "DMARC record exists", "dns", "critical", False, "No _dmarc record"))
        out.append(Check(7, "DMARC policy enforcing (quarantine/reject)", "dns", "important", False, "No DMARC to inspect"))
        out.append(Check(8, "DMARC reporting URI", "dns", "important", False, "No DMARC to inspect"))
        return out

    out.append(Check(6, "DMARC record exists", "dns", "critical", True, record[:120]))

    p_match = re.search(r"\bp=([a-z]+)", record)
    policy = p_match.group(1) if p_match else "missing"
    policy_ok = policy in ("quarantine", "reject")
    out.append(Check(7, "DMARC policy enforcing (quarantine/reject)", "dns", "important", policy_ok,
                     f"Policy: {policy}" + ("" if policy_ok else
                     " — p=none meets the Google/Yahoo minimum; move to quarantine once reports are clean")))

    rua = "rua=" in record
    out.append(Check(8, "DMARC reporting URI", "dns", "important", rua,
                     "Has rua=" if rua else "No 'rua=' aggregate-reporting URI"))
    return out


def check_mx(domain: str) -> List[Check]:
    out = []
    try:
        mx = dig_checked("MX", domain)
    except LookupFailed as err:
        return [Check(9, "MX records exist", "dns", "critical", None, f"MX lookup failed ({err})")]
    out.append(Check(9, "MX records exist", "dns", "critical", bool(mx),
                     mx.split("\n")[0] if mx else "No MX records — replies to this domain bounce"))
    return out


def check_reverse_dns(domain: str) -> List[Check]:
    out = []
    mx = dig("MX", domain).split("\n")[0]
    if not mx:
        out.append(Check(10, "Reverse DNS matches", "dns", "important", False, "No MX to derive IP from"))
        return out
    mx_host = mx.split()[-1].rstrip(".") if mx.split() else ""
    if not mx_host or not HOST.match(mx_host.lower()):
        out.append(Check(10, "Reverse DNS matches", "dns", "important", False,
                         "MX host is not a plain DNS name"))
        return out

    ip = dig("A", mx_host).split("\n")[0].strip()
    if not IPV4.match(ip):
        out.append(Check(10, "Reverse DNS matches", "dns", "important", False,
                         "MX host A record is not an IPv4 address"))
        return out

    ptrs = [line.rstrip(".") for line in dig("-x", ip).split("\n") if line.strip()]
    ptr = ptrs[0] if ptrs else ""
    fwd = ""
    for name in ptrs:
        addrs = dig("A", name).split("\n")
        if ip in addrs:
            ptr, fwd = name, ip
            break

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


# ---------------- Reputation checks (DNS blocklists, no HTTP) ----------------

# (zone, test name that the zone always lists, how to read an answer)
DNSBLS = [
    ("dbl.spamhaus.org", "dbltest.com"),
    ("multi.surbl.org", "test.surbl.org"),
]


def _dnsbl_answer(zone: str, answer: str) -> Optional[bool]:
    """True = listed, False = not listed, None = the zone refused us."""
    ips = [a for a in answer.split() if IPV4.match(a)]
    if not ips:
        return False
    if zone.endswith("spamhaus.org"):
        # 127.0.1.x = listed; 127.255.255.x = query refused (public resolver, rate limit).
        if any(ip.startswith("127.255.255.") for ip in ips):
            return None
        return any(ip.startswith("127.0.1.") for ip in ips)
    # SURBL: 127.0.0.1 = access blocked; any other 127.0.0.x bitmask = listed.
    if ips == ["127.0.0.1"]:
        return None
    return any(ip.startswith("127.0.0.") and ip != "127.0.0.1" for ip in ips)


def check_blacklists(domain: str) -> List[Check]:
    manual = f"https://multirbl.valli.org/lookup/{domain}.html"
    listed_on, unknown = [], []
    for zone, test_name in DNSBLS:
        try:
            # Probe the zone's permanent test entry first. If it does not come
            # back listed, this resolver is not getting real answers, so a clean
            # result for the real domain would mean nothing.
            if _dnsbl_answer(zone, dig_checked("A", f"{test_name}.{zone}")) is not True:
                unknown.append(zone)
                continue
            verdict = _dnsbl_answer(zone, dig_checked("A", f"{domain}.{zone}"))
        except LookupFailed:
            unknown.append(zone)
            continue
        if verdict is None:
            unknown.append(zone)
        elif verdict:
            listed_on.append(zone)

    if listed_on:
        return [Check(11, "Not on Spamhaus DBL / SURBL", "reputation", "critical", False,
                      f"Listed on {', '.join(listed_on)} — request delisting before sending")]
    if unknown:
        checked = [z for z, _ in DNSBLS if z not in unknown]
        prefix = f"Clean on {', '.join(checked)}; " if checked else ""
        return [Check(11, "Not on Spamhaus DBL / SURBL", "reputation", "critical", None,
                      f"{prefix}{', '.join(unknown)} would not answer this resolver; check {manual}")]
    return [Check(11, "Not on Spamhaus DBL / SURBL", "reputation", "critical", True,
                  "Not listed on dbl.spamhaus.org or multi.surbl.org")]


# ---------------- Bulk-sender compliance (Feb 2024 rules) ----------------

def check_bulk_sender_compliance(spf_dkim: Optional[bool], dmarc_exists: Optional[bool]) -> List[Check]:
    """Google/Yahoo (Feb 2024) and Microsoft (May 2025) bulk-sender rules:
    SPF and DKIM, a published DMARC record (p=none is the minimum), one-click
    unsubscribe for marketing mail, spam rate under 0.3%.
    See skills/cold-email/references/bulk-sender-rules.md."""
    out = []
    out.append(Check(12, "SPF + DKIM both published (bulk-sender)", "compliance", "critical",
                     spf_dkim,
                     "SPF and DKIM found" if spf_dkim else
                     "Could not confirm both SPF and DKIM" if spf_dkim is None else
                     "SPF or DKIM missing"))
    out.append(Check(13, "DMARC published (bulk-sender minimum)", "compliance", "critical",
                     dmarc_exists,
                     "Required for senders of 5,000+/day to Gmail, Yahoo, or Outlook.com; p=none is the minimum"))
    out.append(Check(14, "List-Unsubscribe header (RFC 8058)",
                     "compliance", "important", None,
                     "Not visible in DNS — confirm in your sending tool"))
    out.append(Check(15, "Spam-complaint rate <0.3% (Postmaster)",
                     "compliance", "important", None,
                     "Not visible in DNS — check Google Postmaster Tools"))
    return out


# ---------------- Orchestration ----------------

def run_all(domain: str, selector: str) -> dict:
    checks: List[Check] = []
    checks.extend(check_spf(domain))
    checks.extend(check_dkim(domain, selector))
    checks.extend(check_dmarc(domain))
    checks.extend(check_mx(domain))
    checks.extend(check_reverse_dns(domain))
    checks.extend(check_blacklists(domain))

    by_id = {c.id: c.passing for c in checks}
    spf_dkim = _all_known((by_id.get(1), by_id.get(4)))
    checks.extend(check_bulk_sender_compliance(spf_dkim, by_id.get(6)))

    passing = sum(1 for c in checks if c.passing is True)
    verified = sum(1 for c in checks if c.passing is not None)
    total = len(checks)
    score = int(round(passing / verified * 100)) if verified else 0

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
        "verified": verified,
        "total": total,
        "verdict": verdict,
        "checks": [dict(asdict(c), status=c.status) for c in checks],
        "fixes": _fix_order(checks),
        "unverified": [{"id": c.id, "name": c.name, "detail": c.detail}
                       for c in checks if c.passing is None],
    }


def _all_known(values: Tuple[Optional[bool], ...]) -> Optional[bool]:
    if any(v is False for v in values):
        return False
    if any(v is None for v in values):
        return None
    return True


def _fix_order(checks: List[Check]) -> List[dict]:
    """Order failing checks by severity → fix order."""
    severity_order = {"critical": 0, "important": 1, "nice-to-have": 2}
    failing = [c for c in checks if c.passing is False]
    failing.sort(key=lambda c: (severity_order.get(c.severity, 3), c.id))
    return [{"id": c.id, "name": c.name, "severity": c.severity, "detail": c.detail}
            for c in failing]


def format_text(result: dict) -> str:
    lines = [
        f"# Deliverability — {result['domain']}",
        f"",
        f"Score: {result['score']}/100 — {result['verdict']}",
        f"Passing: {result['passing']}/{result['verified']} verified ({result['total'] - result['verified']} unknown)",
        f"",
        f"## Per-check",
    ]
    for c in result["checks"]:
        mark = {"pass": "✓", "fail": "✗"}.get(c["status"], "?")
        lines.append(f"  {mark}  {str(c['id']).rjust(2)}. {c['name'].ljust(45)} {c['detail'][:80]}")

    if result["fixes"]:
        lines.append("")
        lines.append("## Fix order")
        for f in result["fixes"]:
            lines.append(f"  [{f['severity'].upper()}] {f['name']}")
            lines.append(f"    → {f['detail']}")

    if result["unverified"]:
        lines.append("")
        lines.append("## Verify manually (not scored)")
        for u in result["unverified"]:
            lines.append(f"  ? {u['name']}")
            lines.append(f"    → {u['detail']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", default="", help="Sending domain")
    parser.add_argument("--selector", default="default", help="DKIM selector (default: 'default')")
    parser.add_argument("--format", default="text", choices=["text", "json"])
    args = parser.parse_args()

    domain = args.domain.strip().lower().rstrip(".")
    selector = args.selector.strip().lower().rstrip(".")
    if not domain:
        print("--domain required.", file=sys.stderr)
        return 2
    if not HOST.match(domain) or not SELECTOR.match(selector):
        print("error: domain and selector must be plain DNS names", file=sys.stderr)
        return 2

    try:
        result = run_all(domain, selector)
    except DigMissing:
        print("error: `dig` is required (macOS: brew install bind; Debian/Ubuntu: "
              "apt install dnsutils). No checks were run.", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_text(result))

    return 0 if result["score"] >= 85 else 1


if __name__ == "__main__":
    sys.exit(main())
