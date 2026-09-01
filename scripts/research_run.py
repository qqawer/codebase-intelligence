#!/usr/bin/env python3
"""Create an auditable, machine-readable record for repository research runs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


SCHEMA_VERSION = 2
STATUSES = {"passed", "failed", "unavailable", "not-run", "blocked", "observed", "in-progress"}
VERDICTS = {
    "PASS",
    "PASS WITH EVIDENCE LIMITATIONS",
    "TARGETED PASS",
    "PARTIAL PASS",
    "FAIL",
}
SENSITIVE_OPTION = re.compile(r"(?i)^--?(?:api[-_]?key|token|password|passwd|secret|credential)(?:=|$)")
PHASES = [
    "initialized",
    "inventoried",
    "candidates-frozen",
    "runtime-validated",
    "comparators-reviewed",
    "synthesized",
    "report-validated",
    "finalized",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_record(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SystemExit(f"record does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid record JSON: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit("record root must be an object")
    return value


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def sanitize_url(value: str) -> str:
    if "://" not in value:
        return value
    parsed = urlsplit(value)
    host = parsed.netloc
    if "@" in host:
        host = parsed.hostname or ""
        if parsed.port:
            host = f"{host}:{parsed.port}"
    return urlunsplit((parsed.scheme, host, parsed.path, "", ""))


def redact_argv(argv: list[str]) -> list[str]:
    result: list[str] = []
    redact_next = False
    for item in argv:
        if redact_next:
            result.append("[REDACTED]")
            redact_next = False
            continue
        if SENSITIVE_OPTION.match(item):
            if "=" in item:
                result.append(item.split("=", 1)[0] + "=[REDACTED]")
            else:
                result.append(item)
                redact_next = True
            continue
        result.append(sanitize_url(item))
    return result


def relative_artifact(record_path: Path, artifact: Path) -> str:
    try:
        return artifact.resolve().relative_to(record_path.parent.resolve()).as_posix()
    except ValueError:
        return artifact.name


def command_log_paths(record_path: Path, index: int, argv: list[str], logs_dir: Path | None) -> tuple[Path, Path]:
    root = logs_dir or record_path.parent / "logs"
    root.mkdir(parents=True, exist_ok=True)
    command_name = re.sub(r"[^a-zA-Z0-9._-]+", "-", Path(argv[0]).name).strip("-") or "command"
    prefix = f"{index:03d}-{command_name}"
    return root / f"{prefix}.stdout.log", root / f"{prefix}.stderr.log"


def cmd_init(args: argparse.Namespace) -> int:
    if args.output.exists() and not args.force:
        raise SystemExit(f"record already exists: {args.output}")
    value: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": args.run_id,
        "run_class": args.run_class,
        "analysis_date": args.analysis_date,
        "created_at": utc_now(),
        "source_mode": args.source_mode,
        "target": {
            "repository": sanitize_url(args.target_repository),
            "revision": args.target_revision,
            "worktree_state": args.worktree_state,
        },
        "skill": {"revision": args.skill_ref},
        "recorder_environment": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
        },
        "entries": [],
        "artifacts": {},
        "phase": "initialized",
        "phase_history": [{"phase": "initialized", "recorded_at": utc_now(), "evidence_origin": "contemporaneous"}],
    }
    atomic_write(args.output, value)
    print(args.output)
    return 0


def cmd_exec(args: argparse.Namespace) -> int:
    record = read_record(args.record)
    argv = list(args.command)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        raise SystemExit("exec requires a command after --")
    index = len(record.setdefault("entries", [])) + 1
    stdout_path, stderr_path = command_log_paths(args.record, index, argv, args.logs_dir)
    started_at = utc_now()
    started = time.monotonic()
    status = "failed"
    exit_code: int | None = None
    timed_out = False
    try:
        completed = subprocess.run(
            argv,
            cwd=args.cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=args.timeout,
            check=False,
            env=os.environ.copy(),
        )
        stdout, stderr = completed.stdout, completed.stderr
        exit_code = completed.returncode
        status = "passed" if completed.returncode == 0 else "failed"
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b""
        stderr = error.stderr or b""
        status = "failed"
        timed_out = True
    except OSError as error:
        stdout = b""
        stderr = str(error).encode("utf-8", errors="replace")
        status = "unavailable"
    duration_ms = round((time.monotonic() - started) * 1000)
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    digest = hashlib.sha256(stdout + b"\0" + stderr).hexdigest()
    entry: dict[str, Any] = {
        "kind": "command",
        "category": args.category,
        "status": status,
        "argv": redact_argv(argv),
        "cwd": args.cwd_label,
        "started_at": started_at,
        "duration_ms": duration_ms,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stdout_log": relative_artifact(args.record, stdout_path),
        "stderr_log": relative_artifact(args.record, stderr_path),
        "output_sha256": digest,
    }
    if args.summary:
        entry["summary"] = args.summary
    record["entries"].append(entry)
    atomic_write(args.record, record)
    print(f"{status}: {' '.join(redact_argv(argv))}")
    return 0 if status == "passed" else (124 if timed_out else 1)


def cmd_note(args: argparse.Namespace) -> int:
    if args.status not in STATUSES:
        raise SystemExit(f"unsupported status: {args.status}")
    record = read_record(args.record)
    entry: dict[str, Any] = {
        "kind": "note",
        "category": args.category,
        "status": args.status,
        "reason": args.reason,
        "recorded_at": utc_now(),
        "evidence_origin": args.evidence_origin,
    }
    if args.summary:
        entry["summary"] = args.summary
    record.setdefault("entries", []).append(entry)
    atomic_write(args.record, record)
    return 0


def runtime_summary(entries: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {status: 0 for status in sorted(STATUSES)}
    for entry in entries:
        status = entry.get("status")
        if status in counts:
            counts[status] += 1
    return {"counts": counts, "end_to_end": any(entry.get("category") == "end-to-end" and entry.get("status") == "passed" for entry in entries)}


def parse_artifacts(values: list[str]) -> dict[str, Path]:
    artifacts: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"artifact must use key=path syntax: {value}")
        key, raw_path = value.split("=", 1)
        if not key or not raw_path:
            raise SystemExit(f"artifact must use key=path syntax: {value}")
        artifacts[key] = Path(raw_path)
    return artifacts


def gate_phase(record: dict[str, Any], record_path: Path, next_phase: str, supplied: dict[str, Path]) -> list[str]:
    errors: list[str] = []
    artifacts = record.get("artifacts", {})
    if next_phase == "inventoried" and "repository_snapshot" not in supplied and "repository_snapshot" not in artifacts:
        errors.append("inventoried requires repository_snapshot")
    elif next_phase == "candidates-frozen":
        path = supplied.get("candidate_ledger")
        if path is None:
            errors.append("candidates-frozen requires candidate_ledger")
        elif not path.is_file():
            errors.append(f"candidate ledger does not exist: {path}")
        else:
            try:
                from candidate_ledger import load as load_ledger, validate as validate_ledger
                ledger = load_ledger(path)
                errors.extend(f"candidate ledger: {error}" for error in validate_ledger(ledger, require_frozen=True))
                if ledger.get("target", {}).get("revision") != record.get("target", {}).get("revision"):
                    errors.append("candidate ledger target revision does not match run record")
            except (ImportError, SystemExit) as error:
                errors.append(f"candidate ledger could not be validated: {error}")
    elif next_phase == "runtime-validated":
        entries = record.get("entries", [])
        if not entries:
            errors.append("runtime-validated requires executed, unavailable, or intentionally skipped entries")
        if any(entry.get("status") == "in-progress" for entry in entries):
            errors.append("runtime-validated cannot contain in-progress entries")
    elif next_phase == "comparators-reviewed":
        reviewed = any(entry.get("category") == "comparator-review" for entry in record.get("entries", []))
        comparator_value = supplied.get("comparator_ledger")
        if comparator_value is None and artifacts.get("comparator_ledger"):
            comparator_value = record_path_for_artifact(record_path.parent, artifacts["comparator_ledger"])
        full_report = record.get("run_class") == "full-project-intelligence-report"
        if comparator_value is None:
            if full_report:
                errors.append("comparators-reviewed requires comparator_ledger for a full report")
            elif not reviewed:
                errors.append("comparators-reviewed requires a comparator-review entry or comparator_ledger")
        elif not comparator_value.is_file():
            errors.append(f"comparator ledger does not exist: {comparator_value}")
        else:
            candidate_value = artifacts.get("candidate_ledger")
            candidate_path = record_path_for_artifact(record_path.parent, candidate_value) if candidate_value else None
            try:
                from comparator_ledger import load as load_comparator_ledger, validate as validate_comparator_ledger
                from candidate_ledger import load as load_candidate_ledger
                candidate = load_candidate_ledger(candidate_path) if candidate_path and candidate_path.is_file() else None
                comparator = load_comparator_ledger(comparator_value)
                errors.extend(f"comparator ledger: {error}" for error in validate_comparator_ledger(comparator, candidate, require_frozen=True))
                if comparator.get("run_id") != record.get("run_id"):
                    errors.append("comparator ledger run_id does not match run record")
                comparator_target = comparator.get("target", {})
                record_target = record.get("target", {})
                if not isinstance(comparator_target, dict) or not isinstance(record_target, dict) or comparator_target.get("revision") != record_target.get("revision"):
                    errors.append("comparator ledger target revision does not match run record")
            except (ImportError, SystemExit) as error:
                errors.append(f"comparator ledger could not be validated: {error}")
    elif next_phase == "synthesized":
        path = supplied.get("report")
        if path is None or not path.is_file():
            errors.append("synthesized requires an existing report artifact")
    elif next_phase == "report-validated":
        path = supplied.get("validation_receipt")
        if path is None or not path.is_file():
            errors.append("report-validated requires an existing validation_receipt")
        else:
            try:
                receipt = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                errors.append(f"validation receipt is invalid: {error}")
            else:
                if receipt.get("errors") != 0:
                    errors.append("validation receipt contains errors")
                report_name = record.get("artifacts", {}).get("report")
                report_path = record_path_for_artifact(record_path.parent, report_name) if report_name else None
                if report_path and report_path.is_file():
                    actual_hash = hashlib.sha256(report_path.read_bytes()).hexdigest()
                    if receipt.get("report_sha256") != actual_hash:
                        errors.append("validation receipt does not match the current report")
    return errors


def record_path_for_artifact(root: Path, value: str | None) -> Path:
    return root / value if value else root


def cmd_advance(args: argparse.Namespace) -> int:
    record = read_record(args.record)
    current = record.get("phase")
    if current not in PHASES:
        raise SystemExit(f"record has unsupported phase: {current!r}")
    current_index = PHASES.index(current)
    if current_index + 1 >= len(PHASES) or PHASES[current_index + 1] != args.to:
        expected = PHASES[current_index + 1] if current_index + 1 < len(PHASES) else "none"
        raise SystemExit(f"phase transition must be sequential: {current} -> {expected}")
    supplied = parse_artifacts(args.artifact)
    errors = gate_phase(record, args.record, args.to, supplied)
    if errors and not args.retrospective:
        raise SystemExit("phase gate failed:\n- " + "\n- ".join(errors))
    if args.retrospective and not args.reason:
        raise SystemExit("retrospective transition requires --reason")
    for key, path in supplied.items():
        record.setdefault("artifacts", {})[key] = relative_artifact(args.record, path)
    history = {
        "phase": args.to,
        "recorded_at": utc_now(),
        "evidence_origin": "retrospective-migration" if args.retrospective else "contemporaneous",
    }
    if args.reason:
        history["reason"] = args.reason
    if errors:
        history["bypassed_gates"] = errors
    record["phase"] = args.to
    record.setdefault("phase_history", []).append(history)
    atomic_write(args.record, record)
    return 0


def cmd_finalize(args: argparse.Namespace) -> int:
    if args.verdict not in VERDICTS:
        raise SystemExit(f"unsupported verdict: {args.verdict}")
    record = read_record(args.record)
    if record.get("phase") != "report-validated":
        raise SystemExit("finalize requires phase report-validated")
    artifacts = record.setdefault("artifacts", {})
    artifacts["report"] = args.report
    if args.candidate_ledger:
        artifacts["candidate_ledger"] = args.candidate_ledger
    record["verdict"] = args.verdict
    record["completed_at"] = utc_now()
    record["runtime_summary"] = runtime_summary(record.get("entries", []))
    record["phase"] = "finalized"
    record.setdefault("phase_history", []).append({"phase": "finalized", "recorded_at": utc_now(), "evidence_origin": "contemporaneous"})
    atomic_write(args.record, record)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    init = subparsers.add_parser("init", help="create a run record")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--run-id", required=True)
    init.add_argument("--run-class", required=True)
    init.add_argument("--analysis-date", default=datetime.now(timezone.utc).date().isoformat())
    init.add_argument("--target-repository", required=True)
    init.add_argument("--target-revision", required=True)
    init.add_argument("--skill-ref", required=True)
    init.add_argument("--source-mode", required=True)
    init.add_argument("--worktree-state", default="unknown")
    init.add_argument("--force", action="store_true")
    init.set_defaults(handler=cmd_init)

    execute = subparsers.add_parser("exec", help="execute and record one command")
    execute.add_argument("--record", type=Path, required=True)
    execute.add_argument("--category", required=True)
    execute.add_argument("--cwd", type=Path, required=True)
    execute.add_argument("--cwd-label", default=".")
    execute.add_argument("--logs-dir", type=Path)
    execute.add_argument("--timeout", type=float)
    execute.add_argument("--summary")
    execute.add_argument("command", nargs=argparse.REMAINDER)
    execute.set_defaults(handler=cmd_exec)

    note = subparsers.add_parser("note", help="record evidence not produced by a local command")
    note.add_argument("--record", type=Path, required=True)
    note.add_argument("--category", required=True)
    note.add_argument("--status", required=True)
    note.add_argument("--reason", required=True)
    note.add_argument("--summary")
    note.add_argument("--evidence-origin", default="contemporaneous")
    note.set_defaults(handler=cmd_note)

    advance = subparsers.add_parser("advance", help="advance one gated research phase")
    advance.add_argument("--record", type=Path, required=True)
    advance.add_argument("--to", choices=PHASES[1:-1], required=True)
    advance.add_argument("--artifact", action="append", default=[])
    advance.add_argument("--retrospective", action="store_true")
    advance.add_argument("--reason")
    advance.set_defaults(handler=cmd_advance)

    finalize = subparsers.add_parser("finalize", help="attach artifacts and finalize the record")
    finalize.add_argument("--record", type=Path, required=True)
    finalize.add_argument("--report", required=True)
    finalize.add_argument("--candidate-ledger")
    finalize.add_argument("--verdict", required=True)
    finalize.set_defaults(handler=cmd_finalize)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
