#!/usr/bin/env python3
"""Orchestrate initialization, status, and publication of a repository research session."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import research_run


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
PHASE_ACTIONS = {
    "initialized": "preserve repository_snapshot and advance to inventoried",
    "inventoried": "complete and freeze candidate-ledger.json, then advance to candidates-frozen",
    "candidates-frozen": "record executed, unavailable, or intentionally skipped runtime checks, then advance to runtime-validated",
    "runtime-validated": "record comparator-review evidence, then advance to comparators-reviewed",
    "comparators-reviewed": "write PROJECT_INTELLIGENCE_REPORT.md and advance to synthesized",
    "synthesized": "run research_session.py publish for strict validation, finalization, and index refresh",
    "report-validated": "finalize the run record and refresh the research index",
    "finalized": "run build_research_index.py without --write to check publication drift",
}


def run(command: list[str], *, cwd: Path | None = None, stdout_path: Path | None = None) -> str:
    stdout: int | Any = subprocess.PIPE
    handle = None
    if stdout_path is not None:
        handle = stdout_path.open("wb")
        stdout = handle
    try:
        completed = subprocess.run(command, cwd=cwd, stdout=stdout, stderr=subprocess.PIPE, check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise SystemExit(f"command could not run: {' '.join(command)}: {error}") from error
    finally:
        if handle:
            handle.close()
    if completed.returncode != 0:
        stderr = completed.stderr.decode(errors="replace").strip()
        raise SystemExit(stderr or f"command failed ({completed.returncode}): {' '.join(command)}")
    return completed.stdout.decode(errors="replace").strip() if stdout_path is None else ""


def git(checkout: Path, *args: str) -> str:
    return run(["git", "-C", str(checkout), *args])


def normalize_repository_url(value: str) -> str:
    value = value.strip()
    scp = re.fullmatch(r"git@([^:]+):(.+)", value)
    ssh = re.fullmatch(r"ssh://git@([^/]+)/(.+)", value)
    if scp or ssh:
        match = scp or ssh
        return f"https://{match.group(1)}/{match.group(2)}"
    if "://" in value:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        if parsed.port:
            host += f":{parsed.port}"
        return urlunsplit((parsed.scheme, host, parsed.path, "", ""))
    return value


def repository_slug(repository: str) -> str:
    path = urlsplit(repository).path if "://" in repository else repository
    parts = [part for part in path.strip("/").removesuffix(".git").split("/") if part]
    if len(parts) < 2:
        raise SystemExit(f"cannot derive owner/repository from remote: {repository}")
    owner, name = parts[-2:]
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", f"{owner}-{name}").strip("-")
    if not slug:
        raise SystemExit(f"cannot derive report directory from remote: {repository}")
    return slug


def package_content_hash(root: Path) -> str:
    digest = hashlib.sha256()
    ignored = {".git", "__pycache__", ".DS_Store"}
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not ignored.intersection(item.parts)):
        relative = path.relative_to(root).as_posix().encode()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        content = path.read_bytes()
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return "content-sha256:" + digest.hexdigest()


def skill_identity(root: Path) -> str:
    try:
        revision = git(root, "rev-parse", "HEAD")
        status = git(root, "status", "--porcelain")
    except SystemExit:
        return package_content_hash(root)
    return revision if re.fullmatch(r"[0-9a-f]{40}", revision) and not status else package_content_hash(root)


def load_record(path: Path) -> dict[str, Any]:
    return research_run.read_record(path)


def record_path(value: Path) -> Path:
    return value / "run-record.json" if value.is_dir() else value


def invoke(script: str, *arguments: str, cwd: Path | None = None) -> str:
    return run([sys.executable, str(SCRIPT_DIR / script), *arguments], cwd=cwd)


def cmd_init(args: argparse.Namespace) -> int:
    checkout = args.checkout.resolve()
    root = Path(git(checkout, "rev-parse", "--show-toplevel")).resolve()
    if git(root, "status", "--porcelain"):
        raise SystemExit("local-pinned initialization requires a clean target worktree")
    revision = git(root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SystemExit("target HEAD did not resolve to a full commit")
    repository = normalize_repository_url(git(root, "remote", "get-url", args.remote))
    shallow = git(root, "rev-parse", "--is-shallow-repository") == "true"
    source_mode = "local-pinned-shallow" if shallow else "local-pinned"
    skill_ref = args.skill_ref or skill_identity(SKILL_ROOT)
    slug = repository_slug(repository)
    report_root = args.research_root.resolve() / "reports" / slug
    target = report_root / revision[:7]
    if target.exists():
        raise SystemExit(f"research session already exists: {target}")
    report_root.mkdir(parents=True, exist_ok=True)
    run_id = args.run_id or f"{slug}-full-report-{revision[:7]}"
    analysis_date = args.analysis_date or datetime.now(timezone.utc).date().isoformat()

    with tempfile.TemporaryDirectory(prefix=f".{revision[:7]}.", dir=report_root) as temporary:
        staging = Path(temporary)
        snapshot = staging / "repository-snapshot.json"
        run([sys.executable, str(SCRIPT_DIR / "repository_snapshot.py"), str(root), "--format", "json"], stdout_path=snapshot)
        invoke(
            "research_run.py", "init", "--output", str(staging / "run-record.json"), "--run-id", run_id,
            "--run-class", args.run_class, "--analysis-date", analysis_date, "--target-repository", repository,
            "--target-revision", revision, "--skill-ref", skill_ref, "--source-mode", source_mode,
            "--worktree-state", "clean",
        )
        invoke(
            "candidate_ledger.py", "init", "--output", str(staging / "candidate-ledger.json"), "--run-id", run_id,
            "--target-repository", repository, "--target-revision", revision, "--skill-ref", skill_ref,
            "--source-mode", source_mode, "--freeze-boundary", args.freeze_boundary,
        )
        invoke(
            "research_run.py", "advance", "--record", str(staging / "run-record.json"), "--to", "inventoried",
            "--artifact", f"repository_snapshot={snapshot}",
        )
        os.replace(staging, target)
    result = {
        "report_directory": str(target),
        "run_record": str(target / "run-record.json"),
        "candidate_ledger": str(target / "candidate-ledger.json"),
        "repository_snapshot": str(target / "repository-snapshot.json"),
        "phase": "inventoried",
        "target_repository": repository,
        "target_revision": revision,
        "skill_ref": skill_ref,
    }
    print(json.dumps(result, indent=2, sort_keys=True) if args.format == "json" else "\n".join(f"{key}: {value}" for key, value in result.items()))
    return 0


def status_value(path: Path) -> dict[str, Any]:
    path = record_path(path.resolve())
    record = load_record(path)
    phase = record.get("phase")
    if phase not in research_run.PHASES:
        raise SystemExit(f"unsupported research phase: {phase!r}")
    next_phase = research_run.PHASES[research_run.PHASES.index(phase) + 1] if phase != "finalized" else None
    supplied: dict[str, Path] = {}
    candidates = {
        "repository_snapshot": path.parent / "repository-snapshot.json",
        "candidate_ledger": path.parent / "candidate-ledger.json",
        "report": path.parent / "PROJECT_INTELLIGENCE_REPORT.md",
        "validation_receipt": path.parent / "validation-receipt.json",
    }
    for key, candidate in candidates.items():
        if candidate.is_file():
            supplied[key] = candidate
    blockers = research_run.gate_phase(record, path, next_phase, supplied) if next_phase and next_phase != "finalized" else []
    return {
        "run_id": record.get("run_id"),
        "phase": phase,
        "next_phase": next_phase,
        "ready": not blockers,
        "blockers": blockers,
        "next_action": PHASE_ACTIONS[phase],
        "run_record": str(path),
    }


def cmd_status(args: argparse.Namespace) -> int:
    value = status_value(args.session)
    if args.format == "json":
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        print(f"Run: {value['run_id']}")
        print(f"Phase: {value['phase']}")
        print(f"Next phase: {value['next_phase'] or 'none'}")
        print(f"Gate ready: {'yes' if value['ready'] else 'no'}")
        for blocker in value["blockers"]:
            print(f"- {blocker}")
        print(f"Next action: {value['next_action']}")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    path = record_path(args.session.resolve())
    record = load_record(path)
    if record.get("phase") != "synthesized":
        raise SystemExit("publish requires a run in synthesized phase")
    if args.verdict not in research_run.VERDICTS:
        raise SystemExit(f"unsupported verdict: {args.verdict}")
    if str(record.get("source_mode", "")).startswith("local-pinned") and not args.target_checkout:
        raise SystemExit("publish requires --target-checkout for a local-pinned run")
    research_root = args.research_root.resolve()
    index = research_root / "runs.json"
    readme = research_root / "README.md"
    if not index.is_file() or not readme.is_file():
        raise SystemExit("publish requires a research workspace with runs.json and README.md")
    artifacts = record.get("artifacts", {})
    if not isinstance(artifacts, dict):
        raise SystemExit("run record artifacts must be an object")
    report_name = artifacts.get("report")
    ledger_name = artifacts.get("candidate_ledger")
    report = path.parent / str(report_name or "PROJECT_INTELLIGENCE_REPORT.md")
    ledger = path.parent / str(ledger_name or "candidate-ledger.json")
    if not report.is_file() or not ledger.is_file():
        raise SystemExit("publish requires existing report and candidate ledger artifacts")
    receipt = path.parent / "validation-receipt.json"
    validator = [
        str(report), "--run-record", str(path), "--candidate-ledger", str(ledger),
        "--strict", "--write-receipt", str(receipt),
    ]
    if args.target_checkout:
        validator.extend(["--target-checkout", str(args.target_checkout.resolve())])
    invoke("validate_report.py", *validator)
    invoke("research_run.py", "advance", "--record", str(path), "--to", "report-validated", "--artifact", f"validation_receipt={receipt}")
    invoke(
        "research_run.py", "finalize", "--record", str(path), "--report", report.relative_to(path.parent).as_posix(),
        "--candidate-ledger", ledger.relative_to(path.parent).as_posix(), "--verdict", args.verdict,
    )
    invoke("build_research_index.py", str(research_root), "--write")
    final_validator = [
        str(report), "--run-record", str(path), "--candidate-ledger", str(ledger), "--run-index", str(index), "--strict",
    ]
    if args.target_checkout:
        final_validator.extend(["--target-checkout", str(args.target_checkout.resolve())])
    invoke("validate_report.py", *final_validator)
    workspace_validator = research_root / "scripts" / "validate_workspace.py"
    if workspace_validator.is_file():
        run([sys.executable, str(workspace_validator), str(research_root)])
    print(json.dumps({"run_record": str(path), "phase": "finalized", "receipt": str(receipt), "index": str(index)}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    initialize = subparsers.add_parser("init", help="initialize and inventory a clean local checkout")
    initialize.add_argument("--checkout", type=Path, required=True)
    initialize.add_argument("--research-root", type=Path, required=True)
    initialize.add_argument("--remote", default="origin")
    initialize.add_argument("--run-id")
    initialize.add_argument("--run-class", default="full-project-intelligence-report")
    initialize.add_argument("--analysis-date")
    initialize.add_argument("--skill-ref")
    initialize.add_argument("--freeze-boundary", default="Before project-public explanations and external comparator review")
    initialize.add_argument("--format", choices=("text", "json"), default="text")
    initialize.set_defaults(handler=cmd_init)

    status = subparsers.add_parser("status", help="show phase, gate readiness, and next action")
    status.add_argument("session", type=Path, help="report directory or run-record.json")
    status.add_argument("--format", choices=("text", "json"), default="text")
    status.set_defaults(handler=cmd_status)

    publish = subparsers.add_parser("publish", help="strictly validate, finalize, and index a synthesized report")
    publish.add_argument("session", type=Path, help="report directory or run-record.json")
    publish.add_argument("--research-root", type=Path, required=True)
    publish.add_argument("--target-checkout", type=Path)
    publish.add_argument("--verdict", required=True)
    publish.set_defaults(handler=cmd_publish)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
