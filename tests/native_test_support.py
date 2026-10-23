"""Software test doubles only: native dicts, no CSV fixture or serialization.

Exercise our CLI, validation and scoring against DictReader's documented row
contract. The standard-library CSV parser is not reimplemented here. Never use
these deliberately fictional records as research, prospect data or downloads.
"""
import contextlib
import copy
import importlib.util
import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(script):
    name = "_withdrawal_test_" + script.replace(".", "_")
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / script)
        value = importlib.util.module_from_spec(spec)
        sys.modules[name] = value
        spec.loader.exec_module(value)
    return sys.modules[name]


class NativeReader:
    def __init__(self, rows, header):
        self.fieldnames = header
        self.rows = rows

    def __iter__(self):
        return iter(copy.deepcopy(self.rows))


def run_native(script, args, rows, header=None):
    """Actual argparse/main/scoring, mocked private bytes and library row boundary."""
    target = module(script)
    header = header if header is not None else list(rows[0]) if rows else []
    original_read = target.read_text
    reads = []

    def private_read(path):
        if path.suffix == ".json":
            return original_read(path)  # The existing example brand configuration.
        reads.append(path)
        return "opaque test input"  # Not a serialized sample or a physical file.

    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(sys, "argv", [script, *args]))
        stack.enter_context(patch.object(target, "read_text", side_effect=private_read))
        stack.enter_context(patch.object(target, "read_stdin_text", return_value="opaque test input"))
        reader = stack.enter_context(patch.object(target.csv, "DictReader", return_value=NativeReader(rows, header)))
        if hasattr(target, "FREE_EMAIL_DOMAINS"):
            stack.enter_context(patch.object(target, "FREE_EMAIL_DOMAINS", target.FREE_EMAIL_DOMAINS | {"free-mail.example"}))
        stack.enter_context(contextlib.redirect_stdout(stdout))
        stack.enter_context(contextlib.redirect_stderr(stderr))
        try:
            code = target.main()
        except SystemExit as error:
            code = error.code
    result = subprocess.CompletedProcess([script, *args], code, stdout.getvalue(), stderr.getvalue())
    result.reads = reads
    result.reader_calls = reader.call_count
    return result


def prospect_rows():
    """One native row per scoring branch; all mailboxes use reserved domains."""
    def row(email, **changes):
        return dict(email=email, role="CRO", company="Fictional Test", stage="Series B",
                    industry="SaaS", signal="Synthetic unit-test signal", signal_date="2026-10-03", **changes)
    rows = [row("unit@account.example"), row("unit@account.example"),
            row("role@account.example"), row("stale@account.example"),
            row("info@role.example"), row("unit@free-mail.example"), row("excluded@account.example")]
    rows[2]["role"] = "Teacher"
    rows[3]["signal_date"] = "2020-01-01"
    rows[6]["industry"] = "Government"
    return rows
