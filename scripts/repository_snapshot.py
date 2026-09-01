#!/usr/bin/env python3
"""Produce a bounded, read-only repository discovery snapshot."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = 1
DEFAULT_MAX_ITEMS = 20
GIT_TIMEOUT_SECONDS = 15
MAX_CONTENT_SCAN_FILES = 5_000
MAX_CONTENT_SCAN_BYTES = 2 * 1024 * 1024

IGNORED_WALK_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "target",
    "dist",
    "build",
    ".next",
    ".nuxt",
    ".venv",
    "venv",
}

BOUNDARY_DIR_NAMES = {
    "vendor",
    "vendors",
    "third_party",
    "third-party",
    "external",
    "generated",
    "gen",
    "dist",
    "build",
    "target",
    "node_modules",
}

# These names often denote generated output, but are also commonly used for executable
# test fixtures (for example, `tests/build`). In a recognized test tree, keep them visible
# for discovery instead of classifying the fixture as an exclusion boundary.
GENERATED_OUTPUT_DIR_NAMES = {"build", "dist", "target"}

TEST_DIR_NAMES = {"test", "tests", "testing", "__tests__", "spec", "specs"}
BENCHMARK_DIR_NAMES = {"bench", "benches", "benchmark", "benchmarks"}
DOC_DIR_NAMES = {"doc", "docs", "documentation", "adr", "adrs"}

NON_EXECUTION_ARTIFACT_EXTENSIONS = {
    ".adoc",
    ".gif",
    ".jpeg",
    ".jpg",
    ".md",
    ".pdf",
    ".png",
    ".rst",
    ".svg",
    ".txt",
    ".webp",
}

MANIFEST_NAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
    "deno.json",
    "deno.jsonc",
    "pyproject.toml",
    "poetry.lock",
    "uv.lock",
    "requirements.txt",
    "pipfile",
    "pipfile.lock",
    "setup.py",
    "setup.cfg",
    "go.mod",
    "go.sum",
    "cargo.toml",
    "cargo.lock",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "settings.gradle",
    "settings.gradle.kts",
    "gemfile",
    "gemfile.lock",
    "composer.json",
    "composer.lock",
    "mix.exs",
    "mix.lock",
    "pubspec.yaml",
    "pubspec.lock",
    "package.swift",
    "project.clj",
    "deps.edn",
    "flake.nix",
}

ENTRYPOINT_NAMES = {
    "main.py",
    "app.py",
    "server.py",
    "manage.py",
    "main.go",
    "main.rs",
    "main.c",
    "main.cc",
    "main.cpp",
    "main.java",
    "application.java",
    "program.cs",
    "index.js",
    "index.ts",
    "server.js",
    "server.ts",
    "app.js",
    "app.ts",
    "cli.py",
}

LANGUAGE_BY_EXTENSION = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cxx": "C++",
    ".h": "C/C++ headers",
    ".hh": "C++ headers",
    ".hpp": "C++ headers",
    ".cs": "C#",
    ".css": "CSS",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".fs": "F#",
    ".fsx": "F#",
    ".go": "Go",
    ".hs": "Haskell",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".lua": "Lua",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".php": "PHP",
    ".pl": "Perl",
    ".pm": "Perl",
    ".py": "Python",
    ".r": "R",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
    ".zig": "Zig",
}

BENCHMARK_SOURCE_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".py",
    ".rs",
    ".ts",
    ".tsx",
}

BENCHMARK_SYMBOL_PATTERNS = (
    re.compile(r"(?m)^\s*func\s+Benchmark[A-Za-z0-9_]+\s*\("),
    re.compile(r"(?m)^\s*def\s+(?:benchmark_|test_[A-Za-z0-9_]*benchmark)[A-Za-z0-9_]*\s*\("),
    re.compile(r"#\[bench\]|criterion_group!\s*\("),
    re.compile(r"@Benchmark\b|\[Benchmark\]"),
    re.compile(r"\b(?:BENCHMARK|bench|benchmark)\s*\("),
)


def run_git(directory: Path, *args: str) -> tuple[bool, str]:
    """Run a read-only Git query with stable decoding and a timeout."""
    try:
        result = subprocess.run(
            ["git", "-C", str(directory), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=GIT_TIMEOUT_SECONDS,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""
    output = result.stdout.decode("utf-8", errors="surrogateescape").rstrip("\r\n")
    return result.returncode == 0, output


def sanitize_remote(value: str) -> str | None:
    """Remove credentials, query strings, and fragments from a remote URL."""
    value = value.strip()
    if not value:
        return None
    if "://" not in value:
        if "@" in value and ":" in value.split("@", 1)[1]:
            return value.split("@", 1)[1]
        return value
    parsed = urlsplit(value)
    hostname = parsed.hostname or ""
    if parsed.port:
        hostname = f"{hostname}:{parsed.port}"
    return urlunsplit((parsed.scheme, hostname, parsed.path, "", ""))


def git_file_list(root: Path) -> tuple[list[str], int]:
    ok, output = run_git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    if not ok:
        return [], 0
    paths = sorted({item for item in output.split("\0") if item})
    tracked_ok, tracked = run_git(root, "ls-files", "-z", "--cached")
    tracked_count = len([item for item in tracked.split("\0") if item]) if tracked_ok else 0
    return paths, tracked_count


def filesystem_file_list(root: Path) -> list[str]:
    paths: list[str] = []
    for current, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name for name in directories if name not in IGNORED_WALK_DIRS
        )
        current_path = Path(current)
        for filename in sorted(filenames):
            full_path = current_path / filename
            try:
                relative = full_path.relative_to(root).as_posix()
            except ValueError:
                continue
            paths.append(relative)
    return paths


def is_manifest(path: PurePosixPath) -> bool:
    name = path.name.lower()
    return (
        name in MANIFEST_NAMES
        or name.endswith((".csproj", ".fsproj", ".vbproj", ".sln"))
    )


def is_test(path: PurePosixPath) -> bool:
    parts = {part.lower() for part in path.parts[:-1]}
    name = path.name.lower()
    explicit_name = name.startswith("test_") or name.endswith(
        (
            "_test.go",
            "_test.py",
            ".test.js",
            ".test.ts",
            ".test.tsx",
            ".spec.js",
            ".spec.ts",
            ".spec.tsx",
        )
    )
    if explicit_name:
        return True
    return (
        bool(parts & TEST_DIR_NAMES)
        and path.suffix.lower() not in NON_EXECUTION_ARTIFACT_EXTENSIONS
    )


def is_benchmark(path: PurePosixPath) -> bool:
    parts = {part.lower() for part in path.parts[:-1]}
    name = path.name.lower()
    if path.suffix.lower() in NON_EXECUTION_ARTIFACT_EXTENSIONS:
        return False
    return bool(parts & BENCHMARK_DIR_NAMES) or "benchmark" in name or name.endswith(
        ("_bench.go", "_bench.py", ".bench.js", ".bench.ts")
    )


def is_documentation(path: PurePosixPath) -> bool:
    parts = {part.lower() for part in path.parts[:-1]}
    name = path.name.lower()
    return bool(parts & DOC_DIR_NAMES) or name.startswith(
        ("readme", "contributing", "architecture", "changelog", "adr-")
    )


def is_ci(path: PurePosixPath) -> bool:
    text = path.as_posix().lower()
    name = path.name.lower()
    return (
        text.startswith(".github/workflows/")
        or text.startswith(".circleci/")
        or name in {".gitlab-ci.yml", "jenkinsfile", "azure-pipelines.yml", "buildkite.yml"}
    )


def is_entrypoint(path: PurePosixPath) -> bool:
    name = path.name.lower()
    parts = [part.lower() for part in path.parts]
    if name in ENTRYPOINT_NAMES:
        return True
    return len(parts) >= 3 and parts[0] == "cmd" and name == "main.go"


def boundary_directory(path: PurePosixPath) -> str | None:
    for index, part in enumerate(path.parts[:-1]):
        lowered = part.lower()
        if lowered not in BOUNDARY_DIR_NAMES:
            continue
        ancestors = {ancestor.lower() for ancestor in path.parts[:index]}
        if lowered in GENERATED_OUTPUT_DIR_NAMES and ancestors & TEST_DIR_NAMES:
            continue
        if lowered in BOUNDARY_DIR_NAMES:
            return PurePosixPath(*path.parts[: index + 1]).as_posix()
    return None


def benchmark_symbol_paths(root: Path, files: Iterable[str]) -> tuple[list[str], int]:
    """Find common benchmark declarations with strict file-count and size limits."""
    eligible = []
    scanner_path = Path(__file__).resolve()
    for raw_path in files:
        path = PurePosixPath(raw_path)
        full_path = (root / raw_path).resolve()
        if full_path == scanner_path:
            continue
        if path.suffix.lower() in BENCHMARK_SOURCE_EXTENSIONS and not boundary_directory(path):
            eligible.append(raw_path)

    omitted = max(0, len(eligible) - MAX_CONTENT_SCAN_FILES)
    matches = []
    for raw_path in eligible[:MAX_CONTENT_SCAN_FILES]:
        full_path = root / raw_path
        try:
            if not full_path.is_file() or full_path.stat().st_size > MAX_CONTENT_SCAN_BYTES:
                continue
            content = full_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(pattern.search(content) for pattern in BENCHMARK_SYMBOL_PATTERNS):
            matches.append(raw_path)
    return matches, omitted


def bounded(items: Iterable[str], maximum: int) -> dict[str, Any]:
    unique = sorted(set(items))
    return {
        "items": unique[:maximum],
        "omitted": max(0, len(unique) - maximum),
        "total": len(unique),
    }


def bounded_counts(counter: Counter[str], maximum: int) -> dict[str, Any]:
    ordered = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return {
        "items": [{"name": name, "count": count} for name, count in ordered[:maximum]],
        "omitted": max(0, len(ordered) - maximum),
        "total": len(ordered),
    }


def worktree_summary(root: Path) -> tuple[bool | None, int | None, int | None]:
    ok, output = run_git(root, "status", "--porcelain=v2", "-z", "--untracked-files=normal")
    if not ok:
        return None, None, None
    records = [record for record in output.split("\0") if record]
    changes = [record for record in records if record.startswith(("1 ", "2 ", "u ", "? "))]
    untracked = [record for record in records if record.startswith("? ")]
    return bool(changes), len(changes), len(untracked)


def submodule_summary(root: Path, maximum: int) -> dict[str, Any]:
    ok, output = run_git(root, "submodule", "status", "--recursive")
    if not ok or not output:
        return {"items": [], "omitted": 0, "total": 0}
    entries = []
    state_names = {"-": "uninitialized", "+": "revision-mismatch", "U": "conflict", " ": "clean"}
    for line in output.splitlines():
        marker = line[0] if line else " "
        fields = line[1:].strip().split()
        entries.append({
            "path": fields[1] if len(fields) > 1 else (fields[0] if fields else "unknown"),
            "state": state_names.get(marker, "unknown"),
        })
    return {
        "items": entries[:maximum],
        "omitted": max(0, len(entries) - maximum),
        "total": len(entries),
    }


def lfs_patterns(root: Path, maximum: int) -> dict[str, Any]:
    attributes = root / ".gitattributes"
    if not attributes.is_file():
        return {"items": [], "omitted": 0, "total": 0}
    try:
        lines = attributes.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return {"items": [], "omitted": 0, "total": 0}
    patterns = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "filter=lfs" in stripped:
            patterns.append(stripped.split()[0])
    return bounded(patterns, maximum)


def collect_snapshot(target: Path, maximum: int) -> dict[str, Any]:
    requested = target.resolve()
    git_ok, git_root_text = run_git(requested, "rev-parse", "--show-toplevel")
    root = Path(git_root_text).resolve() if git_ok else requested

    if git_ok:
        files, tracked_count = git_file_list(root)
    else:
        files = filesystem_file_list(root)
        tracked_count = 0

    manifests: list[str] = []
    tests: list[str] = []
    benchmarks: list[str] = []
    docs: list[str] = []
    ci: list[str] = []
    entrypoints: list[str] = []
    boundaries: set[str] = set()
    languages: Counter[str] = Counter()
    extensions: Counter[str] = Counter()

    for raw_path in files:
        path = PurePosixPath(raw_path)
        if is_manifest(path):
            manifests.append(raw_path)
        if is_test(path):
            tests.append(raw_path)
        if is_benchmark(path):
            benchmarks.append(raw_path)
        if is_documentation(path):
            docs.append(raw_path)
        if is_ci(path):
            ci.append(raw_path)
        if is_entrypoint(path):
            entrypoints.append(raw_path)
        boundary = boundary_directory(path)
        if boundary:
            boundaries.add(boundary)
        suffix = path.suffix.lower()
        extensions[suffix or "[no extension]"] += 1
        language = LANGUAGE_BY_EXTENSION.get(suffix)
        if language:
            languages[language] += 1

    benchmark_symbols, omitted_content_scan = benchmark_symbol_paths(root, files)
    benchmarks.extend(benchmark_symbols)

    warnings: list[str] = []
    repository: dict[str, Any] = {
        "is_git": git_ok,
        "root": str(root),
        "requested_path": str(requested),
        "tracked_files": tracked_count if git_ok else None,
        "discovered_files": len(files),
    }

    if git_ok:
        _, revision = run_git(root, "rev-parse", "HEAD")
        branch_ok, branch = run_git(root, "symbolic-ref", "--short", "-q", "HEAD")
        shallow_ok, shallow_text = run_git(root, "rev-parse", "--is-shallow-repository")
        remote_ok, remote = run_git(root, "config", "--get", "remote.origin.url")
        dirty, change_count, untracked_count = worktree_summary(root)
        repository.update(
            {
                "revision": revision or None,
                "branch": branch if branch_ok and branch else "DETACHED",
                "dirty": dirty,
                "worktree_changes": change_count,
                "untracked_files": untracked_count,
                "shallow": shallow_text == "true" if shallow_ok else None,
                "origin": sanitize_remote(remote) if remote_ok else None,
                "submodules": submodule_summary(root, maximum),
                "lfs_patterns": lfs_patterns(root, maximum),
            }
        )
        if dirty:
            warnings.append(
                "Worktree has tracked or untracked changes; record them before comparing runs."
            )
        if repository["shallow"]:
            warnings.append(
                "Repository history is shallow; history-based discovery has an evidence ceiling."
            )
        if any(item["state"] != "clean" for item in repository["submodules"]["items"]):
            warnings.append(
                "One or more submodules are unavailable, conflicted, or not at the "
                "recorded revision."
            )
        if repository["lfs_patterns"]["total"]:
            warnings.append(
                "Git LFS patterns are present; verify required objects are materialized."
            )
    else:
        repository.update(
            {
                "revision": None,
                "branch": None,
                "dirty": None,
                "worktree_changes": None,
                "untracked_files": None,
                "shallow": None,
                "origin": None,
                "submodules": {"items": [], "omitted": 0, "total": 0},
                "lfs_patterns": lfs_patterns(root, maximum),
            }
        )
        warnings.append(
            "Target is not inside a Git worktree; revision and reproducibility are unknown."
        )

    if boundaries:
        warnings.append(
            "Generated, vendored, dependency, or build boundaries were detected "
            "heuristically; verify exclusions."
        )
    if not tests:
        warnings.append("No test paths matched the language-agnostic discovery rules.")
    if not benchmarks:
        warnings.append(
            "No benchmark paths or common benchmark declarations matched the discovery rules."
        )
    if omitted_content_scan:
        warnings.append(
            f"Benchmark symbol scanning skipped {omitted_content_scan} eligible source "
            "files after the "
            f"{MAX_CONTENT_SCAN_FILES}-file safety limit."
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repository": repository,
        "inventory": {
            "languages": bounded_counts(languages, maximum),
            "extensions": bounded_counts(extensions, maximum),
            "manifests": bounded(manifests, maximum),
            "entrypoint_candidates": bounded(entrypoints, maximum),
            "tests": bounded(tests, maximum),
            "benchmarks": bounded(benchmarks, maximum),
            "documentation": bounded(docs, maximum),
            "ci": bounded(ci, maximum),
            "source_boundaries": bounded(boundaries, maximum),
        },
        "warnings": warnings,
        "interpretation_note": (
            "Path classifications are discovery hints, not architecture, runtime, ownership, "
            "or quality conclusions."
        ),
    }


def markdown_code(value: Any) -> str:
    text = "unknown" if value is None else str(value)
    return f"`{text.replace('`', 'ˋ')}`"


def render_count_table(title: str, data: dict[str, Any]) -> list[str]:
    lines = [f"### {title}", "", "| Name | Files |", "|---|---:|"]
    if not data["items"]:
        lines.append("| None detected | 0 |")
    else:
        for item in data["items"]:
            lines.append(f"| {markdown_code(item['name'])} | {item['count']} |")
    if data["omitted"]:
        lines.append(f"| … {data['omitted']} more categories omitted | — |")
    lines.append("")
    return lines


def render_path_group(label: str, data: dict[str, Any]) -> str:
    if not data["items"]:
        return f"- **{label} (0):** none detected"
    values = ", ".join(markdown_code(item) for item in data["items"])
    suffix = f"; {data['omitted']} omitted" if data["omitted"] else ""
    return f"- **{label} ({data['total']}):** {values}{suffix}"


def render_markdown(snapshot: dict[str, Any]) -> str:
    repository = snapshot["repository"]
    inventory = snapshot["inventory"]
    lines = [
        "# Repository Snapshot",
        "",
        f"Generated: {markdown_code(snapshot['generated_at'])}",
        "",
        "## Repository identity",
        "",
        f"- **Root:** {markdown_code(repository['root'])}",
        f"- **Git worktree:** {'yes' if repository['is_git'] else 'no'}",
        f"- **Origin:** {markdown_code(repository['origin'])}",
        f"- **Revision:** {markdown_code(repository['revision'])}",
        f"- **Branch:** {markdown_code(repository['branch'])}",
        f"- **Dirty:** {markdown_code(repository['dirty'])}",
        f"- **Shallow:** {markdown_code(repository['shallow'])}",
        f"- **Tracked files:** {markdown_code(repository['tracked_files'])}",
        f"- **Discovered files:** {repository['discovered_files']}",
        f"- **Worktree changes:** {markdown_code(repository['worktree_changes'])}",
        f"- **Untracked files:** {markdown_code(repository['untracked_files'])}",
        "",
        "## Inventory",
        "",
    ]
    lines.extend(render_count_table("Languages", inventory["languages"]))
    lines.extend(render_count_table("File extensions", inventory["extensions"]))
    lines.extend(
        [
            "## Discovery clusters",
            "",
            render_path_group("Manifests and locks", inventory["manifests"]),
            render_path_group("Entrypoint candidates", inventory["entrypoint_candidates"]),
            render_path_group("Tests", inventory["tests"]),
            render_path_group("Benchmarks", inventory["benchmarks"]),
            render_path_group("Documentation", inventory["documentation"]),
            render_path_group("CI", inventory["ci"]),
            render_path_group("Source boundaries", inventory["source_boundaries"]),
            "",
            "## Submodules and LFS",
            "",
        ]
    )
    submodules = repository["submodules"]
    if submodules["items"]:
        for item in submodules["items"]:
            lines.append(f"- **Submodule:** {markdown_code(item['path'])} — {item['state']}")
        if submodules["omitted"]:
            lines.append(f"- {submodules['omitted']} additional submodules omitted")
    else:
        lines.append("- **Submodules:** none detected")
    lines.append(render_path_group("Git LFS patterns", repository["lfs_patterns"]))
    lines.extend(["", "## Warnings and follow-ups", ""])
    if snapshot["warnings"]:
        lines.extend(f"- {warning}" for warning in snapshot["warnings"])
    else:
        lines.append("- None from the bounded discovery pass.")
    lines.extend(["", f"_{snapshot['interpretation_note']}_", ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Produce a bounded, read-only repository discovery snapshot.",
    )
    parser.add_argument(
        "repository",
        nargs="?",
        default=".",
        help="Repository or directory to inspect",
    )
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument(
        "--max-items",
        type=int,
        default=DEFAULT_MAX_ITEMS,
        help=f"Maximum entries per output category (default: {DEFAULT_MAX_ITEMS})",
    )
    args = parser.parse_args()
    if not 1 <= args.max_items <= 200:
        parser.error("--max-items must be between 1 and 200")
    target = Path(args.repository).expanduser()
    if not target.is_dir():
        parser.error(f"repository is not a readable directory: {target}")
    args.repository = target
    return args


def main() -> int:
    args = parse_args()
    snapshot = collect_snapshot(args.repository, args.max_items)
    try:
        if args.format == "json":
            print(json.dumps(snapshot, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            print(render_markdown(snapshot), end="")
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
