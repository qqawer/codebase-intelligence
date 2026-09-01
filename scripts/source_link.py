#!/usr/bin/env python3
"""Generate an immutable GitHub source link from a local Git checkout."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import quote


GITHUB_REMOTE = re.compile(
    r"^(?:https?://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+)/([^/]+?)(?:\.git)?/?$",
    re.IGNORECASE,
)


def git(checkout: Path, *args: str, text: bool = True) -> str | bytes:
    result = subprocess.run(
        ["git", "-C", str(checkout), *args],
        capture_output=True,
        text=text,
        check=False,
        timeout=20,
    )
    if result.returncode != 0:
        error = result.stderr.strip() if text else result.stderr.decode(errors="replace").strip()
        raise SystemExit(error or f"git {' '.join(args)} failed")
    return result.stdout.strip() if text else result.stdout


def github_repository(remote: str) -> tuple[str, str]:
    match = GITHUB_REMOTE.fullmatch(remote.strip())
    if not match:
        raise SystemExit(f"remote is not a supported GitHub repository URL: {remote}")
    return match.group(1), match.group(2)


def normalize_path(raw_path: str) -> str:
    candidate = PurePosixPath(raw_path.replace("\\", "/"))
    if candidate.is_absolute() or not candidate.parts or ".." in candidate.parts:
        raise SystemExit("--path must be a repository-relative path without '..'")
    value = candidate.as_posix()
    if value in {"", "."}:
        raise SystemExit("--path must identify a file")
    return value


def parse_lines(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d+)(?::(\d+))?", value)
    if not match:
        raise SystemExit("--lines must use START or START:END")
    start = int(match.group(1))
    end = int(match.group(2) or start)
    if start < 1 or end < start:
        raise SystemExit("line numbers must be positive and END must not precede START")
    return start, end


def revision_content(checkout: Path, revision: str, path: str) -> bytes:
    return git(checkout, "show", f"{revision}:{path}", text=False)  # type: ignore[return-value]


def build_link(
    checkout: Path,
    path: str,
    lines: tuple[int, int],
    remote_name: str,
    revision: str,
    require_clean_head: bool,
) -> dict[str, object]:
    root = Path(str(git(checkout, "rev-parse", "--show-toplevel"))).resolve()
    commit = str(git(root, "rev-parse", f"{revision}^{{commit}}"))
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit(f"revision did not resolve to a full commit: {commit}")
    remote = str(git(root, "remote", "get-url", remote_name))
    owner, repository = github_repository(remote)
    normalized = normalize_path(path)
    content = revision_content(root, commit, normalized)
    line_count = len(content.splitlines())
    start, end = lines
    if end > line_count:
        raise SystemExit(f"line {end} exceeds {normalized} ({line_count} lines at {commit})")

    head = str(git(root, "rev-parse", "HEAD"))
    if require_clean_head and commit == head:
        status = str(git(root, "status", "--porcelain", "--", normalized))
        if status:
            raise SystemExit(f"refusing to link dirty worktree content: {normalized}")

    encoded_path = "/".join(quote(part, safe="") for part in PurePosixPath(normalized).parts)
    fragment = f"#L{start}" if start == end else f"#L{start}-L{end}"
    repository_url = f"https://github.com/{owner}/{repository}"
    url = f"{repository_url}/blob/{commit}/{encoded_path}{fragment}"
    return {
        "repository_url": repository_url,
        "revision": commit,
        "path": normalized,
        "line_start": start,
        "line_end": end,
        "url": url,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--path", required=True)
    parser.add_argument("--lines", required=True)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--label")
    parser.add_argument("--format", choices=("markdown", "url", "json"), default="markdown")
    args = parser.parse_args()

    result = build_link(args.checkout, args.path, parse_lines(args.lines), args.remote, args.revision, args.revision == "HEAD")
    label = args.label or f"{result['path']}#L{result['line_start']}-L{result['line_end']}"
    result["markdown"] = f"[{label}]({result['url']})"
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(result[args.format])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
