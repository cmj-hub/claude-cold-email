#!/usr/bin/env python3
"""Scoring behaviour: whole-word lexicons, acronyms, reply routing, list scoring."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_deliverability  # noqa: E402
import score_reply  # noqa: E402
import score_subject_line  # noqa: E402
import spam_word_lint  # noqa: E402


def run(script, args, env=None):
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        capture_output=True,
        text=True,
        timeout=10,
        env=env,
    )


def lint_flags(subject, body=""):
    result = spam_word_lint.lint(subject, body)
    return [f.pattern for a in result.axes for f in a.flags], result.total_score


class SpamLint(unittest.TestCase):
    def test_trigger_words_match_whole_words(self):
        flags, score = lint_flags("Accredited GTM team", "Insurgent brands get credited for lifetime value.")
        self.assertEqual(flags, [])
        self.assertEqual(score, 100)

    def test_trigger_word_still_fires(self):
        flags, _ = lint_flags("Quick note", "Act now, it's urgent.")
        self.assertIn("act now", flags)
        self.assertIn("urgent", flags)

    def test_acronyms_are_not_shouting(self):
        flags, _ = lint_flags("Q3 SDR plan for the CRO")
        self.assertFalse([f for f in flags if "caps" in f])

    def test_shouting_is_flagged(self):
        for subject in ("URGENT pricing", "ACT NOW please"):
            flags, _ = lint_flags(subject)
            self.assertTrue([f for f in flags if "caps" in f], subject)

    def test_curly_apostrophe_clickbait(self):
        flags, _ = lint_flags("Hi", "You won’t believe this.")
        self.assertIn("you won't believe", flags)


class SubjectLine(unittest.TestCase):
    def test_learn_is_not_earn(self):
        result = score_subject_line.score_subject("Learn how Acme cut SDR ramp")
        self.assertFalse([f for f in result.flags if "Spam-trigger" in f])

    def test_banned_patterns_never_ship(self):
        for subject in ("Re: quick question", "URGENT pricing", "Pipeline gap \U0001F680"):
            result = score_subject_line.score_subject(subject)
            self.assertLess(result.score, 70, subject)

    def test_strong_subject_ships(self):
        self.assertGreaterEqual(score_subject_line.score_subject("Pipeline gap after the Q3 freeze?").score, 85)


class ReplyScoring(unittest.TestCase):
    def cat(self, body):
        return score_reply.classify(body)

    def test_pricing_question_is_buy_signal(self):
        self.assertEqual(self.cat("Sure, what does pricing look like for a team of 10?").category, "buy-signal")

    def test_substring_does_not_score(self):
        r = self.cat("We need to ensure the pressure on pipeline drops")
        self.assertEqual(r.category, "neutral")
        self.assertTrue(r.needs_review)

    def test_short_unknown_goes_to_review_not_suppression(self):
        for body in ("Who is this?", "ok"):
            r = self.cat(body)
            self.assertNotEqual(r.category, "not-interested", body)
            self.assertTrue(r.needs_review, body)

    def test_curly_apostrophe(self):
        self.assertEqual(self.cat("Let’s set up a call — Thursday works").category, "buy-signal")

    def test_stop_alone_vs_in_sentence(self):
        self.assertEqual(self.cat("Stop").category, "not-interested")
        self.assertNotEqual(self.cat("Don't stop sending these, great reads").category, "not-interested")

    def test_unsubscribe(self):
        self.assertEqual(self.cat("Please unsubscribe me").category, "not-interested")


class ListScoring(unittest.TestCase):
    def score(self, *extra):
        result = run("score_list.py", [
            "--input", str(ROOT / "examples" / "prospects.csv"),
            "--today", "2026-10-04", "--format", "json", *extra,
        ])
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return json.loads(result.stdout)

    def test_sample_with_brand_config(self):
        data = self.score("--brand-config", str(ROOT / "brand-config.example.json"))
        reasons = {r["row"]: r["reason"] for r in data["remove"]}
        self.assertIn("same email", reasons[2])
        self.assertIn("outside icp.role_targets", reasons[3])
        self.assertIn("stale", reasons[4])
        self.assertIn("role account", reasons[5])
        self.assertIn("free-mail", reasons[6])
        self.assertIn("exclusion", reasons[7])
        self.assertLess(data["score"], 60)

    def test_axes_without_data_are_not_scored(self):
        data = self.score()
        na = {a["axis"] for a in data["axes"] if a["score"] is None}
        self.assertEqual(na, {"role-fit", "exclusion", "company-stage"})

    def test_write_splits_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "list.csv"
            src.write_text(
                "email,role\nsam@acme.example,VP Demand Gen\nsam@acme.example,VP Demand Gen\n",
                encoding="utf-8",
            )
            result = run("score_list.py", ["--input", str(src), "--write"])
            self.assertIn(result.returncode, (0, 1), result.stderr)
            cleaned = (Path(tmp) / "list.cleaned.csv").read_text(encoding="utf-8").splitlines()
            removed = (Path(tmp) / "list.removed.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(cleaned), 2)
        self.assertEqual(len(removed), 2)
        self.assertIn("removal_reason", removed[0])

    def test_bad_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            path.write_text("name\nx\n", encoding="utf-8")
            result = run("score_list.py", ["--input", str(path)])
            self.assertEqual(result.returncode, 2)
            missing = run("score_list.py", ["--input", str(Path(tmp) / "none.csv")])
            self.assertEqual(missing.returncode, 2)
            self.assertNotIn("Traceback", missing.stderr)


class Deliverability(unittest.TestCase):
    def test_missing_dig_is_an_error_not_a_failed_domain(self):
        env = dict(os.environ, PATH=tempfile.gettempdir())
        result = run("check_deliverability.py", ["--domain", "example.com"], env=env)
        self.assertEqual(result.returncode, 2)
        self.assertIn("dig", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_dnsbl_answers(self):
        f = check_deliverability._dnsbl_answer
        self.assertIs(f("dbl.spamhaus.org", ""), False)
        self.assertIs(f("dbl.spamhaus.org", "127.0.1.2"), True)
        self.assertIsNone(f("dbl.spamhaus.org", "127.255.255.254"))
        self.assertIs(f("multi.surbl.org", "127.0.0.64"), True)
        self.assertIsNone(f("multi.surbl.org", "127.0.0.1"))

    def test_unknown_checks_are_not_scored(self):
        checks = check_deliverability.check_bulk_sender_compliance(True, True)
        self.assertEqual([c.status for c in checks], ["pass", "pass", "unknown", "unknown"])


if __name__ == "__main__":
    unittest.main()
