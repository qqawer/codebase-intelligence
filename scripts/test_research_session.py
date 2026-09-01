#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SESSION = SCRIPT_DIR / "research_session.py"
RUN = SCRIPT_DIR / "research_run.py"
LEDGER = SCRIPT_DIR / "candidate_ledger.py"


class ResearchSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.checkout = self.root / "checkout"
        self.research = self.root / "research"
        self.checkout.mkdir()
        self.research.mkdir()
        subprocess.run(["git", "init", "-q", str(self.checkout)], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "remote", "add", "origin", "git@github.com:example/project.git"], check=True)
        (self.checkout / "main.py").write_text("one\ntwo\nthree\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.checkout), "add", "main.py"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "commit", "-qm", "fixture"], check=True)
        self.revision = subprocess.run(["git", "-C", str(self.checkout), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()
        (self.research / "runs.json").write_text(json.dumps({"schema_version": 2, "skill_repository": "https://github.com/example/skill", "runs": []}) + "\n", encoding="utf-8")
        (self.research / "README.md").write_text("# Research\n\n## Full report examples\n\n<!-- BEGIN GENERATED FULL REPORT INDEX -->\n| Repository | Revision | Runtime validation | Report |\n|---|---|---|---|\n<!-- END GENERATED FULL REPORT INDEX -->\n\n## Next\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def command(self, script: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(script), *arguments], text=True, capture_output=True, check=False)

    def initialize(self) -> Path:
        completed = self.command(
            SESSION, "init", "--checkout", str(self.checkout), "--research-root", str(self.research),
            "--skill-ref", "c" * 40, "--analysis-date", "2026-09-01", "--format", "json",
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        return Path(json.loads(completed.stdout)["report_directory"])

    def test_init_fixes_identity_inventory_and_next_gate(self) -> None:
        report_dir = self.initialize()
        record = json.loads((report_dir / "run-record.json").read_text(encoding="utf-8"))
        ledger = json.loads((report_dir / "candidate-ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(report_dir.resolve(), (self.research / "reports" / "example-project" / self.revision[:7]).resolve())
        self.assertEqual(record["phase"], "inventoried")
        self.assertEqual(record["target"]["revision"], self.revision)
        self.assertEqual(record["target"]["repository"], "https://github.com/example/project.git")
        self.assertEqual(ledger["run_id"], record["run_id"])
        self.assertTrue((report_dir / "repository-snapshot.json").is_file())
        status = self.command(SESSION, "status", str(report_dir), "--format", "json")
        value = json.loads(status.stdout)
        self.assertEqual(value["next_phase"], "candidates-frozen")
        self.assertFalse(value["ready"])
        self.assertTrue(any("candidate ledger" in item for item in value["blockers"]))

    def test_init_rejects_dirty_checkout_without_creating_session(self) -> None:
        (self.checkout / "main.py").write_text("dirty\n", encoding="utf-8")
        completed = self.command(SESSION, "init", "--checkout", str(self.checkout), "--research-root", str(self.research), "--skill-ref", "c" * 40)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("clean target worktree", completed.stderr)
        self.assertFalse((self.research / "reports").exists())

    def test_publish_strictly_validates_finalizes_and_indexes(self) -> None:
        report_dir = self.initialize()
        ledger_path = report_dir / "candidate-ledger.json"
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        ledger["coverage"] = [{"area": "entrypoint", "status": "analyzed", "depth": 3, "importance": "high", "notes": "traced"}]
        ledger["traces"] = [{"name": "main", "summary": "representative", "steps": ["enter", "return"]}]
        ledger["candidates"] = [{
            "id": "representative-mechanism", "name": "Representative mechanism", "rank": 1, "tier": 3,
            "parent": "", "problem": "fixture problem", "mechanism": "fixture mechanism", "value": "fixture value",
            "evidence": ["main.py:1-3"], "counterevidence": ["fixture limitation"], "provenance": "conventional",
            "runtime_hypotheses": ["tests pass"], "nested_scan": "",
        }]
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(self.command(LEDGER, "freeze", "--ledger", str(ledger_path), "--note", "fixture freeze").returncode, 0)
        record = report_dir / "run-record.json"
        self.assertEqual(self.command(RUN, "advance", "--record", str(record), "--to", "candidates-frozen", "--artifact", f"candidate_ledger={ledger_path}").returncode, 0)
        self.assertEqual(self.command(RUN, "note", "--record", str(record), "--category", "tests", "--status", "passed", "--reason", "fixture tests").returncode, 0)
        self.assertEqual(self.command(RUN, "advance", "--record", str(record), "--to", "runtime-validated").returncode, 0)
        self.assertEqual(self.command(RUN, "note", "--record", str(record), "--category", "comparator-review", "--status", "observed", "--reason", "fixture comparator").returncode, 0)
        self.assertEqual(self.command(RUN, "advance", "--record", str(record), "--to", "comparators-reviewed").returncode, 0)
        report = report_dir / "PROJECT_INTELLIGENCE_REPORT.md"
        report.write_text(
            f"""# Example Project Intelligence Report

Analysis date: 2026-09-01
Revision: `{self.revision}`
Source mode: `local-pinned`
Worktree: clean

## Runtime validation

Project tests passed.

## Uncertainty ledger

This fixture has evidence limitations.

## Coverage ledger

[source](https://github.com/example/project/blob/{self.revision}/main.py#L1-L3)
""",
            encoding="utf-8",
        )
        self.assertEqual(self.command(RUN, "advance", "--record", str(record), "--to", "synthesized", "--artifact", f"report={report}").returncode, 0)
        missing_checkout = self.command(
            SESSION, "publish", str(report_dir), "--research-root", str(self.research),
            "--verdict", "PASS WITH EVIDENCE LIMITATIONS",
        )
        self.assertNotEqual(missing_checkout.returncode, 0)
        self.assertIn("requires --target-checkout", missing_checkout.stderr)
        self.assertEqual(json.loads(record.read_text(encoding="utf-8"))["phase"], "synthesized")
        published = self.command(
            SESSION, "publish", str(report_dir), "--research-root", str(self.research),
            "--target-checkout", str(self.checkout), "--verdict", "PASS WITH EVIDENCE LIMITATIONS",
        )
        self.assertEqual(published.returncode, 0, published.stdout + published.stderr)
        finalized = json.loads(record.read_text(encoding="utf-8"))
        index = json.loads((self.research / "runs.json").read_text(encoding="utf-8"))
        self.assertEqual(finalized["phase"], "finalized")
        self.assertTrue((report_dir / "validation-receipt.json").is_file())
        self.assertEqual(index["generated_run_records"], 1)
        self.assertEqual(index["runs"][0]["id"], finalized["run_id"])
        self.assertEqual(json.loads(self.command(SESSION, "status", str(report_dir), "--format", "json").stdout)["phase"], "finalized")


if __name__ == "__main__":
    unittest.main()
