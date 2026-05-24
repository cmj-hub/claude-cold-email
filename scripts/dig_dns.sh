#!/usr/bin/env bash
# dig_dns.sh — Deterministic DNS lookups for cold-email deliverability.
#
# USAGE:
#   ./dig_dns.sh <sending-domain> [dkim-selector]
#
# Returns plain-text output with SPF, DKIM, DMARC, MX, and PTR results.
# Zero deps beyond `dig` (BIND tools — pre-installed on macOS/Linux).
#
# Output is human-readable AND can be piped to check_deliverability.py
# for scoring.

set -euo pipefail

DOMAIN="${1:-}"
SELECTOR="${2:-default}"

if [[ -z "$DOMAIN" ]]; then
    echo "Usage: $0 <sending-domain> [dkim-selector]" >&2
    echo "Example: $0 outreach.acme.com default" >&2
    exit 2
fi

if ! command -v dig >/dev/null 2>&1; then
    echo "ERROR: dig is required but not installed." >&2
    echo "  macOS: brew install bind" >&2
    echo "  Ubuntu/Debian: apt install dnsutils" >&2
    exit 2
fi

echo "=== Deliverability DNS check for $DOMAIN ==="
echo ""

# --- SPF ---
echo "## SPF"
SPF=$(dig +short TXT "$DOMAIN" | grep -i "v=spf1" || true)
if [[ -z "$SPF" ]]; then
    echo "  ✗ No SPF record found"
else
    echo "  ✓ $SPF"
    # SPF lookup-count check
    LOOKUPS=$(echo "$SPF" | grep -oE "include:|a:|mx:|ptr:|exists:|redirect=" | wc -l | tr -d ' ')
    echo "  → lookup count (approx): $LOOKUPS (limit: 10)"
fi
echo ""

# --- DKIM ---
echo "## DKIM (selector: $SELECTOR)"
DKIM=$(dig +short TXT "${SELECTOR}._domainkey.${DOMAIN}" | tr -d '"' | tr -d ' ' || true)
if [[ -z "$DKIM" ]]; then
    echo "  ✗ No DKIM record at ${SELECTOR}._domainkey.${DOMAIN}"
    echo "  → Try other common selectors: google, selector1, s1024, mandrill"
else
    echo "  ✓ DKIM record present"
    # Try to extract key length
    KEY=$(echo "$DKIM" | grep -oE "p=[A-Za-z0-9+/=]+" | cut -c3- || true)
    if [[ -n "$KEY" ]]; then
        KEY_LEN=${#KEY}
        # Approx: 1024-bit key = ~216 base64 chars; 2048-bit = ~360
        if (( KEY_LEN < 200 )); then
            echo "  ⚠ Key appears <1024 bits (len=$KEY_LEN base64 chars)"
        elif (( KEY_LEN < 350 )); then
            echo "  → Key ~1024 bits"
        else
            echo "  → Key ~2048 bits"
        fi
    fi
fi
echo ""

# --- DMARC ---
echo "## DMARC"
DMARC=$(dig +short TXT "_dmarc.${DOMAIN}" | tr -d '"' || true)
if [[ -z "$DMARC" ]]; then
    echo "  ✗ No DMARC record"
    echo "  → Required for bulk-sender compliance (Google/Yahoo/Microsoft Feb 2024)"
else
    echo "  ✓ $DMARC"
    POLICY=$(echo "$DMARC" | grep -oE "p=[a-z]+" | cut -c3- || true)
    case "$POLICY" in
        none)
            echo "  ⚠ Policy is 'none' — bulk-sender rules require 'quarantine' or 'reject'"
            ;;
        quarantine|reject)
            echo "  → Policy: $POLICY (bulk-sender compliant)"
            ;;
        *)
            echo "  ⚠ No policy found in record"
            ;;
    esac
    RUA=$(echo "$DMARC" | grep -oE "rua=mailto:[^;]+" || true)
    if [[ -z "$RUA" ]]; then
        echo "  ⚠ No 'rua=' aggregate-reporting URI configured"
    else
        echo "  → Reporting URI: $RUA"
    fi
fi
echo ""

# --- MX ---
echo "## MX"
MX=$(dig +short MX "$DOMAIN" || true)
if [[ -z "$MX" ]]; then
    echo "  ✗ No MX records"
else
    echo "$MX" | while IFS= read -r line; do
        echo "  ✓ $line"
    done
fi
echo ""

# --- Reverse DNS (only if a sending IP is derivable) ---
echo "## Reverse DNS"
MX_HOST=$(echo "$MX" | head -1 | awk '{print $2}' | sed 's/\.$//' || true)
if [[ -n "$MX_HOST" ]]; then
    MX_IP=$(dig +short "$MX_HOST" A | head -1 || true)
    if [[ -n "$MX_IP" ]]; then
        PTR=$(dig +short -x "$MX_IP" | sed 's/\.$//' || true)
        if [[ -z "$PTR" ]]; then
            echo "  ✗ No PTR record for $MX_IP"
        else
            echo "  ✓ $MX_IP → $PTR"
            # Forward-confirm
            FWD=$(dig +short "$PTR" A | head -1 || true)
            if [[ "$FWD" == "$MX_IP" ]]; then
                echo "  → Forward-confirms (FCrDNS): yes"
            else
                echo "  ⚠ Forward-confirm mismatch: $PTR → $FWD"
            fi
        fi
    else
        echo "  (no A record on primary MX; skip)"
    fi
else
    echo "  (no MX to derive IP from; skip)"
fi
echo ""

# --- Summary ---
echo "## Summary"
echo "Domain:    $DOMAIN"
echo "Selector:  $SELECTOR"
echo ""
echo "Pipe to check_deliverability.py for scoring:"
echo "  $0 $DOMAIN $SELECTOR | python3 check_deliverability.py --stdin"
