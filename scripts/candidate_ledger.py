#!/usr/bin/env python3
"""Create, freeze, validate, and render structured technical-candidate ledgers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SOURCE_MODES = {"local-pinned", "local-pinned-shallow", "remote-pinned", "indexed-snapshot", "docs-only"}
PROVENANCE = {"repository-original", "adapted", "upstream", "published", "conventional", "unknown"}
COVERAGE_STATUS = {"discovered", "analyzed", "excluded", "gap"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SystemExit(f"ledger does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid ledger JSON: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit("ledger root must be an object")
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


def frozen_payload(ledger: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in ledger.items() if key != "freeze"}


def payload_hash(ledger: dict[str, Any]) -> str:
    encoded = json.dumps(frozen_payload(ledger), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate(ledger: dict[str, Any], require_frozen: bool = False) -> list[str]:
    errors: list[str] = []
    for key in ("schema_version", "run_id", "target", "skill_revision", "source_mode", "coverage", "traces", "candidates"):
        if key not in ledger:
            errors.append(f"missing field: {key}")
    if ledger.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported schema_version")
    if ledger.get("source_mode") not in SOURCE_MODES:
        errors.append(f"unsupported source_mode: {ledger.get('source_mode')!r}")
    target = ledger.get("target")
    if not isinstance(target, dict) or not target.get("repository") or not target.get("revision"):
        errors.append("target.repository and target.revision are required")
    candidates = ledger.get("candidates", [])
    if not isinstance(candidates, list):
        errors.append("candidates must be an array")
        candidates = []
    ids: list[str] = []
    ranks: list[int] = []
    for index, item in enumerate(candidates):
        prefix = f"candidate[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for key in ("id", "name", "rank", "tier", "problem", "mechanism", "value", "evidence", "counterevidence", "provenance"):
            if key not in item:
                errors.append(f"{prefix} missing {key}")
        candidate_id = item.get("id")
        if isinstance(candidate_id, str):
            ids.append(candidate_id)
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", candidate_id):
                errors.append(f"{prefix}.id must be kebab-case")
        rank = item.get("rank")
        if isinstance(rank, int) and rank > 0:
            ranks.append(rank)
        else:
            errors.append(f"{prefix}.rank must be a positive integer")
        tier = item.get("tier")
        if not isinstance(tier, int) or not 0 <= tier <= 5:
            errors.append(f"{prefix}.tier must be between 0 and 5")
        if item.get("provenance") not in PROVENANCE:
            errors.append(f"{prefix}.provenance is unsupported")
        for key in ("evidence", "counterevidence", "runtime_hypotheses"):
            if key in item and not isinstance(item[key], list):
                errors.append(f"{prefix}.{key} must be an array")
        if tier and tier >= 3 and item.get("parent") and not item.get("nested_scan"):
            errors.append(f"{prefix} is Tier 3+ with a parent but has no nested_scan note")
    if len(ids) != len(set(ids)):
        errors.append("candidate IDs must be unique")
    if len(ranks) != len(set(ranks)):
        errors.append("candidate ranks must be unique")
    if ranks and sorted(ranks) != list(range(1, len(ranks) + 1)):
        errors.append("candidate ranks must be contiguous from 1")
    if require_frozen or ledger.get("freeze"):
        freeze = ledger.get("freeze")
        if not isinstance(freeze, dict) or not freeze.get("content_sha256"):
            errors.append("frozen ledger requires freeze.content_sha256")
        elif freeze["content_sha256"] != payload_hash(ledger):
            errors.append("frozen ledger content hash does not match; frozen content was modified")
    return errors


def ensure_mutable(ledger: dict[str, Any]) -> None:
    if ledger.get("freeze"):
        raise SystemExit("ledger is frozen and cannot be modified")


def cmd_init(args: argparse.Namespace) -> int:
    if args.output.exists() and not args.force:
        raise SystemExit(f"ledger already exists: {args.output}")
    value = {
        "schema_version": SCHEMA_VERSION,
        "run_id": args.run_id,
        "target": {"repository": args.target_repository, "revision": args.target_revision},
        "skill_revision": args.skill_ref,
        "source_mode": args.source_mode,
        "freeze_boundary": args.freeze_boundary,
        "coverage": [],
        "traces": [],
        "candidates": [],
    }
    atomic_write(args.output, value)
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    ledger = load(args.ledger)
    ensure_mutable(ledger)
    if args.status not in COVERAGE_STATUS:
        raise SystemExit(f"unsupported coverage status: {args.status}")
    if not 0 <= args.depth <= 5:
        raise SystemExit("coverage depth must be between 0 and 5")
    item = {"area": args.area, "status": args.status, "depth": args.depth, "importance": args.importance, "notes": args.notes}
    coverage = ledger.setdefault("coverage", [])
    coverage[:] = [existing for existing in coverage if existing.get("area") != args.area]
    coverage.append(item)
    atomic_write(args.ledger, ledger)
    return 0


def cmd_trace(args: argparse.Namespace) -> int:
    ledger = load(args.ledger)
    ensure_mutable(ledger)
    traces = ledger.setdefault("traces", [])
    traces[:] = [existing for existing in traces if existing.get("name") != args.name]
    traces.append({"name": args.name, "summary": args.summary, "steps": args.step})
    atomic_write(args.ledger, ledger)
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    ledger = load(args.ledger)
    ensure_mutable(ledger)
    candidate = {
        "id": args.id,
        "name": args.name,
        "rank": args.rank,
        "tier": args.tier,
        "parent": args.parent,
        "problem": args.problem,
        "mechanism": args.mechanism,
        "value": args.value,
        "evidence": args.evidence,
        "counterevidence": args.counterevidence,
        "provenance": args.provenance,
        "runtime_hypotheses": args.runtime_hypothesis,
        "nested_scan": args.nested_scan,
    }
    candidates = ledger.setdefault("candidates", [])
    if any(existing.get("id") == args.id for existing in candidates):
        raise SystemExit(f"candidate already exists: {args.id}")
    candidates.append(candidate)
    atomic_write(args.ledger, ledger)
    return 0


def cmd_freeze(args: argparse.Namespace) -> int:
    ledger = load(args.ledger)
    ensure_mutable(ledger)
    errors = validate(ledger)
    if not ledger.get("coverage"):
        errors.append("cannot freeze without coverage entries")
    if not ledger.get("traces"):
        errors.append("cannot freeze without a representative trace")
    if not ledger.get("candidates"):
        errors.append("cannot freeze without candidates")
    if errors:
        raise SystemExit("cannot freeze ledger:\n- " + "\n- ".join(errors))
    ledger["freeze"] = {
        "recorded_at": utc_now(),
        "evidence_origin": args.evidence_origin,
        "note": args.note,
    }
    ledger["freeze"]["content_sha256"] = payload_hash(ledger)
    atomic_write(args.ledger, ledger)
    return 0


def render_markdown(ledger: dict[str, Any]) -> str:
    target = ledger.get("target", {})
    lines = [
        "# Frozen technical-candidate ledger",
        "",
        "## Run identity",
        "",
        f"- Run: `{ledger.get('run_id', '')}`",
        f"- Target: `{target.get('repository', '')}`",
        f"- Revision: `{target.get('revision', '')}`",
        f"- Source mode: `{ledger.get('source_mode', '')}`",
        f"- Skill revision: `{ledger.get('skill_revision', '')}`",
        f"- Freeze boundary: {ledger.get('freeze_boundary', '')}",
        "",
        "## Coverage ledger",
        "",
        "| Area | Status | Depth | Importance | Notes |",
        "|---|---|---:|---|---|",
    ]
    for item in sorted(ledger.get("coverage", []), key=lambda value: value.get("area", "")):
        lines.append(f"| {markdown_cell(item.get('area', ''))} | {markdown_cell(item.get('status', ''))} | {markdown_cell(item.get('depth', ''))} | {markdown_cell(item.get('importance', ''))} | {markdown_cell(item.get('notes', ''))} |")
    lines.extend(["", "## Representative traces", ""])
    for trace in ledger.get("traces", []):
        lines.extend([f"### {trace.get('name', '')}", "", trace.get("summary", ""), ""])
        for index, step in enumerate(trace.get("steps", []), 1):
            lines.append(f"{index}. {step}")
        lines.append("")
    lines.extend([
        "## Frozen candidate ranking",
        "",
        "| Rank | Candidate | Tier | Mechanism and value | Provenance | Counterevidence |",
        "|---:|---|---:|---|---|---|",
    ])
    for item in sorted(ledger.get("candidates", []), key=lambda value: value.get("rank", 0)):
        mechanism = f"{item.get('mechanism', '')} {item.get('value', '')}".strip()
        counter = "; ".join(item.get("counterevidence", []))
        lines.append(f"| {markdown_cell(item.get('rank', ''))} | {markdown_cell(item.get('name', ''))} | {markdown_cell(item.get('tier', ''))} | {markdown_cell(mechanism)} | {markdown_cell(item.get('provenance', ''))} | {markdown_cell(counter)} |")
    freeze = ledger.get("freeze")
    if freeze:
        lines.extend([
            "",
            "## Freeze record",
            "",
            f"- Recorded at: `{freeze.get('recorded_at', '')}`",
            f"- Evidence origin: `{freeze.get('evidence_origin', '')}`",
            f"- Content SHA-256: `{freeze.get('content_sha256', '')}`",
            f"- Note: {freeze.get('note', '')}",
        ])
    return "\n".join(lines).rstrip() + "\n"


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def cmd_render(args: argparse.Namespace) -> int:
    ledger = load(args.ledger)
    errors = validate(ledger, require_frozen=args.require_frozen)
    if errors:
        raise SystemExit("invalid ledger:\n- " + "\n- ".join(errors))
    output = render_markdown(ledger)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate(load(args.ledger), require_frozen=args.require_frozen)
    if errors:
        print(f"Candidate ledger: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Candidate ledger: valid")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--run-id", required=True)
    init.add_argument("--target-repository", required=True)
    init.add_argument("--target-revision", required=True)
    init.add_argument("--skill-ref", required=True)
    init.add_argument("--source-mode", required=True)
    init.add_argument("--freeze-boundary", required=True)
    init.add_argument("--force", action="store_true")
    init.set_defaults(handler=cmd_init)
    coverage = subparsers.add_parser("coverage")
    coverage.add_argument("--ledger", type=Path, required=True)
    coverage.add_argument("--area", required=True)
    coverage.add_argument("--status", required=True)
    coverage.add_argument("--depth", type=int, required=True)
    coverage.add_argument("--importance", required=True)
    coverage.add_argument("--notes", default="")
    coverage.set_defaults(handler=cmd_coverage)
    trace = subparsers.add_parser("trace")
    trace.add_argument("--ledger", type=Path, required=True)
    trace.add_argument("--name", required=True)
    trace.add_argument("--summary", required=True)
    trace.add_argument("--step", action="append", default=[])
    trace.set_defaults(handler=cmd_trace)
    add = subparsers.add_parser("add")
    add.add_argument("--ledger", type=Path, required=True)
    add.add_argument("--id", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--rank", type=int, required=True)
    add.add_argument("--tier", type=int, required=True)
    add.add_argument("--parent")
    add.add_argument("--problem", required=True)
    add.add_argument("--mechanism", required=True)
    add.add_argument("--value", required=True)
    add.add_argument("--evidence", action="append", default=[])
    add.add_argument("--counterevidence", action="append", default=[])
    add.add_argument("--provenance", required=True)
    add.add_argument("--runtime-hypothesis", action="append", default=[])
    add.add_argument("--nested-scan")
    add.set_defaults(handler=cmd_add)
    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--ledger", type=Path, required=True)
    freeze.add_argument("--evidence-origin", default="contemporaneous")
    freeze.add_argument("--note", required=True)
    freeze.set_defaults(handler=cmd_freeze)
    render = subparsers.add_parser("render")
    render.add_argument("--ledger", type=Path, required=True)
    render.add_argument("--output", type=Path)
    render.add_argument("--require-frozen", action="store_true")
    render.set_defaults(handler=cmd_render)
    check = subparsers.add_parser("validate")
    check.add_argument("--ledger", type=Path, required=True)
    check.add_argument("--require-frozen", action="store_true")
    check.set_defaults(handler=cmd_validate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
