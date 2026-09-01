#!/usr/bin/env python3
"""Validate the self-contained structure and local links of this Skill package."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from urllib.parse import unquote


NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LOCAL_LINK = re.compile(r"\[[^]]*\]\(([^)]+)\)")


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise ValueError("SKILL.md requires YAML frontmatter delimited by ---")
    block = text[4 : text.index("\n---\n", 4)]
    values: dict[str, str] = {}
    for line in block.splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip().strip("'\"")
    return values


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    skill = root / "SKILL.md"
    if not skill.is_file():
        return ["missing SKILL.md"]
    try:
        metadata = frontmatter(skill)
    except (OSError, UnicodeError, ValueError) as error:
        return [str(error)]
    name = metadata.get("name", "")
    description = metadata.get("description", "")
    if not NAME.fullmatch(name):
        errors.append("frontmatter name must be lowercase kebab-case")
    if root.name != name:
        errors.append(f"folder name {root.name!r} does not match Skill name {name!r}")
    if not description:
        errors.append("frontmatter description is required")
    elif len(description) > 1024:
        errors.append("frontmatter description exceeds 1024 characters")

    for markdown in sorted(root.rglob("*.md")):
        if ".git" in markdown.parts:
            continue
        text = markdown.read_text(encoding="utf-8")
        for raw in LOCAL_LINK.findall(text):
            destination = raw.strip().split(maxsplit=1)[0].strip("<>\"")
            if not destination or destination.startswith(("http://", "https://", "mailto:", "#")):
                continue
            local = unquote(destination.split("#", 1)[0])
            if local and not (markdown.parent / local).resolve().is_file():
                errors.append(f"broken local link in {markdown.relative_to(root)}: {destination}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_root", type=Path, nargs="?", default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    errors = validate(args.skill_root.resolve())
    if errors:
        print(f"Skill package validation: {len(errors)} error(s)")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Skill package is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
