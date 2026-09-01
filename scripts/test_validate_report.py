#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_report.py")


class ValidateReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.checkout = self.root / "checkout"
        self.checkout.mkdir()
        subprocess.run(["git", "init", "-q", str(self.checkout)], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.name", "Test"], check=True)
        (self.checkout / "main.py").write_text("one\ntwo\nthree\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.checkout), "add", "main.py"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "commit", "-qm", "fixture"], check=True)
        self.revision = subprocess.run(["git", "-C", str(self.checkout), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
        self.report = self.root / "PROJECT_INTELLIGENCE_REPORT.md"
        self.record = self.root / "run-record.json"
        self.ledger = self.root / "candidate-ledger.md"
        self.index = self.root / "runs.json"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_record(self, **changes: object) -> None:
        value = {
            "schema_version": 2,
            "run_id": "fixture",
            "run_class": "behavior-validated-blind",
            "analysis_date": "2026-09-01",
            "source_mode": "local-pinned",
            "target": {"repository": "https://github.com/example/project.git", "revision": self.revision, "worktree_state": "clean"},
            "skill": {"revision": "b" * 40},
            "entries": [{"kind": "command", "category": "test", "status": "passed"}],
            "phase": "synthesized",
            "phase_history": [{"phase": "initialized"}, {"phase": "synthesized"}],
            "verdict": "PASS",
        }
        value.update(changes)
        self.record.write_text(json.dumps(value), encoding="utf-8")

    def run_validator(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.report), "--run-record", str(self.record), "--candidate-ledger", str(self.ledger), "--target-checkout", str(self.checkout), "--run-index", str(self.index), "--format", "json", *extra],
            check=False,
            text=True,
            capture_output=True,
        )

    def test_valid_report_has_no_findings(self) -> None:
        self.ledger.write_text("# Frozen candidates\n", encoding="utf-8")
        self.index.write_text(json.dumps({"runs": [{"id": "fixture", "target_revision": self.revision}]}), encoding="utf-8")
        self.report.write_text(
            f"""# Project Intelligence Report

Analysis date: 2026-09-01  
Revision: `{self.revision}`  
Source mode: `local-pinned`  
Worktree: clean

## Runtime validation

Project tests passed.

## Uncertainty ledger

End-to-end behavior was not run.

## Coverage ledger

Entrypoint traced. [source](https://github.com/example/project/blob/{self.revision}/main.py#L1-L3)
""",
            encoding="utf-8",
        )
        self.write_record()
        completed = self.run_validator()
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["findings"], [])

    def test_detects_revision_paths_lines_and_missing_test_evidence(self) -> None:
        self.ledger.write_text("# Frozen candidates\n", encoding="utf-8")
        self.index.write_text(json.dumps({"runs": [{"id": "fixture", "target_revision": self.revision}]}), encoding="utf-8")
        self.report.write_text(
            f"""# Report

Revision: `{self.revision}`. Tests passed. /Users/private/source

## Runtime validation
## Uncertainty ledger
## Coverage ledger

[bad](https://github.com/example/project/blob/main/missing.py#L9-L2)
""",
            encoding="utf-8",
        )
        self.write_record(entries=[])
        completed = self.run_validator()
        self.assertNotEqual(completed.returncode, 0)
        codes = {item["code"] for item in json.loads(completed.stdout)["findings"]}
        self.assertTrue({"machine-path", "link-revision", "mutable-source-link", "line-range", "link-path", "test-evidence"}.issubset(codes))

    def test_measured_outcome_requires_benchmark_evidence(self) -> None:
        self.ledger.write_text("# Frozen candidates\n", encoding="utf-8")
        self.index.write_text(json.dumps({"runs": [{"id": "fixture", "target_revision": self.revision}]}), encoding="utf-8")
        self.report.write_text(
            f"""# Project Intelligence Report

Analysis date: 2026-09-01  
Revision: `{self.revision}`  
Source mode: `local-pinned`  
Worktree: clean

## Runtime validation

Project tests passed and the implementation was measured to be 25% faster than the baseline.

## Uncertainty ledger

Measurement details remain uncertain.

## Coverage ledger

[source](https://github.com/example/project/blob/{self.revision}/main.py#L1-L3)
""",
            encoding="utf-8",
        )
        self.write_record()
        completed = self.run_validator()
        codes = {item["code"] for item in json.loads(completed.stdout)["findings"]}
        self.assertIn("measurement-evidence", codes)

    def test_negated_external_measurement_does_not_require_passed_benchmark(self) -> None:
        self.ledger.write_text("# Frozen candidates\n", encoding="utf-8")
        self.index.write_text(json.dumps({"runs": [{"id": "fixture", "target_revision": self.revision}]}), encoding="utf-8")
        self.report.write_text(
            f"""# Project Intelligence Report

Analysis date: 2026-09-01
Revision: `{self.revision}`
Source mode: `local-pinned`
Worktree: clean

## Runtime validation

Project tests passed. This run did not independently reproduce the `10-100x faster than baseline` headline.

## Uncertainty ledger

Performance remains unmeasured here.

## Coverage ledger

[source](https://github.com/example/project/blob/{self.revision}/main.py#L1-L3)
""",
            encoding="utf-8",
        )
        self.write_record()
        completed = self.run_validator()
        codes = {item["code"] for item in json.loads(completed.stdout)["findings"]}
        self.assertNotIn("measurement-evidence", codes)

    def test_unrelated_negation_does_not_hide_measurement_claim(self) -> None:
        self.ledger.write_text("# Frozen candidates\n", encoding="utf-8")
        self.index.write_text(json.dumps({"runs": [{"id": "fixture", "target_revision": self.revision}]}), encoding="utf-8")
        self.report.write_text(
            f"""# Project Intelligence Report

Analysis date: 2026-09-01
Revision: `{self.revision}`
Source mode: `local-pinned`
Worktree: clean

## Runtime validation

Project tests passed. We did not benchmark startup, but throughput was measured to be 25% faster than baseline.

## Uncertainty ledger

Startup remains unmeasured.

## Coverage ledger

[source](https://github.com/example/project/blob/{self.revision}/main.py#L1-L3)
""",
            encoding="utf-8",
        )
        self.write_record()
        completed = self.run_validator()
        codes = {item["code"] for item in json.loads(completed.stdout)["findings"]}
        self.assertIn("measurement-evidence", codes)


if __name__ == "__main__":
    unittest.main()
