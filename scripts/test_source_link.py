#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("source_link.py")


class SourceLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.checkout = Path(self.temporary.name) / "checkout"
        self.checkout.mkdir()
        subprocess.run(["git", "init", "-q", str(self.checkout)], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "remote", "add", "origin", "git@github.com:example/project.git"], check=True)
        (self.checkout / "space name.py").write_text("one\ntwo\nthree\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.checkout), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.checkout), "commit", "-qm", "fixture"], check=True)
        self.revision = subprocess.run(["git", "-C", str(self.checkout), "rev-parse", "HEAD"], check=True, text=True, capture_output=True).stdout.strip()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_script(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--checkout", str(self.checkout), "--path", "space name.py", "--lines", "1:2", *extra],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_generates_full_commit_encoded_link(self) -> None:
        completed = self.run_script("--format", "json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        value = json.loads(completed.stdout)
        self.assertEqual(value["revision"], self.revision)
        self.assertEqual(value["url"], f"https://github.com/example/project/blob/{self.revision}/space%20name.py#L1-L2")

    def test_rejects_dirty_head_and_out_of_bounds_lines(self) -> None:
        (self.checkout / "space name.py").write_text("changed\n", encoding="utf-8")
        dirty = self.run_script()
        self.assertNotEqual(dirty.returncode, 0)
        self.assertIn("dirty", dirty.stderr)
        bounds = self.run_script("--revision", self.revision, "--lines", "1:9")
        self.assertNotEqual(bounds.returncode, 0)
        self.assertIn("exceeds", bounds.stderr)

    def test_can_link_historical_revision_without_using_dirty_file(self) -> None:
        (self.checkout / "space name.py").write_text("changed\n", encoding="utf-8")
        completed = self.run_script("--revision", self.revision, "--format", "url")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn(self.revision, completed.stdout)


if __name__ == "__main__":
    unittest.main()
