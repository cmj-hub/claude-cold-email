#!/usr/bin/env python3
"""Scorer CLI convention: --file / --stdin, --json, old flags as aliases,
"- what → fix" refusal lines, and a closing "Next:" line."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
CANARY = "super-secret-token"
NEXT_FIX = "Next: fix the lines above and run this again."


def run(script, args, stdin=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=10,
    )


def last_line(result):
    return result.stdout.strip().splitlines()[-1]


class Letter(unittest.TestCase):
    def test_pass_ends_with_next(self):
        result = run("score_letter.py", ["--file", str(EXAMPLES / "letter-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(last_line(result).startswith("Next: "))
        self.assertIn("lint", last_line(result))

    def test_refusal_lines_say_what_to_change(self):
        result = run("score_letter.py", ["--file", str(EXAMPLES / "letter-demographic.json")])
        self.assertEqual(result.returncode, 1)
        reasons = [l for l in result.stdout.splitlines() if l.startswith("- ")]
        self.assertEqual(len(reasons), 3)
        self.assertTrue(all(" → " in l for l in reasons))
        self.assertEqual(last_line(result), NEXT_FIX)

    def test_json_adds_fixes_and_next(self):
        result = run("score_letter.py", ["--file", str(EXAMPLES / "letter-demographic.json"), "--json"])
        data = json.loads(result.stdout)
        self.assertEqual(len(data["fixes"]), len(data["reasons"]))
        self.assertEqual(data["next"], NEXT_FIX)


class SpamLint(unittest.TestCase):
    def test_file_plain_text_email(self):
        result = run("spam_word_lint.py", ["--file", str(EXAMPLES / "t1.email.md")])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Score: 100/100", result.stdout)
        self.assertTrue(last_line(result).startswith("Next: "))

    def test_file_spam_refused_with_fixes(self):
        result = run("spam_word_lint.py", ["--file", str(EXAMPLES / "spam.email.md")])
        self.assertEqual(result.returncode, 1)
        flags = [l for l in result.stdout.splitlines() if l.startswith("- ")]
        self.assertTrue(flags)
        self.assertTrue(all(" → " in l for l in flags))
        self.assertEqual(last_line(result), NEXT_FIX)

    def test_json_alias_and_letter_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "letter.json"
            path.write_text(json.dumps({
                "public_signal": "x", "subject": "Quick note", "letter": "Act now, it's urgent.",
            }), encoding="utf-8")
            result = run("spam_word_lint.py", ["--file", str(path), "--json"])
        data = json.loads(result.stdout)
        fixes = [f["fix"] for a in data["axes"] for f in a["flags"]]
        self.assertTrue(fixes)
        self.assertIn("next", data)
        legacy = run("spam_word_lint.py", ["--subject", "Hi", "--body", "Hello", "--format", "json"])
        self.assertIn("next", json.loads(legacy.stdout))

    def test_bad_file_is_not_echoed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text('{"subject": "' + CANARY, encoding="utf-8")
            result = run("spam_word_lint.py", ["--file", str(path)])
            missing = run("spam_word_lint.py", ["--file", str(Path(tmp) / "none.json")])
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(CANARY, result.stdout + result.stderr)
        self.assertEqual(missing.returncode, 2)
        self.assertNotIn("Traceback", missing.stderr)


class Subject(unittest.TestCase):
    def test_file_reads_subject_line(self):
        result = run("score_subject_line.py", ["--file", str(EXAMPLES / "t1.email.md"), "--framework", "pain"])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(last_line(result).startswith("Next: "))

    def test_refusal_has_fixes(self):
        result = run("score_subject_line.py", ["--file", str(EXAMPLES / "spam.email.md"), "--json"])
        self.assertEqual(result.returncode, 1)
        data = json.loads(result.stdout)
        self.assertEqual(len(data["fixes"]), len(data["flags"]))
        self.assertEqual(data["next"], NEXT_FIX)


class Reply(unittest.TestCase):
    def test_file_and_batch_alias_match(self):
        new = run("score_reply.py", ["--file", str(EXAMPLES / "replies.jsonl"), "--json"])
        old = run("score_reply.py", ["--batch", str(EXAMPLES / "replies.jsonl"), "--format", "json"])
        self.assertEqual(new.returncode, 0)
        self.assertEqual(json.loads(new.stdout), json.loads(old.stdout))
        cats = [r["category"] for r in json.loads(new.stdout)]
        self.assertEqual(cats, ["buy-signal", "neutral", "not-interested"])
        self.assertTrue(all(r["next"].startswith("Next: ") for r in json.loads(new.stdout)))

    def test_single_reply_ends_with_next(self):
        result = run("score_reply.py", ["--body", "Please unsubscribe me"])
        self.assertTrue(last_line(result).startswith("Next: "))
        self.assertNotIn("  --batch", run("score_reply.py", ["--help"]).stdout.split("options:")[-1])


class List(unittest.TestCase):
    ARGS = ["--brand-config", str(ROOT / "brand-config.example.json"), "--today", "2026-10-04"]

    def test_file_and_input_alias_match(self):
        new = run("score_list.py", ["--file", str(EXAMPLES / "prospects.csv"), "--json", *self.ARGS])
        old = run("score_list.py", ["--input", str(EXAMPLES / "prospects.csv"), "--format", "json", *self.ARGS])
        self.assertEqual(new.returncode, 1)
        self.assertEqual(json.loads(new.stdout), json.loads(old.stdout))
        data = json.loads(new.stdout)
        self.assertTrue(all(r["fix"] for r in data["remove"]))
        self.assertEqual(data["next"], NEXT_FIX)

    def test_stdin_and_refusal_lines(self):
        text = (EXAMPLES / "prospects.csv").read_text(encoding="utf-8")
        result = run("score_list.py", ["--stdin", *self.ARGS], stdin=text)
        self.assertEqual(result.returncode, 1)
        rows = [l for l in result.stdout.splitlines() if l.startswith("- row ")]
        self.assertTrue(rows)
        self.assertTrue(all(" → " in l for l in rows))
        self.assertEqual(last_line(result), NEXT_FIX)

    def test_stdin_write_is_bad_input(self):
        result = run("score_list.py", ["--stdin", "--write"], stdin="email\na@b.example\n")
        self.assertEqual(result.returncode, 2)


class Deliverability(unittest.TestCase):
    def test_file_input_is_validated_before_dig(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "domain.json"
            path.write_text(json.dumps({"domain": "-evil.example"}), encoding="utf-8")
            result = run("check_deliverability.py", ["--file", str(path)])
            bad = run("check_deliverability.py", ["--stdin"], stdin='{"domain": "' + CANARY)
        self.assertEqual(result.returncode, 2)
        self.assertIn("plain DNS names", result.stderr)
        self.assertEqual(bad.returncode, 2)
        self.assertNotIn(CANARY, bad.stdout + bad.stderr)

    def test_failing_checks_carry_a_fix(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        import check_deliverability as cd
        saved = cd.dig_checked, cd.dig
        cd.dig_checked = lambda q, n: ""
        cd.dig = lambda q, n: ""
        try:
            result = cd.run_all("example.com", "default")
        finally:
            cd.dig_checked, cd.dig = saved
        self.assertTrue(result["fixes"])
        self.assertTrue(all(f["fix"] for f in result["fixes"]))
        self.assertEqual(result["next"], NEXT_FIX)
        text = cd.format_text(result)
        self.assertEqual(text.splitlines()[-1], NEXT_FIX)


class Help(unittest.TestCase):
    def test_every_scorer_help_shows_an_example(self):
        for script in ("score_letter.py", "spam_word_lint.py", "score_subject_line.py",
                       "score_reply.py", "score_list.py", "check_deliverability.py"):
            result = run(script, ["--help"])
            self.assertEqual(result.returncode, 0, script)
            self.assertIn("examples/", result.stdout.split("example:")[-1], script)


if __name__ == "__main__":
    unittest.main()
