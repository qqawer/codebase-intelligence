#!/usr/bin/env python3
"""Build a research workspace run index and README report table from run records."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


BEGIN = "<!-- BEGIN GENERATED FULL REPORT INDEX -->"
END = "<!-- END GENERATED FULL REPORT INDEX -->"
CANONICAL_FIELDS = {
    "id", "date", "class", "target_repository", "target_revision", "skill_ref", "source_mode",
    "candidate_ledger", "run_record", "report", "verdict", "runtime_summary", "generated_from_run_record",
    "record_status",
}


def load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SystemExit(f"missing file: {path}") from error
    except json.JSONDecodeError as error:
        raise SystemExit(f"invalid JSON in {path}: {error}") from error
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be an object: {path}")
    return value


def inside(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise SystemExit(f"artifact escapes research root: {path}") from error
    return resolved


def artifact_path(root: Path, record_path: Path, value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise SystemExit(f"{record_path}: artifact {field!r} must be a relative path string")
    candidate = inside(root, record_path.parent / value)
    if not candidate.is_file():
        raise SystemExit(f"{record_path}: artifact {field!r} does not exist: {value}")
    return candidate.relative_to(root.resolve()).as_posix()


def record_entry(root: Path, record_path: Path, old: dict[str, Any] | None) -> dict[str, Any]:
    record = load_object(record_path)
    required = ("run_id", "run_class", "analysis_date", "source_mode", "target", "skill", "artifacts", "verdict")
    missing = [key for key in required if key not in record]
    if missing:
        raise SystemExit(f"{record_path}: missing fields: {', '.join(missing)}")
    if record.get("schema_version") != 2 or record.get("phase") != "finalized":
        raise SystemExit(f"{record_path}: generated index requires a finalized schema version 2 record")
    target = record["target"]
    skill = record["skill"]
    artifacts = record["artifacts"]
    if not all(isinstance(item, dict) for item in (target, skill, artifacts)):
        raise SystemExit(f"{record_path}: target, skill, and artifacts must be objects")

    entry: dict[str, Any] = {
        "id": record["run_id"],
        "date": record["analysis_date"],
        "class": record["run_class"],
        "target_repository": target.get("repository"),
        "target_revision": target.get("revision"),
        "skill_ref": skill.get("revision"),
        "source_mode": record["source_mode"],
        "run_record": record_path.resolve().relative_to(root.resolve()).as_posix(),
        "report": artifact_path(root, record_path, artifacts.get("report"), "report"),
        "verdict": record["verdict"],
        "runtime_summary": record.get("runtime_summary", {}),
        "generated_from_run_record": True,
    }
    ledger = artifact_path(root, record_path, artifacts.get("candidate_ledger"), "candidate_ledger")
    if ledger:
        entry["candidate_ledger"] = ledger
    if old:
        for key, value in old.items():
            if key not in CANONICAL_FIELDS:
                entry[key] = value
    if not all(entry.get(key) for key in ("id", "date", "class", "target_repository", "target_revision", "skill_ref", "source_mode", "report", "verdict")):
        raise SystemExit(f"{record_path}: one or more required index values are empty")
    return entry


def report_title(path: Path, repository_url: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"(?m)^#\s+(.+?)\s*$", text)
    if match:
        title = re.sub(r"(?i)\s+(?:project\s+)?intelligence\s+report.*$", "", match.group(1)).strip(" :-")
        if title:
            return title
    return repository_url.rstrip("/").removesuffix(".git").rsplit("/", 1)[-1]


def runtime_text(entry: dict[str, Any]) -> str:
    if isinstance(entry.get("runtime"), str) and entry["runtime"]:
        return entry["runtime"]
    summary = entry.get("runtime_summary", {})
    counts = summary.get("counts", summary) if isinstance(summary, dict) else {}
    parts = []
    for key, label in (("passed", "passed"), ("failed", "failed"), ("unavailable", "unavailable"), ("not-run", "not run"), ("observed", "externally observed")):
        value = counts.get(key, 0) if isinstance(counts, dict) else 0
        if value:
            parts.append(f"{value} {label}")
    if isinstance(summary, dict):
        parts.append("end-to-end passed" if summary.get("end_to_end") else "no end-to-end run")
    return "; ".join(parts) or "Not recorded"


def render_table(root: Path, runs: list[dict[str, Any]]) -> str:
    rows = ["| Repository | Revision | Runtime validation | Report |", "|---|---|---|---|"]
    full = [item for item in runs if Path(str(item.get("report", ""))).name == "PROJECT_INTELLIGENCE_REPORT.md"]
    for item in sorted(full, key=lambda value: (str(value.get("date", "")), str(value.get("id", "")))):
        report = inside(root, root / str(item["report"]))
        if not report.is_file():
            raise SystemExit(f"indexed report does not exist: {item['report']}")
        title = str(item.get("display_name") or report_title(report, str(item.get("target_repository", ""))))
        revision = str(item.get("target_revision", ""))[:7]
        rows.append(f"| {title} | `{revision}` | {runtime_text(item)} | [Project Intelligence Report]({item['report']}) |")
    return "\n".join(rows)


def update_readme(text: str, table: str) -> str:
    block = f"{BEGIN}\n{table}\n{END}"
    if BEGIN in text or END in text:
        if text.count(BEGIN) != 1 or text.count(END) != 1 or text.index(BEGIN) > text.index(END):
            raise SystemExit("README has malformed generated report index markers")
        return text[: text.index(BEGIN)] + block + text[text.index(END) + len(END) :]
    match = re.search(r"(?ms)^## Full report examples\s*\n.*?(?=^##\s)", text)
    if not match:
        raise SystemExit("README needs a '## Full report examples' section or generated markers")
    replacement = f"## Full report examples\n\n{block}\n\n"
    return text[: match.start()] + replacement + text[match.end() :]


def atomic_text(path: Path, text: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def expected_outputs(root: Path) -> tuple[str, str]:
    index_path = root / "runs.json"
    readme_path = root / "README.md"
    index = load_object(index_path)
    old_runs = index.get("runs")
    if not isinstance(old_runs, list) or not all(isinstance(item, dict) for item in old_runs):
        raise SystemExit("runs.json 'runs' must be an array of objects")
    old_by_id: dict[str, dict[str, Any]] = {}
    for item in old_runs:
        run_id = item.get("id")
        if not isinstance(run_id, str) or not run_id:
            raise SystemExit("every indexed run needs a non-empty string id")
        if run_id in old_by_id:
            raise SystemExit(f"duplicate run id in runs.json: {run_id}")
        old_by_id[run_id] = item

    generated: dict[str, dict[str, Any]] = {}
    for record_path in sorted(root.glob("reports/**/run-record.json")):
        record = load_object(record_path)
        run_id = record.get("run_id")
        if not isinstance(run_id, str) or not run_id:
            raise SystemExit(f"{record_path}: missing run_id")
        if run_id in generated:
            raise SystemExit(f"duplicate run id in run records: {run_id}")
        generated[run_id] = record_entry(root, record_path, old_by_id.get(run_id))

    merged = [item for item in old_runs if item["id"] not in generated] + list(generated.values())
    merged.sort(key=lambda item: (str(item.get("date", "")), str(item.get("id", ""))))
    output_index = dict(index)
    output_index["schema_version"] = 2
    output_index["generated_run_records"] = len(generated)
    output_index["runs"] = merged
    index_text = json.dumps(output_index, ensure_ascii=False, indent=2) + "\n"
    readme_text = update_readme(readme_path.read_text(encoding="utf-8"), render_table(root, merged))
    return index_text, readme_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("research_root", type=Path)
    parser.add_argument("--write", action="store_true", help="write generated outputs instead of checking for drift")
    args = parser.parse_args()
    root = args.research_root.resolve()
    expected_index, expected_readme = expected_outputs(root)
    index_path, readme_path = root / "runs.json", root / "README.md"
    if args.write:
        atomic_text(index_path, expected_index)
        atomic_text(readme_path, expected_readme)
        print(f"updated {index_path} and {readme_path}")
        return 0
    stale = []
    if index_path.read_text(encoding="utf-8") != expected_index:
        stale.append("runs.json")
    if readme_path.read_text(encoding="utf-8") != expected_readme:
        stale.append("README.md")
    if stale:
        print("research index drift: " + ", ".join(stale))
        return 1
    print("research index is current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
