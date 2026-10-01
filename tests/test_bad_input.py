#!/usr/bin/env python3
"""Bad input exits 2. DNS checks reject a name before dig or HTTP."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "super-secret-token"


def run(script, args, stdin=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=5,
    )


class ColdEmailBadInput(unittest.TestCase):
    def test_reply_bad_json_hides_bytes(self):
        result = run("score_reply.py", ["--stdin"], stdin='{"body": "' + TOKEN)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(TOKEN, result.stderr + result.stdout)

    def test_reply_array_rejected(self):
        result = run("score_reply.py", ["--stdin"], stdin="[]")
        self.assertEqual(result.returncode, 2)
        self.assertIn("JSON must be an object", result.stderr)

    def test_reply_batch_missing_and_bad_line(self):
        missing = run("score_reply.py", ["--batch", str(ROOT / "no-such.jsonl")])
        self.assertEqual(missing.returncode, 2)
        self.assertNotIn("Traceback", missing.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_text(
                '{"body":"sounds good"}\n'
                + '{"body": "' + TOKEN + "\n"
                + "[]\n",
                encoding="utf-8",
            )
            result = run("score_reply.py", ["--batch", str(path)])
        self.assertEqual(result.returncode, 0)
        self.assertIn("line 2: bad JSON", result.stderr)
        self.assertIn("line 3: JSON must be an object", result.stderr)
        self.assertNotIn(TOKEN, result.stderr + result.stdout)

    def test_subject_and_spam_reject_array(self):
        for script in ("score_subject_line.py", "spam_word_lint.py"):
            result = run(script, ["--stdin"], stdin="[]")
            self.assertEqual(result.returncode, 2, script)
            self.assertNotIn("Traceback", result.stderr)

    def test_subject_happy_path(self):
        result = run("score_subject_line.py", ["--subject", "quick question about renewals"])
        self.assertIn(result.returncode, (0, 1))
        self.assertNotIn("Traceback", result.stderr)

    def test_domain_and_selector_never_reach_dig(self):
        cases = [
            ["--domain=-evil.example"],
            ["--domain=example.com?x=1"],
            ["--domain=example.com", "--selector=-x"],
            ["--domain=user@example.com"],
        ]
        for args in cases:
            result = run("check_deliverability.py", args)
            self.assertEqual(result.returncode, 2, args)
            self.assertIn("plain DNS names", result.stderr)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
