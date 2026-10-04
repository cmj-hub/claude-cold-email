#!/usr/bin/env python3
"""score_letter.py prints one letter plus the lint, or refuses with every reason."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELL = "super-secret-cell"
SIGNAL = "Acme posted a Demand Gen Lead role four days ago."


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "score_letter.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=5,
    )


def score(letter, signal=SIGNAL):
    result = run(["--stdin", "--json"], stdin=json.dumps({"public_signal": signal, "letter": letter}))
    return result.returncode, json.loads(result.stdout)


class ScoreLetter(unittest.TestCase):
    def test_good_draft_prints_letter_and_lint(self):
        result = run(["--file", str(ROOT / "examples" / "letter-good.json")])
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("Demand Gen Lead role four days ago.", result.stdout)
        self.assertIn("lint: ", result.stdout)
        self.assertNotIn("demographic email", result.stdout)
        letter = result.stdout.strip().splitlines()[0]
        self.assertLess(len(letter.split()), 90)

    def test_demographic_exits_1(self):
        result = run(["--file", str(ROOT / "examples" / "letter-demographic.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("demographic email", result.stdout)
        self.assertNotIn("lint:", result.stdout)

    def test_demographic_lists_every_reason(self):
        result = run(["--file", str(ROOT / "examples" / "letter-demographic.json"), "--json"])
        reasons = json.loads(result.stdout)["reasons"]
        self.assertEqual(len(reasons), 3, reasons)
        self.assertTrue(reasons[0].startswith("signal not quoted"))
        self.assertTrue(reasons[1].startswith("demographic email"))
        self.assertTrue(reasons[2].startswith("no binary ask"))

    def test_missing_signal_exits_1(self):
        result = run(["--stdin"], stdin='{"public_signal":"","letter":"A note about the post. Want it?"}')
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing public signal", result.stdout)
        self.assertNotIn("lint:", result.stdout)

    def test_role_alone_is_not_demographic(self):
        code, out = score(
            "Your VP of Sales posted it: Acme posted a Demand Gen Lead role four days ago. "
            "Worth 15 minutes Thursday?"
        )
        self.assertEqual(code, 0, out)

    def test_role_plus_stage_is_demographic(self):
        for line in (
            "I write VPs of Marketing at Series B companies.",
            "We help companies like yours.",
            "Just bumping this.",
        ):
            code, out = score(f"{SIGNAL} {line} Worth 15 minutes Thursday?")
            self.assertEqual(code, 1, line)
            self.assertTrue(any(r.startswith("demographic email") for r in out["reasons"]), line)

    def test_paraphrased_signal_refused(self):
        code, out = score("Saw you are hiring for demand. Worth 15 minutes Thursday?")
        self.assertEqual(code, 1)
        self.assertTrue(out["reasons"][0].startswith("signal not quoted"))

    def test_three_word_span_is_enough(self):
        code, out = score("Saw the Demand Gen Lead post. Worth 15 minutes Thursday?")
        self.assertEqual(code, 0, out)

    def test_ask_must_be_binary(self):
        cases = {
            "Let me know.": "no binary ask",
            "What do you think?": "ask is open-ended",
            "Let me know your thoughts?": "ask is open-ended",
            "Worth a chat? Or should I send the doc?": "more than one ask",
        }
        for ask, reason in cases.items():
            code, out = score(f"{SIGNAL} {ask}")
            self.assertEqual(code, 1, ask)
            self.assertTrue(any(r.startswith(reason) for r in out["reasons"]), (ask, out))

    def test_conditional_binary_close_passes(self):
        code, out = score(f"{SIGNAL} If it is not a priority, should I close the loop?")
        self.assertEqual(code, 0, out)

    def test_ninety_words_refused(self):
        code, out = score(SIGNAL + " word" * 85 + " Want the page?")
        self.assertEqual(code, 1)
        self.assertTrue(any("must be under 90" in r for r in out["reasons"]))

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"letter": "' + CELL)
        self.assertEqual(bad.returncode, 2)
        self.assertNotIn(CELL, bad.stdout + bad.stderr)
        self.assertIn("invalid JSON", bad.stderr)
        array = run(["--stdin"], stdin='["' + CELL + '"]')
        self.assertEqual(array.returncode, 2)
        self.assertNotIn(CELL, array.stdout + array.stderr)
        self.assertIn("JSON must be an object", array.stderr)

    def test_missing_file(self):
        result = run(["--file", str(ROOT / "no-such.json")])
        self.assertEqual(result.returncode, 2)
        self.assertIn("file not found", result.stderr)


if __name__ == "__main__":
    unittest.main()
