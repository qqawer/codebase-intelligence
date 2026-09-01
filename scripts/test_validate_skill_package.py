#!/usr/bin/env python3

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from validate_skill_package import validate


class ValidateSkillPackageTests(unittest.TestCase):
    def test_accepts_matching_package_and_existing_local_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "example-skill"
            root.mkdir()
            (root / "reference.md").write_text("# Reference\n", encoding="utf-8")
            (root / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: Example capability.\n---\n\n[Reference](reference.md)\n",
                encoding="utf-8",
            )
            self.assertEqual(validate(root), [])

    def test_rejects_name_mismatch_and_broken_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "wrong-folder"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: Example capability.\n---\n\n[Missing](missing.md)\n",
                encoding="utf-8",
            )
            errors = validate(root)
            self.assertTrue(any("does not match" in error for error in errors))
            self.assertTrue(any("broken local link" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
