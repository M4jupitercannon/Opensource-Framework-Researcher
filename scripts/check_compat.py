#!/usr/bin/env python3
"""Lightweight compatibility checks for the feature-research skill."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "install.sh",
    "SKILL.md",
    "AGENTS.md",
    "README.md",
    "topics/default_topics.md",
    "topics/topic_json_schema.md",
    "scope/chip_scope_map.md",
    "sources/source_playbook.md",
    "agents/researcher.md",
    "agents/analyzer_external_repos.md",
    "agents/monitor_existence.md",
    "agents/monitor_scope.md",
    "agents/monitor_feature.md",
    "templates/REPORT_template.md",
]

FORBIDDEN_TEMPLATE_PATTERNS = [
    re.compile(r"`(?:Bash|Read|Write|Agent)`"),
    re.compile(r"\bgeneral-purpose Agent\b"),
    re.compile(r"\bcall only `"),
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def parse_frontmatter(markdown: str) -> dict[str, str]:
    if not markdown.startswith("---\n"):
        fail("SKILL.md is missing YAML frontmatter")
    try:
        _, raw_frontmatter, _ = markdown.split("---\n", 2)
    except ValueError:
        fail("SKILL.md frontmatter is not closed")

    fields: dict[str, str] = {}
    for line in raw_frontmatter.splitlines():
        if not line or line.startswith(" ") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip('"')
    return fields


def check_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")


def check_skill_frontmatter() -> None:
    fields = parse_frontmatter(read("SKILL.md"))
    for field in ("name", "description", "compatibility"):
        if not fields.get(field):
            fail(f"SKILL.md frontmatter missing {field!r}")
    if fields["name"] != "feature-research":
        fail("SKILL.md name must be 'feature-research'")
    if "claude-code" not in fields["compatibility"]:
        fail("SKILL.md compatibility must include claude-code")
    if "cursor" not in fields["compatibility"]:
        fail("SKILL.md compatibility must include cursor")
    if "codex" not in fields["compatibility"]:
        fail("SKILL.md compatibility must include codex")


def check_codex_shim() -> None:
    agents = read("AGENTS.md")
    for expected in ("SKILL.md", "serial fallback", "scope/chip_scope_map.md", "agents/researcher.md"):
        if expected not in agents:
            fail(f"AGENTS.md does not reference {expected!r}")


def check_template_wording() -> None:
    for path in sorted((ROOT / "agents").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_TEMPLATE_PATTERNS:
            if pattern.search(text):
                fail(f"{path.relative_to(ROOT)} contains stale Claude-only wording: {pattern.pattern}")


def check_readme() -> None:
    readme = read("README.md")
    for expected in ("Claude Code", "Cursor", "Codex", "AGENTS.md", "install.sh", "scripts/check_compat.py"):
        if expected not in readme:
            fail(f"README.md does not mention {expected!r}")


def check_installer() -> None:
    installer = ROOT / "install.sh"
    if not installer.stat().st_mode & 0o111:
        fail("install.sh is not executable")
    text = installer.read_text(encoding="utf-8")
    for expected in ("claude", "cursor", "codex", ".claude/skills", ".cursor/skills", ".codex/AGENTS.md"):
        if expected not in text:
            fail(f"install.sh does not mention {expected!r}")


def main() -> int:
    check_required_files()
    check_skill_frontmatter()
    check_codex_shim()
    check_template_wording()
    check_readme()
    check_installer()
    print("OK: feature-research compatibility checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
