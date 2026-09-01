#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import candidate_ledger


SCRIPT = Path(__file__).with_name("comparator_ledger.py")


class ComparatorLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.record = self.root / "run-record.json"
        self.candidates = self.root / "candidate-ledger.json"
        self.ledger = self.root / "comparator-ledger.json"
        revision = "a" * 40
        skill = "b" * 40
        self.record.write_text(json.dumps({
            "run_id": "fixture", "target": {"repository": "https://github.com/example/project.git", "revision": revision},
            "skill": {"revision": skill},
        }), encoding="utf-8")
        candidate_value = {
            "schema_version": 1, "run_id": "fixture",
            "target": {"repository": "https://github.com/example/project.git", "revision": revision},
            "skill_revision": skill, "source_mode": "local-pinned", "freeze_boundary": "fixture",
            "coverage": [{"area": "core", "status": "analyzed", "depth": 3, "importance": "high", "notes": "fixture"}],
            "traces": [{"name": "main", "summary": "fixture", "steps": ["enter"]}],
            "candidates": [
                {"id": "major-one", "name": "Major one", "rank": 1, "tier": 4, "problem": "p", "mechanism": "m", "value": "v", "evidence": ["e"], "counterevidence": ["c"], "provenance": "unknown"},
                {"id": "major-two", "name": "Major two", "rank": 2, "tier": 3, "problem": "p", "mechanism": "m", "value": "v", "evidence": ["e"], "counterevidence": ["c"], "provenance": "unknown"},
                {"id": "minor", "name": "Minor", "rank": 3, "tier": 2, "problem": "p", "mechanism": "m", "value": "v", "evidence": ["e"], "counterevidence": ["c"], "provenance": "conventional"},
            ],
        }
        candidate_value["freeze"] = {"recorded_at": "2026-09-01T00:00:00Z", "evidence_origin": "contemporaneous", "note": "fixture"}
        candidate_value["freeze"]["content_sha256"] = candidate_ledger.payload_hash(candidate_value)
        self.candidates.write_text(json.dumps(candidate_value), encoding="utf-8")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def command(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPT), *arguments], text=True, capture_output=True, check=False)

    def initialize(self) -> None:
        completed = self.command("init", "--output", str(self.ledger), "--run-record", str(self.record), "--scope", "Tier 3+ originality review")
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def add_comparator(self) -> None:
        completed = self.command(
            "add", "--ledger", str(self.ledger), "--id", "peer-project", "--name", "Peer project",
            "--candidate-id", "major-one", "--source-type", "peer-repository", "--source-title", "Peer source",
            "--source-url", "https://github.com/example/peer", "--accessed-at", "2026-09-01",
            "--identity-limit", "Default branch documentation; exact source revision was unavailable",
            "--problem", "same constraint", "--baseline", "conventional baseline", "--shared-mechanism", "shared mechanism",
            "--acknowledged-inspiration", "none found", "--repository-difference", "target adds a bounded adaptation",
            "--outcome-difference", "structurally enabled outcome; not independently measured", "--counterevidence", "peer establishes precedent",
            "--classification", "unusual-adaptation", "--originality-effect", "lowers", "--confidence", "medium",
            "--evidence", "peer source and target implementation were compared",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_freeze_requires_major_candidate_coverage_and_detects_mutation(self) -> None:
        self.initialize()
        self.add_comparator()
        missing = self.command("freeze", "--ledger", str(self.ledger), "--candidate-ledger", str(self.candidates), "--note", "fixture review")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("major-two", missing.stderr)
        excluded = self.command("exclude", "--ledger", str(self.ledger), "--candidate-id", "major-two", "--reason", "No originality claim was made; classified from direct upstream attribution")
        self.assertEqual(excluded.returncode, 0, excluded.stderr)
        frozen = self.command("freeze", "--ledger", str(self.ledger), "--candidate-ledger", str(self.candidates), "--note", "fixture review")
        self.assertEqual(frozen.returncode, 0, frozen.stderr)
        valid = self.command("validate", "--ledger", str(self.ledger), "--candidate-ledger", str(self.candidates), "--require-frozen")
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        rendered = self.command("render", "--ledger", str(self.ledger), "--candidate-ledger", str(self.candidates), "--require-frozen")
        self.assertIn("Peer project", rendered.stdout)
        value = json.loads(self.ledger.read_text(encoding="utf-8"))
        value["scope"] = "mutated"
        self.ledger.write_text(json.dumps(value), encoding="utf-8")
        invalid = self.command("validate", "--ledger", str(self.ledger), "--candidate-ledger", str(self.candidates), "--require-frozen")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("content hash", invalid.stdout)

    def test_rejects_unknown_candidate_and_credential_url(self) -> None:
        self.initialize()
        value = json.loads(self.ledger.read_text(encoding="utf-8"))
        value["entries"] = [{
            "id": "bad", "name": "Bad", "candidate_ids": ["unknown"],
            "source": {"type": "documentation", "title": "Bad", "url": "https://user:secret@example.com/docs", "accessed_at": "2026-09-01", "identity_limit": "moving"},
            "problem": "p", "baseline": "b", "shared_mechanism": "m", "acknowledged_inspiration": "none",
            "repository_difference": "d", "outcome_difference": "o", "counterevidence": "c",
            "classification": "conventional-engineering", "originality_effect": "lowers", "confidence": "low", "evidence": ["e"],
        }]
        self.ledger.write_text(json.dumps(value), encoding="utf-8")
        completed = self.command("validate", "--ledger", str(self.ledger), "--candidate-ledger", str(self.candidates))
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("unknown IDs", completed.stdout)
        self.assertIn("contains credentials", completed.stdout)


if __name__ == "__main__":
    unittest.main()
