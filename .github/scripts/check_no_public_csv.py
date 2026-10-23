#!/usr/bin/env python3
"""Reject tracked CSV paths using Git metadata only; never read file contents.
Future exceptions require Jay's exact-file approval and a reviewed guard change.
There is deliberately no environment/CLI bypass or blanket allowlist.
"""
import json
import subprocess


def csv_paths(names):
    return [name.decode("utf-8", "surrogateescape") for name in names.split(b"\0")
            if name and name.lower().endswith(b".csv")]


# Filename-only regression checks: no CSV file or serialized sample is created.
assert csv_paths(b"README.md\0examples/withdrawn.CSV\0folder/space name.csv\0source/parser.py\0") == [
    "examples/withdrawn.CSV", "folder/space name.csv"]
assert csv_paths(b"source/csv_parser.py\0notes.csv.md\0") == []

if __name__ == "__main__":
    paths = csv_paths(subprocess.check_output(["git", "ls-files", "-z"]))
    for path in paths:
        print("::error::Unapproved tracked CSV path: " + json.dumps(path))
    print("public-csv guard: " + str(len(paths)) + " tracked CSV paths")
    raise SystemExit(1 if paths else 0)
