#!/usr/bin/env python3
"""Validate that every skills/*/SKILL.md has well-formed YAML frontmatter
with the required `name` and `description` fields, and that companion files
referenced from the skill body exist next to it."""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

REQUIRED_FIELDS = ("name", "description")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def check_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir}: missing SKILL.md"]

    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append(f"{skill_md}: missing frontmatter block")
        return errors

    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"{skill_md}: frontmatter block not closed")
        return errors

    try:
        frontmatter = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        errors.append(f"{skill_md}: invalid YAML frontmatter: {exc}")
        return errors

    if not isinstance(frontmatter, dict):
        errors.append(f"{skill_md}: frontmatter must be a mapping")
        return errors

    for field in REQUIRED_FIELDS:
        value = frontmatter.get(field)
        if not value or not str(value).strip():
            errors.append(f"{skill_md}: missing required frontmatter field '{field}'")

    name = frontmatter.get("name")
    if isinstance(name, str):
        if name != skill_dir.name:
            errors.append(
                f"{skill_md}: frontmatter name '{name}' does not match directory '{skill_dir.name}'"
            )
        if not NAME_RE.match(name):
            errors.append(f"{skill_md}: name '{name}' must be lowercase kebab-case")

    # Companion markdown files referenced in the body must exist.
    body = parts[2]
    for ref in re.findall(r"`([a-z0-9-]+\.md)`", body):
        if not (skill_dir / ref).exists():
            errors.append(f"{skill_md}: references companion file '{ref}' which is missing")

    return errors


def main() -> int:
    skills_root = Path(__file__).resolve().parents[2] / "skills"
    if not skills_root.is_dir():
        print(f"skills directory not found at {skills_root}", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        all_errors.extend(check_skill(skill_dir))

    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    found = sorted(p.name for p in skills_root.iterdir() if p.is_dir())
    print(f"OK: {len(found)} skills validated: {', '.join(found)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
