#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("build_research_index.py")


class BuildResearchIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        report_dir = self.root / "reports" / "example-project" / "a1b2c3d"
        report_dir.mkdir(parents=True)
        (report_dir / "PROJECT_INTELLIGENCE_REPORT.md").write_text("# Example Project Intelligence Report\n", encoding="utf-8")
        (report_dir / "candidate-ledger.json").write_text("{}\n", encoding="utf-8")
        record = {
            "schema_version": 2,
            "run_id": "generated-run",
            "run_class": "full-project-intelligence-report",
            "analysis_date": "2026-09-01",
            "source_mode": "local-pinned",
            "target": {"repository": "https://github.com/example/project.git", "revision": "a" * 40},
            "skill": {"revision": "b" * 40},
            "artifacts": {"report": "PROJECT_INTELLIGENCE_REPORT.md", "candidate_ledger": "candidate-ledger.json"},
            "verdict": "PASS",
            "runtime_summary": {"counts": {"passed": 2, "unavailable": 1}, "end_to_end": False},
            "phase": "finalized",
        }
        (report_dir / "run-record.json").write_text(json.dumps(record), encoding="utf-8")
        legacy_report = self.root / "reports" / "legacy" / "PROJECT_INTELLIGENCE_REPORT.md"
        legacy_report.parent.mkdir(parents=True)
        legacy_report.write_text("# Legacy Project Intelligence Report\n", encoding="utf-8")
        self.index = {
            "schema_version": 1,
            "skill_repository": "https://github.com/qqawer/codebase-intelligence",
            "runs": [
                {"id": "legacy", "date": "2026-08-31", "class": "full-project-intelligence-report", "target_repository": "https://github.com/example/legacy.git", "target_revision": "c" * 40, "report": "reports/legacy/PROJECT_INTELLIGENCE_REPORT.md", "runtime": "Legacy evidence"},
                {"id": "generated-run", "date": "old", "runtime": "Detailed runtime wording", "report": "wrong", "record_status": "legacy report without run-record.json"},
            ],
        }
        (self.root / "runs.json").write_text(json.dumps(self.index), encoding="utf-8")
        (self.root / "README.md").write_text("# Research\n\n## Full report examples\n\nold\n\n## Next\n\ntext\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_script(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), str(self.root), *extra], text=True, capture_output=True, check=False)

    def test_write_preserves_legacy_and_generates_record_entry_and_table(self) -> None:
        completed = self.run_script("--write")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        value = json.loads((self.root / "runs.json").read_text(encoding="utf-8"))
        self.assertEqual(value["schema_version"], 2)
        self.assertEqual(value["generated_run_records"], 1)
        by_id = {item["id"]: item for item in value["runs"]}
        self.assertIn("legacy", by_id)
        self.assertEqual(by_id["generated-run"]["target_revision"], "a" * 40)
        self.assertEqual(by_id["generated-run"]["runtime"], "Detailed runtime wording")
        self.assertNotIn("record_status", by_id["generated-run"])
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        self.assertIn("BEGIN GENERATED FULL REPORT INDEX", readme)
        self.assertIn("| Example |", readme)
        self.assertIn("| Legacy |", readme)
        self.assertEqual(self.run_script().returncode, 0)

    def test_check_detects_drift(self) -> None:
        completed = self.run_script()
        self.assertEqual(completed.returncode, 1)
        self.assertIn("drift", completed.stdout)


if __name__ == "__main__":
    unittest.main()
