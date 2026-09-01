#!/usr/bin/env python3
"""Focused regression tests for repository_snapshot.py."""

from pathlib import Path, PurePosixPath
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repository_snapshot


class BoundaryDirectoryTests(unittest.TestCase):
    def test_generated_build_directory_is_a_boundary(self) -> None:
        path = PurePosixPath("crates/example/build/generated.rs")
        self.assertEqual(repository_snapshot.boundary_directory(path), "crates/example/build")

    def test_build_test_fixture_is_not_a_boundary(self) -> None:
        path = PurePosixPath("crates/uv/tests/build/basic.rs")
        self.assertIsNone(repository_snapshot.boundary_directory(path))

    def test_vendored_code_inside_tests_remains_a_boundary(self) -> None:
        path = PurePosixPath("tests/fixtures/vendor/dependency.py")
        self.assertEqual(
            repository_snapshot.boundary_directory(path),
            "tests/fixtures/vendor",
        )


if __name__ == "__main__":
    unittest.main()
