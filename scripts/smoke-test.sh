#!/usr/bin/env bash
# Smoke-test the deterministic scripts in claude-cold-email.
# Each must exit cleanly on known input and produce expected output shape.
#
# Runs in CI under GitHub Actions (Ubuntu, Python 3.12, dig pre-installed).

set -euo pipefail

PASSED=0
FAILED=0

check() {
  local name="$1"; shift
  if "$@"; then
    echo "  ✓ $name"
    PASSED=$((PASSED + 1))
  else
    echo "  ✗ $name (exit $?)"
    FAILED=$((FAILED + 1))
  fi
}

echo "=== score_letter.py ==="
check "signal-anchored letter passes" \
  python3 scripts/score_letter.py --file examples/letter-good.json
set +e
python3 scripts/score_letter.py --file examples/letter-demographic.json > /dev/null
rc=$?
set -e
if [ "$rc" -eq 1 ]; then
  echo "  ✓ demographic letter refused"
  PASSED=$((PASSED + 1))
else
  echo "  ✗ demographic letter should exit 1 (got $rc)"
  FAILED=$((FAILED + 1))
fi

echo ""
echo "=== spam_word_lint.py ==="
check "sample T1 file scores ≥75" \
  python3 scripts/spam_word_lint.py --file examples/t1.email.md
# Should exit 0 (score ≥75) on a clean email
check "clean email scores ≥75" \
  python3 scripts/spam_word_lint.py \
    --subject "Pipeline gap after the Q3 hire freeze?" \
    --body "Sarah — saw you posted the Demand Gen Lead role four days ago. Pipeline gap is usually upstream of an SDR hire. Worth 15 min Thursday to walk through?"
# Should exit 1 on spam-laden email
echo "  (testing inverse — spam input should exit non-zero)"
if python3 scripts/spam_word_lint.py --subject "URGENT! ACT NOW Limited Time 🚀 FREE" --body "ACT NOW! You won't believe this one trick. FREE MONEY guaranteed! Click here for amazing results. https://x.com https://y.com https://z.com" > /dev/null 2>&1; then
  echo "  ✗ spam-laden email should have failed but passed"
  FAILED=$((FAILED + 1))
else
  echo "  ✓ spam-laden email correctly rejected"
  PASSED=$((PASSED + 1))
fi

echo ""
echo "=== score_subject_line.py ==="
check "strong pain subject" \
  python3 scripts/score_subject_line.py --subject "Pipeline gap after the Q3 freeze?" --framework pain
check "subject read from the sample T1 file" \
  python3 scripts/score_subject_line.py --file examples/t1.email.md --framework pain

echo ""
echo "=== score_reply.py ==="
check "buy-signal reply" \
  python3 scripts/score_reply.py \
    --body "Sounds interesting — send me the case study and what dates work next week?" \
    --minutes-since-send 27
check "sample reply batch" \
  python3 scripts/score_reply.py --file examples/replies.jsonl

echo ""
echo "=== score_list.py ==="
# The sample list is built to fail: exit 1 with a JSON report, not exit 2.
set +e
python3 scripts/score_list.py --file examples/prospects.csv \
  --brand-config brand-config.example.json --today 2026-10-04 --json > /dev/null
rc=$?
set -e
if [ "$rc" -eq 1 ]; then
  echo "  ✓ sample list scored and flagged for cleaning"
  PASSED=$((PASSED + 1))
else
  echo "  ✗ sample list should exit 1 (got $rc)"
  FAILED=$((FAILED + 1))
fi

echo ""
echo "=== check_deliverability.py ==="
# Hit a domain with known-good DNS
check "DNS resolution against jaymountconsulting.com" \
  python3 scripts/check_deliverability.py --file examples/domain.json

echo ""
echo "=== dig_dns.sh ==="
check "dig_dns.sh syntax + run" \
  bash scripts/dig_dns.sh jaymountconsulting.com

echo ""
echo "Passed: $PASSED"
echo "Failed: $FAILED"
[ "$FAILED" -eq 0 ]
