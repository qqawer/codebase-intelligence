#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("research_run.py")


class ResearchRunTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.record = self.root / "run-record.json"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "init",
                "--output",
                str(self.record),
                "--run-id",
                "fixture-run",
                "--run-class",
                "behavior-validated-blind",
                "--target-repository",
                "https://user:secret@github.com/example/project.git?token=secret#fragment",
                "--target-revision",
                "a" * 40,
                "--skill-ref",
                "b" * 40,
                "--source-mode",
                "local-pinned",
                "--worktree-state",
                "clean",
            ],
            check=True,
            capture_output=True,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def load(self) -> dict:
        return json.loads(self.record.read_text(encoding="utf-8"))

    def test_init_sanitizes_remote_and_records_identity(self) -> None:
        value = self.load()
        self.assertEqual(value["target"]["repository"], "https://github.com/example/project.git")
        self.assertEqual(value["target"]["worktree_state"], "clean")
        self.assertEqual(value["entries"], [])

    def test_exec_records_logs_hash_and_redacts_secret_options(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "exec",
                "--record",
                str(self.record),
                "--category",
                "test",
                "--cwd",
                str(self.root),
                "--",
                sys.executable,
                "-c",
                "print('ok')",
                "--token",
                "secret-value",
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0)
        entry = self.load()["entries"][0]
        self.assertEqual(entry["status"], "passed")
        self.assertEqual(entry["argv"][-1], "[REDACTED]")
        self.assertTrue((self.root / entry["stdout_log"]).is_file())
        self.assertRegex(entry["output_sha256"], r"^[0-9a-f]{64}$")

    def test_note_and_finalize_create_granular_summary(self) -> None:
        subprocess.run(
            [sys.executable, str(SCRIPT), "note", "--record", str(self.record), "--category", "rust-tests", "--status", "unavailable", "--reason", "cargo missing"],
            check=True,
        )
        for phase in ("inventoried", "candidates-frozen", "runtime-validated", "comparators-reviewed", "synthesized", "report-validated"):
            subprocess.run(
                [sys.executable, str(SCRIPT), "advance", "--record", str(self.record), "--to", phase, "--retrospective", "--reason", "fixture migration"],
                check=True,
                capture_output=True,
            )
        subprocess.run([sys.executable, str(SCRIPT), "finalize", "--record", str(self.record), "--report", "PROJECT_INTELLIGENCE_REPORT.md", "--candidate-ledger", "candidate-ledger.json", "--verdict", "PASS WITH EVIDENCE LIMITATIONS"], check=True)
        value = self.load()
        self.assertEqual(value["runtime_summary"]["counts"]["unavailable"], 1)
        self.assertFalse(value["runtime_summary"]["end_to_end"])
        self.assertEqual(value["phase"], "finalized")
        self.assertTrue(any(item.get("bypassed_gates") for item in value["phase_history"]))

    def test_phase_transitions_are_sequential_and_gated(self) -> None:
        skipped = subprocess.run(
            [sys.executable, str(SCRIPT), "advance", "--record", str(self.record), "--to", "candidates-frozen"],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(skipped.returncode, 0)
        self.assertIn("sequential", skipped.stderr)
        missing = subprocess.run(
            [sys.executable, str(SCRIPT), "advance", "--record", str(self.record), "--to", "inventoried"],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("repository_snapshot", missing.stderr)

    def test_validation_receipt_must_match_current_report(self) -> None:
        subprocess.run([sys.executable, str(SCRIPT), "note", "--record", str(self.record), "--category", "test", "--status", "not-run", "--reason", "fixture"], check=True)
        for phase in ("inventoried", "candidates-frozen"):
            subprocess.run([sys.executable, str(SCRIPT), "advance", "--record", str(self.record), "--to", phase, "--retrospective", "--reason", "fixture"], check=True, capture_output=True)
        subprocess.run([sys.executable, str(SCRIPT), "advance", "--record", str(self.record), "--to", "runtime-validated"], check=True)
        subprocess.run([sys.executable, str(SCRIPT), "note", "--record", str(self.record), "--category", "comparator-review", "--status", "not-run", "--reason", "not requested"], check=True)
        subprocess.run([sys.executable, str(SCRIPT), "advance", "--record", str(self.record), "--to", "comparators-reviewed"], check=True)
        report = self.root / "PROJECT_INTELLIGENCE_REPORT.md"
        report.write_text("# Report\n", encoding="utf-8")
        subprocess.run([sys.executable, str(SCRIPT), "advance", "--record", str(self.record), "--to", "synthesized", "--artifact", f"report={report}"], check=True)
        receipt = self.root / "validation-receipt.json"
        receipt.write_text(json.dumps({"errors": 0, "report_sha256": "0" * 64}), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "advance", "--record", str(self.record), "--to", "report-validated", "--artifact", f"validation_receipt={receipt}"],
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("does not match", completed.stderr)


if __name__ == "__main__":
    unittest.main()
