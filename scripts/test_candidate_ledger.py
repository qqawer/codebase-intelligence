#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("candidate_ledger.py")


class CandidateLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.ledger = self.root / "candidate-ledger.json"
        subprocess.run(
            [sys.executable, str(SCRIPT), "init", "--output", str(self.ledger), "--run-id", "fixture", "--target-repository", "https://github.com/example/project.git", "--target-revision", "a" * 40, "--skill-ref", "b" * 40, "--source-mode", "local-pinned", "--freeze-boundary", "Before project-public documentation"],
            check=True,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *args], check=check, text=True, capture_output=True)

    def populate(self) -> None:
        self.run_cli("coverage", "--ledger", str(self.ledger), "--area", "runtime", "--status", "analyzed", "--depth", "4", "--importance", "high", "--notes", "entrypoint and failure paths")
        self.run_cli("trace", "--ledger", str(self.ledger), "--name", "request", "--summary", "Representative request path", "--step", "enter", "--step", "exit")
        self.run_cli("add", "--ledger", str(self.ledger), "--id", "process-lifecycle", "--name", "Process lifecycle", "--rank", "1", "--tier", "4", "--problem", "Descendants can outlive the parent", "--mechanism", "Own a process group", "--value", "Bounds cancellation lifecycle", "--evidence", "src/process.rs:1-20", "--counterevidence", "Windows path not executed", "--provenance", "repository-original", "--runtime-hypothesis", "descendants terminate")

    def test_freeze_hash_detects_post_freeze_tampering(self) -> None:
        self.populate()
        self.run_cli("freeze", "--ledger", str(self.ledger), "--note", "Frozen before docs")
        valid = self.run_cli("validate", "--ledger", str(self.ledger), "--require-frozen", check=False)
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        value = json.loads(self.ledger.read_text(encoding="utf-8"))
        value["candidates"][0]["rank"] = 2
        self.ledger.write_text(json.dumps(value), encoding="utf-8")
        invalid = self.run_cli("validate", "--ledger", str(self.ledger), "--require-frozen", check=False)
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("content hash", invalid.stdout)

    def test_frozen_ledger_cannot_be_modified_and_renders(self) -> None:
        self.populate()
        self.run_cli("freeze", "--ledger", str(self.ledger), "--note", "Frozen before docs")
        mutation = self.run_cli("coverage", "--ledger", str(self.ledger), "--area", "other", "--status", "gap", "--depth", "0", "--importance", "low", check=False)
        self.assertNotEqual(mutation.returncode, 0)
        rendered = self.run_cli("render", "--ledger", str(self.ledger), "--require-frozen")
        self.assertIn("Process lifecycle", rendered.stdout)
        self.assertIn("Content SHA-256", rendered.stdout)

    def test_freeze_requires_coverage_trace_and_candidate(self) -> None:
        completed = self.run_cli("freeze", "--ledger", str(self.ledger), "--note", "too early", check=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("coverage", completed.stderr)


if __name__ == "__main__":
    unittest.main()
