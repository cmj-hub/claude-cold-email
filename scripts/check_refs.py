#!/usr/bin/env python3
"""
check_refs.py — Fail when a skill, agent, or doc points at a file that
does not exist.

Skills tell the agent to "load references/x.md" or "run scripts/y.py".
A dead path there means the agent improvises, so CI checks every
relative path (containing a "/") in backticks or markdown links across
the pack's markdown. A path counts as found if it resolves from the
file's own directory, the skill's directory, or the repo root.

Zero dependencies. Python 3.8+.

USAGE:
    python3 scripts/check_refs.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ["AGENTS.md", "README.md", "CONTRIBUTING.md", "SOUL.md"]
DIRS = ["skills", "agents"]
EXTS = (".md", ".py", ".sh", ".json", ".csv", ".jsonl", ".png", ".gif")

TOKEN_RE = re.compile(r"`([^`\s]+)`|\]\(([^)\s]+)\)")


def candidates(md: Path, ref: str):
    yield md.parent / ref
    parts = md.relative_to(ROOT).parts
    if len(parts) >= 2 and parts[0] == "skills":
        yield ROOT / "skills" / parts[1] / ref
    yield ROOT / ref


def is_checkable(ref: str) -> bool:
    if "/" not in ref or "://" in ref or ref.startswith(("#", "mailto:")):
        return False
    if any(ch in ref for ch in "<>{}*$"):
        return False
    return ref.split("#")[0].endswith(EXTS)


def main() -> int:
    files = [ROOT / d for d in DOCS if (ROOT / d).is_file()]
    for d in DIRS:
        files += sorted((ROOT / d).rglob("*.md"))

    missing = []
    for md in files:
        text = md.read_text(encoding="utf-8")
        for n, line in enumerate(text.splitlines(), start=1):
            for m in TOKEN_RE.finditer(line):
                ref = (m.group(1) or m.group(2)).split("#")[0]
                if not is_checkable(ref):
                    continue
                if not any(c.exists() for c in candidates(md, ref)):
                    missing.append(f"{md.relative_to(ROOT)}:{n}: {ref}")

    if missing:
        print("✗ Dead references:")
        for item in missing:
            print(f"  {item}")
        return 1
    print(f"✓ All file references resolve ({len(files)} files checked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
