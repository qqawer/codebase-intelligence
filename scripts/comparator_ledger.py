#!/usr/bin/env python3
"""Create, freeze, validate, and render structured comparator research ledgers."""

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
SOURCE_TYPES = {"upstream-repository", "peer-repository", "library", "paper", "standard", "documentation", "common-pattern"}
CLASSIFICATIONS = {"conventional-engineering", "strong-engineering", "distinctive-design", "unusual-adaptation", "plausible-innovation", "unverified-innovation-candidate"}
ORIGINALITY_EFFECTS = {"lowers", "supports-distinctiveness", "supports-innovation", "neutral", "inconclusive"}
CONFIDENCE = {"high", "medium", "low"}
CREDENTIAL_URL = re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SystemExit(f"comparator ledger does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid comparator ledger JSON: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit("comparator ledger root must be an object")
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


def payload_hash(ledger: dict[str, Any]) -> str:
    payload = {key: value for key, value in ledger.items() if key != "freeze"}
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def candidate_value(candidate_ledger: dict[str, Any] | None) -> tuple[set[str], set[str]]:
    if candidate_ledger is None:
        return set(), set()
    candidates = candidate_ledger.get("candidates", [])
    if not isinstance(candidates, list):
        return set(), set()
    all_ids = {item.get("id") for item in candidates if isinstance(item, dict) and isinstance(item.get("id"), str)}
    major = {item.get("id") for item in candidates if isinstance(item, dict) and isinstance(item.get("id"), str) and isinstance(item.get("tier"), int) and item["tier"] >= 3}
    return all_ids, major


def validate(ledger: dict[str, Any], candidate_ledger: dict[str, Any] | None = None, require_frozen: bool = False) -> list[str]:
    errors: list[str] = []
    for key in ("schema_version", "run_id", "target", "skill_revision", "scope", "entries", "exclusions"):
        if key not in ledger:
            errors.append(f"missing field: {key}")
    if ledger.get("schema_version") != SCHEMA_VERSION:
        errors.append("unsupported schema_version")
    target = ledger.get("target")
    if not isinstance(target, dict) or not target.get("repository") or not target.get("revision"):
        errors.append("target.repository and target.revision are required")
    scope = ledger.get("scope")
    if not isinstance(scope, str) or not scope.strip():
        errors.append("scope must be a non-empty string")
    entries = ledger.get("entries", [])
    exclusions = ledger.get("exclusions", [])
    if not isinstance(entries, list):
        errors.append("entries must be an array")
        entries = []
    if not isinstance(exclusions, list):
        errors.append("exclusions must be an array")
        exclusions = []
    all_candidates, major_candidates = candidate_value(candidate_ledger)
    if candidate_ledger is not None:
        try:
            from candidate_ledger import validate as validate_candidate_ledger
            errors.extend(f"candidate ledger: {error}" for error in validate_candidate_ledger(candidate_ledger, require_frozen=True))
        except ImportError as error:
            errors.append(f"candidate ledger validator unavailable: {error}")
    covered: set[str] = set()
    ids: list[str] = []
    for index, item in enumerate(entries):
        prefix = f"entry[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        required = ("id", "name", "candidate_ids", "source", "problem", "baseline", "shared_mechanism", "acknowledged_inspiration", "repository_difference", "outcome_difference", "counterevidence", "classification", "originality_effect", "confidence", "evidence")
        for key in required:
            if key not in item:
                errors.append(f"{prefix} missing {key}")
        comparator_id = item.get("id")
        if isinstance(comparator_id, str):
            ids.append(comparator_id)
            if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", comparator_id):
                errors.append(f"{prefix}.id must be kebab-case")
        candidate_ids = item.get("candidate_ids", [])
        if not isinstance(candidate_ids, list) or not candidate_ids or not all(isinstance(value, str) for value in candidate_ids):
            errors.append(f"{prefix}.candidate_ids must be a non-empty string array")
        else:
            covered.update(candidate_ids)
            unknown = sorted(set(candidate_ids) - all_candidates) if candidate_ledger is not None else []
            if unknown:
                errors.append(f"{prefix}.candidate_ids contains unknown IDs: {', '.join(unknown)}")
        source = item.get("source")
        if not isinstance(source, dict):
            errors.append(f"{prefix}.source must be an object")
        else:
            if source.get("type") not in SOURCE_TYPES:
                errors.append(f"{prefix}.source.type is unsupported")
            for key in ("title", "url", "accessed_at"):
                if not isinstance(source.get(key), str) or not source[key].strip():
                    errors.append(f"{prefix}.source.{key} is required")
            url = str(source.get("url", ""))
            if url and not url.startswith("https://"):
                errors.append(f"{prefix}.source.url must use https")
            if CREDENTIAL_URL.search(url):
                errors.append(f"{prefix}.source.url contains credentials")
            if source.get("accessed_at") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(source["accessed_at"])):
                errors.append(f"{prefix}.source.accessed_at must use YYYY-MM-DD")
            if not any(isinstance(source.get(key), str) and source[key].strip() for key in ("revision", "version", "identity_limit")):
                errors.append(f"{prefix}.source requires revision, version, or identity_limit")
            if source.get("type") in {"upstream-repository", "peer-repository"} and source.get("revision") and not re.fullmatch(r"[0-9a-fA-F]{40}", str(source["revision"])):
                errors.append(f"{prefix}.source.revision must be a full commit when present")
        for key in ("name", "problem", "baseline", "shared_mechanism", "acknowledged_inspiration", "repository_difference", "outcome_difference", "counterevidence"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                errors.append(f"{prefix}.{key} must be a non-empty string")
        if item.get("classification") not in CLASSIFICATIONS:
            errors.append(f"{prefix}.classification is unsupported")
        if item.get("originality_effect") not in ORIGINALITY_EFFECTS:
            errors.append(f"{prefix}.originality_effect is unsupported")
        if item.get("confidence") not in CONFIDENCE:
            errors.append(f"{prefix}.confidence is unsupported")
        evidence = item.get("evidence", [])
        if not isinstance(evidence, list) or not evidence or not all(isinstance(value, str) and value.strip() for value in evidence):
            errors.append(f"{prefix}.evidence must be a non-empty string array")
    if len(ids) != len(set(ids)):
        errors.append("comparator IDs must be unique")
    excluded: set[str] = set()
    for index, item in enumerate(exclusions):
        if not isinstance(item, dict) or not isinstance(item.get("candidate_id"), str) or not isinstance(item.get("reason"), str) or not item["reason"].strip():
            errors.append(f"exclusion[{index}] requires candidate_id and non-empty reason")
            continue
        excluded.add(item["candidate_id"])
        if candidate_ledger is not None and item["candidate_id"] not in all_candidates:
            errors.append(f"exclusion[{index}] references unknown candidate: {item['candidate_id']}")
    overlap = sorted(covered.intersection(excluded))
    if overlap:
        errors.append("candidates cannot be both compared and excluded: " + ", ".join(overlap))
    if candidate_ledger is not None:
        if ledger.get("run_id") != candidate_ledger.get("run_id"):
            errors.append("run_id does not match candidate ledger")
        ledger_target = ledger.get("target", {})
        candidate_target = candidate_ledger.get("target", {})
        if not isinstance(ledger_target, dict) or not isinstance(candidate_target, dict) or ledger_target.get("revision") != candidate_target.get("revision"):
            errors.append("target revision does not match candidate ledger")
        if ledger.get("skill_revision") != candidate_ledger.get("skill_revision"):
            errors.append("Skill revision does not match candidate ledger")
        missing_major = sorted(major_candidates - covered - excluded)
        if missing_major:
            errors.append("Tier 3+ candidates lack comparator coverage or explicit exclusion: " + ", ".join(missing_major))
    if require_frozen or ledger.get("freeze"):
        freeze = ledger.get("freeze")
        if not isinstance(freeze, dict) or not freeze.get("content_sha256"):
            errors.append("frozen comparator ledger requires freeze.content_sha256")
        elif freeze["content_sha256"] != payload_hash(ledger):
            errors.append("frozen comparator ledger content hash does not match")
    return errors


def ensure_mutable(ledger: dict[str, Any]) -> None:
    if ledger.get("freeze"):
        raise SystemExit("comparator ledger is frozen and cannot be modified")


def cmd_init(args: argparse.Namespace) -> int:
    if args.output.exists() and not args.force:
        raise SystemExit(f"comparator ledger already exists: {args.output}")
    try:
        record = json.loads(args.run_record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"could not read run record: {error}") from error
    value = {
        "schema_version": SCHEMA_VERSION,
        "run_id": record.get("run_id"),
        "target": record.get("target"),
        "skill_revision": record.get("skill", {}).get("revision"),
        "scope": args.scope,
        "entries": [],
        "exclusions": [],
    }
    atomic_write(args.output, value)
    return 0


def source_value(args: argparse.Namespace) -> dict[str, str]:
    return {key: value for key, value in {
        "type": args.source_type, "title": args.source_title, "url": args.source_url, "revision": args.source_revision,
        "version": args.source_version, "accessed_at": args.accessed_at, "identity_limit": args.identity_limit,
    }.items() if value}


def cmd_add(args: argparse.Namespace) -> int:
    ledger = load(args.ledger)
    ensure_mutable(ledger)
    if any(item.get("id") == args.id for item in ledger.get("entries", []) if isinstance(item, dict)):
        raise SystemExit(f"comparator already exists: {args.id}")
    ledger.setdefault("entries", []).append({
        "id": args.id, "name": args.name, "candidate_ids": args.candidate_id, "source": source_value(args),
        "problem": args.problem, "baseline": args.baseline, "shared_mechanism": args.shared_mechanism,
        "acknowledged_inspiration": args.acknowledged_inspiration, "repository_difference": args.repository_difference,
        "outcome_difference": args.outcome_difference, "counterevidence": args.counterevidence,
        "classification": args.classification, "originality_effect": args.originality_effect,
        "confidence": args.confidence, "evidence": args.evidence,
    })
    atomic_write(args.ledger, ledger)
    return 0


def cmd_exclude(args: argparse.Namespace) -> int:
    ledger = load(args.ledger)
    ensure_mutable(ledger)
    exclusions = ledger.setdefault("exclusions", [])
    exclusions[:] = [item for item in exclusions if item.get("candidate_id") != args.candidate_id]
    exclusions.append({"candidate_id": args.candidate_id, "reason": args.reason})
    atomic_write(args.ledger, ledger)
    return 0


def candidate(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"could not read candidate ledger: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit("candidate ledger root must be an object")
    return value


def cmd_freeze(args: argparse.Namespace) -> int:
    ledger = load(args.ledger)
    ensure_mutable(ledger)
    candidate_ledger = candidate(args.candidate_ledger)
    errors = validate(ledger, candidate_ledger)
    if not ledger.get("entries"):
        errors.append("cannot freeze without comparator entries")
    if errors:
        raise SystemExit("cannot freeze comparator ledger:\n- " + "\n- ".join(errors))
    ledger["freeze"] = {"recorded_at": utc_now(), "evidence_origin": args.evidence_origin, "note": args.note}
    ledger["freeze"]["content_sha256"] = payload_hash(ledger)
    atomic_write(args.ledger, ledger)
    return 0


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_markdown(ledger: dict[str, Any]) -> str:
    target = ledger.get("target", {})
    lines = [
        "# Frozen comparator ledger", "", "## Identity", "", f"- Run: `{ledger.get('run_id', '')}`",
        f"- Target: `{target.get('repository', '')}`", f"- Revision: `{target.get('revision', '')}`",
        f"- Skill revision: `{ledger.get('skill_revision', '')}`", f"- Scope: {ledger.get('scope', '')}", "",
        "## Comparators", "", "| Comparator | Candidates | Source | Difference | Classification | Effect | Confidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in ledger.get("entries", []):
        source = item.get("source", {})
        source_text = f"[{source.get('title', '')}]({source.get('url', '')})"
        lines.append(f"| {markdown_cell(item.get('name', ''))} | {markdown_cell(', '.join(item.get('candidate_ids', [])))} | {source_text} | {markdown_cell(item.get('repository_difference', ''))} | {markdown_cell(item.get('classification', ''))} | {markdown_cell(item.get('originality_effect', ''))} | {markdown_cell(item.get('confidence', ''))} |")
    lines.extend(["", "## Explicit exclusions", ""])
    if ledger.get("exclusions"):
        for item in ledger["exclusions"]:
            lines.append(f"- `{item.get('candidate_id', '')}`: {item.get('reason', '')}")
    else:
        lines.append("None.")
    freeze = ledger.get("freeze")
    if freeze:
        lines.extend(["", "## Freeze record", "", f"- Recorded at: `{freeze.get('recorded_at', '')}`", f"- Evidence origin: `{freeze.get('evidence_origin', '')}`", f"- Content SHA-256: `{freeze.get('content_sha256', '')}`", f"- Note: {freeze.get('note', '')}"])
    return "\n".join(lines).rstrip() + "\n"


def cmd_render(args: argparse.Namespace) -> int:
    ledger = load(args.ledger)
    candidate_ledger = candidate(args.candidate_ledger) if args.candidate_ledger else None
    errors = validate(ledger, candidate_ledger, require_frozen=args.require_frozen)
    if errors:
        raise SystemExit("invalid comparator ledger:\n- " + "\n- ".join(errors))
    output = render_markdown(ledger)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    candidate_ledger = candidate(args.candidate_ledger) if args.candidate_ledger else None
    errors = validate(load(args.ledger), candidate_ledger, require_frozen=args.require_frozen)
    if errors:
        print(f"Comparator ledger: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Comparator ledger: valid")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    init = subparsers.add_parser("init")
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--run-record", type=Path, required=True)
    init.add_argument("--scope", required=True)
    init.add_argument("--force", action="store_true")
    init.set_defaults(handler=cmd_init)
    add = subparsers.add_parser("add")
    add.add_argument("--ledger", type=Path, required=True)
    add.add_argument("--id", required=True)
    add.add_argument("--name", required=True)
    add.add_argument("--candidate-id", action="append", required=True)
    add.add_argument("--source-type", choices=sorted(SOURCE_TYPES), required=True)
    add.add_argument("--source-title", required=True)
    add.add_argument("--source-url", required=True)
    add.add_argument("--source-revision")
    add.add_argument("--source-version")
    add.add_argument("--accessed-at", required=True)
    add.add_argument("--identity-limit")
    add.add_argument("--problem", required=True)
    add.add_argument("--baseline", required=True)
    add.add_argument("--shared-mechanism", required=True)
    add.add_argument("--acknowledged-inspiration", required=True)
    add.add_argument("--repository-difference", required=True)
    add.add_argument("--outcome-difference", required=True)
    add.add_argument("--counterevidence", required=True)
    add.add_argument("--classification", choices=sorted(CLASSIFICATIONS), required=True)
    add.add_argument("--originality-effect", choices=sorted(ORIGINALITY_EFFECTS), required=True)
    add.add_argument("--confidence", choices=sorted(CONFIDENCE), required=True)
    add.add_argument("--evidence", action="append", required=True)
    add.set_defaults(handler=cmd_add)
    exclude = subparsers.add_parser("exclude")
    exclude.add_argument("--ledger", type=Path, required=True)
    exclude.add_argument("--candidate-id", required=True)
    exclude.add_argument("--reason", required=True)
    exclude.set_defaults(handler=cmd_exclude)
    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("--ledger", type=Path, required=True)
    freeze.add_argument("--candidate-ledger", type=Path, required=True)
    freeze.add_argument("--evidence-origin", default="contemporaneous")
    freeze.add_argument("--note", required=True)
    freeze.set_defaults(handler=cmd_freeze)
    render = subparsers.add_parser("render")
    render.add_argument("--ledger", type=Path, required=True)
    render.add_argument("--candidate-ledger", type=Path)
    render.add_argument("--output", type=Path)
    render.add_argument("--require-frozen", action="store_true")
    render.set_defaults(handler=cmd_render)
    check = subparsers.add_parser("validate")
    check.add_argument("--ledger", type=Path, required=True)
    check.add_argument("--candidate-ledger", type=Path)
    check.add_argument("--require-frozen", action="store_true")
    check.set_defaults(handler=cmd_validate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
