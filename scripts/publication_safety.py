#!/usr/bin/env python3
"""Redact machine-local paths from report artifacts and preserve evidence hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


PUBLISHABLE_SUFFIXES = {".json", ".log", ".md", ".sh", ".txt"}
GENERIC_ROOTS = (
    (re.compile(r"/Users/[^/\s\"'<>]+"), "[USER_HOME]"),
    (re.compile(r"/home/[^/\s\"'<>]+"), "[USER_HOME]"),
    (re.compile(r"/private/tmp/[^/\s\"'<>]+"), "[TEMP_DIR]"),
    (re.compile(r"/var/folders/[^\s\"'<>]+"), "[TEMP_DIR]"),
    (re.compile(r"/opt/homebrew/Cellar/[^/\s\"'<>]+/[^/\s\"'<>]+"), "[TOOLCHAIN_ROOT]"),
    (re.compile(r"[A-Za-z]:\\Users\\[^\\\s\"'<>]+"), "[USER_HOME]"),
)
RESIDUAL_MACHINE_PATH = re.compile(
    r"(?:/Users/|/home/|/private/tmp/|/var/folders/|/opt/homebrew/Cellar/|[A-Za-z]:\\Users\\)"
)


def atomic_json_write(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.publication-safety.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def replacements(target_checkout: Path | None) -> list[tuple[str, str]]:
    values: list[tuple[str, str]] = []
    if target_checkout:
        values.extend([
            (str(target_checkout), "[TARGET_CHECKOUT]"),
            (str(target_checkout.resolve()), "[TARGET_CHECKOUT]"),
        ])
    home = Path.home()
    if str(home) not in {"", "/"}:
        values.append((str(home), "[USER_HOME]"))
    return sorted(set(values), key=lambda item: len(item[0]), reverse=True)


def redact_text(value: str, exact: list[tuple[str, str]]) -> str:
    for source, replacement in exact:
        value = value.replace(source, replacement)
    for pattern, replacement in GENERIC_ROOTS:
        value = pattern.sub(replacement, value)
    return value


def artifact_files(session: Path) -> list[Path]:
    return sorted(
        path for path in session.rglob("*")
        if path.is_file() and path.name != "run-record.json" and path.suffix.lower() in PUBLISHABLE_SUFFIXES
    )


def sanitize(session: Path, target_checkout: Path | None = None) -> dict[str, Any]:
    session = session.resolve()
    record_path = session / "run-record.json"
    if not record_path.is_file():
        raise SystemExit(f"run record does not exist: {record_path}")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    pending: dict[Path, str] = {}
    changed_files: list[str] = []
    residuals: list[str] = []
    exact = replacements(target_checkout)
    for path in artifact_files(session):
        original = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(session).as_posix()
        # The report is authored analysis. Do not silently rewrite its semantics or
        # turn an absolute local link into a bogus placeholder link; require the
        # author to fix it. Supporting machine-generated artifacts are safe to redact.
        redacted = original if path.name == "PROJECT_INTELLIGENCE_REPORT.md" else redact_text(original, exact)
        if RESIDUAL_MACHINE_PATH.search(redacted):
            residuals.append(relative)
        pending[path] = redacted
        if redacted != original:
            changed_files.append(relative)
    if residuals:
        raise SystemExit("machine-specific paths remain after redaction: " + ", ".join(residuals))

    for path, content in pending.items():
        path.write_text(content, encoding="utf-8")

    changed_outputs = 0
    for entry in record.get("entries", []):
        if entry.get("kind") != "command":
            continue
        stdout = (session / entry["stdout_log"]).read_bytes()
        stderr = (session / entry["stderr_log"]).read_bytes()
        digest = hashlib.sha256(stdout + b"\0" + stderr).hexdigest()
        previous = entry.get("output_sha256")
        if digest != previous:
            entry.setdefault("raw_output_sha256", previous)
            entry["output_sha256"] = digest
            entry["output_redacted"] = True
            changed_outputs += 1
    record["publication_redaction"] = {
        "status": "applied",
        "changed_files": changed_files,
        "changed_command_outputs": changed_outputs,
        "preserves_raw_output_hash": True,
    }
    atomic_json_write(record_path, record)
    return {
        "session": str(session),
        "files_scanned": len(pending),
        "files_changed": len(changed_files),
        "command_outputs_redacted": changed_outputs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("session", type=Path)
    parser.add_argument("--target-checkout", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    result = sanitize(args.session, args.target_checkout)
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f"Publication artifacts: {result['files_scanned']} scanned, "
            f"{result['files_changed']} changed, "
            f"{result['command_outputs_redacted']} command outputs rehashed"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
