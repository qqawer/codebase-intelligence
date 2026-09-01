#!/usr/bin/env python3
"""Validate reproducibility and publication invariants of a Project Intelligence Report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import unquote


VERDICTS = {
    "PASS",
    "PASS WITH EVIDENCE LIMITATIONS",
    "TARGETED PASS",
    "PARTIAL PASS",
    "FAIL",
}
SOURCE_MODES = {"local-pinned", "local-pinned-shallow", "remote-pinned", "indexed-snapshot", "docs-only"}
GITHUB_BLOB = re.compile(r"https://github\.com/([^/]+)/([^/]+)/blob/([^/)#\s]+)/([^#)\s]+)(?:#L(\d+)(?:-L(\d+))?)?")
MACHINE_PATH = re.compile(r"(?:(?<![A-Za-z0-9:/])/(?:Users|home)/|[A-Za-z]:\\Users\\)")
CREDENTIAL_URL = re.compile(r"https?://[^/\s:@]+:[^/\s@]+@")


@dataclass
class Finding:
    severity: str
    code: str
    message: str


def load_json(path: Path, findings: list[Finding]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        findings.append(Finding("error", "record-missing", f"run record does not exist: {path}"))
        return {}
    except json.JSONDecodeError as error:
        findings.append(Finding("error", "record-json", f"invalid run record JSON: {error}"))
        return {}
    if not isinstance(value, dict):
        findings.append(Finding("error", "record-root", "run record root must be an object"))
        return {}
    return value


def repository_identity(url: str) -> tuple[str, str] | None:
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", url)
    return (match.group(1).lower(), match.group(2).lower()) if match else None


def git_value(checkout: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(checkout), *args], capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def validate_record(record: dict[str, Any], findings: list[Finding]) -> None:
    required = ["schema_version", "run_id", "run_class", "analysis_date", "source_mode", "target", "skill", "entries"]
    for key in required:
        if key not in record:
            findings.append(Finding("error", "record-field", f"run record is missing '{key}'"))
    if record.get("schema_version") not in {1, 2}:
        findings.append(Finding("error", "record-schema", "unsupported run record schema_version"))
    elif record.get("schema_version") == 1:
        findings.append(Finding("warning", "legacy-record", "run record uses legacy schema version 1 without phase gates"))
    if record.get("schema_version") == 2:
        if record.get("phase") not in {"synthesized", "report-validated", "finalized"}:
            findings.append(Finding("error", "record-phase", "report validation requires synthesized or later phase"))
        if not isinstance(record.get("phase_history"), list):
            findings.append(Finding("error", "phase-history", "schema version 2 requires phase_history"))
    if record.get("source_mode") not in SOURCE_MODES:
        findings.append(Finding("error", "source-mode", f"unsupported source mode: {record.get('source_mode')!r}"))
    if "verdict" in record and record["verdict"] not in VERDICTS:
        findings.append(Finding("error", "verdict", f"unsupported verdict: {record['verdict']!r}"))
    target = record.get("target")
    if not isinstance(target, dict) or not target.get("repository") or not target.get("revision"):
        findings.append(Finding("error", "target-identity", "target.repository and target.revision are required"))
    if not isinstance(record.get("entries", []), list):
        findings.append(Finding("error", "entries", "entries must be an array"))


def validate_report_text(text: str, record: dict[str, Any], findings: list[Finding]) -> None:
    if MACHINE_PATH.search(text):
        findings.append(Finding("error", "machine-path", "report contains a machine-specific absolute path"))
    if CREDENTIAL_URL.search(text):
        findings.append(Finding("error", "credential-url", "report contains a URL with embedded credentials"))
    revision = str(record.get("target", {}).get("revision", ""))
    if revision and revision not in text:
        findings.append(Finding("warning", "revision-not-visible", "target revision is not visible in the report"))
    checks = {
        "analysis-date": (r"(?i)analysis date|analysis_date|分析日期|研究日期", "analysis date is not visible in the report"),
        "source-mode-visible": (r"(?i)source mode|source_mode|证据模式", "source mode is not visible in the report"),
        "worktree-state": (r"(?i)worktree|work tree|工作树", "worktree state is not visible in the report"),
        "runtime-section": (r"(?im)^##+\s+.*(?:runtime|validation|运行|验证)", "runtime validation section was not detected"),
        "uncertainty": (r"(?i)uncertainty|evidence limitation|不确定|证据限制", "uncertainty/evidence-limit discussion was not detected"),
        "coverage": (r"(?i)coverage ledger|覆盖账本|coverage", "coverage ledger was not detected"),
    }
    for code, (pattern, message) in checks.items():
        if not re.search(pattern, text):
            findings.append(Finding("warning", code, message))

    entries = record.get("entries", []) if isinstance(record.get("entries"), list) else []
    passed_categories = {str(entry.get("category", "")).lower() for entry in entries if entry.get("status") == "passed"}
    if re.search(r"(?i)tests? (?:all )?passed|测试.*通过|\d+/\d+.*(?:tests?|测试)", text) and not any("test" in item for item in passed_categories):
        findings.append(Finding("warning", "test-evidence", "report states passing tests but the run record has no passed test entry"))
    measured_outcome = re.search(
        r"(?i)(?:\bmeasured\s+(?:at|to|as)\b|\b\d+(?:\.\d+)?%\s+(?:faster|slower|less memory|lower memory)|\b(?:faster|slower|lower memory|more scalable)\s+than\b|实测(?:为|达到|提升|降低)|(?:提升|降低)\s*\d+(?:\.\d+)?%)",
        text,
    )
    if measured_outcome and not any("bench" in item or "performance" in item for item in passed_categories):
        findings.append(Finding("warning", "measurement-evidence", "report uses measurement/performance language without a passed benchmark entry"))
    if re.search(r"(?i)innovati|original|原创|创新", text) and not re.search(r"(?i)comparator|precedent|originality|上游|先例|原创性", text):
        findings.append(Finding("warning", "originality-evidence", "originality language appears without comparator/provenance discussion"))


def validate_links(text: str, record: dict[str, Any], checkout: Path | None, findings: list[Finding]) -> None:
    target = record.get("target", {}) if isinstance(record.get("target"), dict) else {}
    target_identity = repository_identity(str(target.get("repository", "")))
    revision = str(target.get("revision", ""))
    for owner, repository, ref, encoded_path, start, end in GITHUB_BLOB.findall(text):
        if target_identity == (owner.lower(), repository.lower()):
            if revision and ref != revision:
                findings.append(Finding("error", "link-revision", f"target source link uses {ref}, expected {revision}: {encoded_path}"))
            if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
                findings.append(Finding("error", "mutable-source-link", f"target source link is not pinned to a full commit: {ref}"))
            if start and end and int(start) > int(end):
                findings.append(Finding("error", "line-range", f"source link has reversed line range: {encoded_path}#L{start}-L{end}"))
            if checkout:
                local = checkout / unquote(encoded_path)
                if not local.is_file():
                    findings.append(Finding("error", "link-path", f"linked target file does not exist: {encoded_path}"))
                elif start:
                    line_count = sum(1 for _ in local.open("rb"))
                    upper = int(end or start)
                    if upper > line_count:
                        findings.append(Finding("error", "line-bounds", f"source link line {upper} exceeds {encoded_path} ({line_count} lines)"))


def validate_checkout(checkout: Path, record: dict[str, Any], findings: list[Finding]) -> None:
    if not checkout.is_dir():
        findings.append(Finding("error", "checkout", f"target checkout is not a directory: {checkout}"))
        return
    expected = str(record.get("target", {}).get("revision", ""))
    actual = git_value(checkout, "rev-parse", "HEAD")
    if not actual:
        findings.append(Finding("error", "checkout-git", "could not read target checkout revision"))
    elif expected and actual != expected:
        findings.append(Finding("error", "checkout-revision", f"target checkout is {actual}, expected {expected}"))


def validate_ledger(path: Path | None, record: dict[str, Any], findings: list[Finding]) -> None:
    blind = "blind" in str(record.get("run_class", "")).lower()
    if blind and path is None:
        findings.append(Finding("error", "ledger-required", "blind run requires a candidate ledger"))
    if path is not None and not path.is_file():
        findings.append(Finding("error", "ledger-missing", f"candidate ledger does not exist: {path}"))
    elif path is not None and path.suffix.lower() == ".json":
        try:
            from candidate_ledger import load as load_ledger, validate as validate_candidate_ledger
            errors = validate_candidate_ledger(load_ledger(path), require_frozen=True)
        except (ImportError, SystemExit) as error:
            findings.append(Finding("error", "ledger-json", f"candidate ledger could not be validated: {error}"))
        else:
            for error in errors:
                findings.append(Finding("error", "ledger-json", error))
            ledger = load_ledger(path)
            if ledger.get("target", {}).get("revision") != record.get("target", {}).get("revision"):
                findings.append(Finding("error", "ledger-revision", "candidate ledger revision does not match run record"))


def validate_index(path: Path | None, record: dict[str, Any], findings: list[Finding]) -> None:
    if path is None:
        return
    data = load_json(path, findings)
    runs = data.get("runs", []) if isinstance(data, dict) else []
    if not isinstance(runs, list):
        findings.append(Finding("error", "index-runs", "run index 'runs' must be an array"))
        return
    ids = [item.get("id") for item in runs if isinstance(item, dict)]
    duplicates = sorted({item for item in ids if item and ids.count(item) > 1})
    if duplicates:
        findings.append(Finding("error", "index-duplicate", f"duplicate run IDs: {', '.join(duplicates)}"))
    run_id = record.get("run_id")
    matches = [item for item in runs if isinstance(item, dict) and item.get("id") == run_id]
    if not matches:
        findings.append(Finding("warning", "index-missing", f"run index has no entry for {run_id!r}"))
    elif matches[0].get("target_revision") != record.get("target", {}).get("revision"):
        findings.append(Finding("error", "index-revision", "run index target revision does not match run record"))


def render(findings: list[Finding], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps({"findings": [asdict(item) for item in findings], "summary": {"errors": sum(item.severity == "error" for item in findings), "warnings": sum(item.severity == "warning" for item in findings)}}, indent=2))
        return
    errors = sum(item.severity == "error" for item in findings)
    warnings = sum(item.severity == "warning" for item in findings)
    print(f"Report validation: {errors} error(s), {warnings} warning(s)")
    for item in findings:
        print(f"- {item.severity.upper()} [{item.code}] {item.message}")


def write_receipt(path: Path, report: Path, findings: list[Finding]) -> None:
    value = {
        "schema_version": 1,
        "validated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "report": report.name,
        "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest() if report.is_file() else None,
        "errors": sum(item.severity == "error" for item in findings),
        "warnings": sum(item.severity == "warning" for item in findings),
        "finding_codes": [item.code for item in findings],
    }
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--run-record", type=Path, required=True)
    parser.add_argument("--candidate-ledger", type=Path)
    parser.add_argument("--target-checkout", type=Path)
    parser.add_argument("--run-index", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--strict", action="store_true", help="return nonzero for warnings")
    parser.add_argument("--write-receipt", type=Path)
    args = parser.parse_args()

    findings: list[Finding] = []
    if not args.report.is_file():
        findings.append(Finding("error", "report-missing", f"report does not exist: {args.report}"))
        text = ""
    else:
        text = args.report.read_text(encoding="utf-8")
        if not text.strip():
            findings.append(Finding("error", "report-empty", "report is empty"))
    record = load_json(args.run_record, findings)
    if record:
        validate_record(record, findings)
        validate_report_text(text, record, findings)
        if args.target_checkout:
            validate_checkout(args.target_checkout, record, findings)
        validate_links(text, record, args.target_checkout, findings)
        validate_ledger(args.candidate_ledger, record, findings)
        validate_index(args.run_index, record, findings)
    render(findings, args.format)
    if args.write_receipt:
        args.write_receipt.parent.mkdir(parents=True, exist_ok=True)
        write_receipt(args.write_receipt, args.report, findings)
    errors = any(item.severity == "error" for item in findings)
    warnings = any(item.severity == "warning" for item in findings)
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
