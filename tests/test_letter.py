#!/usr/bin/env python3
"""score.py prints one letter plus the lint, or refuses a demographic email."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CELL = "super-secret-cell"


def run(args, stdin=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "score.py"), *args],
        input=stdin,
        capture_output=True,
        text=True,
    )


class ScoreLetter(unittest.TestCase):
    def test_good_draft_prints_letter_and_lint(self):
        result = run(["--file", str(ROOT / "examples" / "letter-good.json")])
        self.assertEqual(result.returncode, 0)
        self.assertIn("Demand Gen Lead role four days ago.", result.stdout)
        self.assertIn("lint: ", result.stdout)
        self.assertNotIn("demographic email", result.stdout)
        words = result.stdout.strip().splitlines()[0]
        self.assertLess(len(words.split()), 90)

    def test_demographic_exits_1(self):
        result = run(["--file", str(ROOT / "examples" / "letter-demographic.json")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("demographic email", result.stdout)
        self.assertNotIn("lint:", result.stdout)

    def test_missing_signal_exits_1(self):
        result = run(["--stdin"], stdin='{"public_signal":"","letter":"A note about the post."}')
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing public signal", result.stdout)
        self.assertNotIn("lint:", result.stdout)

    def test_bad_json_hides_input(self):
        bad = run(["--stdin"], stdin='{"letter": "' + CELL)
        self.assertNotEqual(bad.returncode, 0)
        self.assertNotIn(CELL, bad.stdout + bad.stderr)
        self.assertIn("invalid JSON", bad.stderr)
        array = run(["--stdin"], stdin='["' + CELL + '"]')
        self.assertNotEqual(array.returncode, 0)
        self.assertNotIn(CELL, array.stdout + array.stderr)
        self.assertIn("JSON must be an object", array.stderr)


if __name__ == "__main__":
    unittest.main()
