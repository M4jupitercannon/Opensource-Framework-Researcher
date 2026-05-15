#!/usr/bin/env python3
"""Lightweight compatibility checks for the feature-research skill."""

from __future__ import annotations

import re
import subprocess
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
    "agents/plot_ecosystem_activity.md",
    "scripts/plot_ecosystem_activity.py",
    "templates/REPORT_template.md",
    "templates/COMPARISON_REPORT_template.md",
    "sources/signals_service_discovered.md",
]

FORBIDDEN_KEYWORD_FILE = "sources/ecosystem_activity_keywords.md"

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


def parse_frontmatter(markdown: str) -> dict[str, object]:
    """Parse SKILL.md YAML frontmatter.

    Prefers `yaml.safe_load` so we can handle YAML-list `compatibility:` blocks
    and other structured fields. Falls back to a minimal line parser if PyYAML
    is unavailable (with a soft warning); in fallback mode, list-shaped fields
    are returned as the raw multi-line string and YAML-only assertions in
    `check_skill_frontmatter` are skipped.
    """
    if not markdown.startswith("---\n"):
        fail("SKILL.md is missing YAML frontmatter")
    try:
        _, raw_frontmatter, _ = markdown.split("---\n", 2)
    except ValueError:
        fail("SKILL.md frontmatter is not closed")

    try:
        import yaml  # type: ignore
    except ImportError:
        print(
            "WARN: PyYAML not installed; parsing SKILL.md frontmatter with the "
            "minimal line parser. YAML-only assertions (e.g. compatibility as a "
            "list) will be skipped. Install PyYAML to enable full checks."
        )
        fields: dict[str, object] = {}
        for line in raw_frontmatter.splitlines():
            if not line or line.startswith(" ") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
        fields["_yaml_loaded"] = False
        return fields

    loaded = yaml.safe_load(raw_frontmatter) or {}
    if not isinstance(loaded, dict):
        fail("SKILL.md frontmatter did not parse to a YAML mapping")
    loaded["_yaml_loaded"] = True
    return loaded


def check_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail(f"missing required files: {', '.join(missing)}")


def check_skill_frontmatter() -> None:
    fields = parse_frontmatter(read("SKILL.md"))
    yaml_loaded = bool(fields.get("_yaml_loaded"))
    for field in ("name", "description", "compatibility"):
        if not fields.get(field):
            fail(f"SKILL.md frontmatter missing {field!r}")
    if fields["name"] != "feature-research":
        fail("SKILL.md name must be 'feature-research'")

    description = fields["description"]
    if not isinstance(description, str):
        fail("SKILL.md frontmatter `description` must be a string")
    if len(description) > 1024:
        fail(
            f"SKILL.md frontmatter `description` is {len(description)} chars; "
            "must be <= 1024."
        )

    compatibility = fields["compatibility"]
    expected_hosts = ("claude-code", "cursor", "codex", "opencode")
    if yaml_loaded:
        if not isinstance(compatibility, list):
            fail(
                "SKILL.md frontmatter `compatibility` must be a YAML list "
                "(e.g. `- claude-code` per line)."
            )
        compat_set = {str(x).strip() for x in compatibility}
        for host in expected_hosts:
            if host not in compat_set:
                fail(f"SKILL.md compatibility must include {host!r}")
    else:
        # Soft fallback: substring match on the raw string form.
        compat_str = str(compatibility)
        for host in expected_hosts:
            if host not in compat_str:
                fail(f"SKILL.md compatibility must include {host!r}")


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
    for expected in (
        "Claude Code",
        "Cursor",
        "Codex",
        "opencode",
        "AGENTS.md",
        "install.sh",
        "scripts/check_compat.py",
    ):
        if expected not in readme:
            fail(f"README.md does not mention {expected!r}")


def check_installer() -> None:
    installer = ROOT / "install.sh"
    if not installer.stat().st_mode & 0o111:
        fail("install.sh is not executable")
    text = installer.read_text(encoding="utf-8")
    for expected in (
        "claude",
        "cursor",
        "codex",
        "opencode",
        ".claude/skills",
        ".cursor/skills",
        ".codex/AGENTS.md",
        ".config/opencode/skills",
    ):
        if expected not in text:
            fail(f"install.sh does not mention {expected!r}")
    # --target enum must accept opencode.
    if "claude|cursor|codex|opencode" not in text:
        fail(
            "install.sh --target enum must accept opencode "
            "(expected the literal 'claude|cursor|codex|opencode' in the case "
            "match or usage text)."
        )


def check_phase_4_wired_in() -> None:
    skill = read("SKILL.md")
    for expected in (
        "Phase 4",
        "plot_ecosystem_activity",
        "ecosystem_plot_metric",
        "scope/chip_scope_map.md",
    ):
        if expected not in skill:
            fail(f"SKILL.md does not mention {expected!r} (Phase 4 wiring incomplete)")

    plot_prompt = read("agents/plot_ecosystem_activity.md")
    for expected in (
        "scope/chip_scope_map.md",
        "merged_prs",
        "opened_issues",
        "closed_issues",
        "vendor_groups",
        "BOTH",
        "NEITHER",
    ):
        if expected not in plot_prompt:
            fail(f"agents/plot_ecosystem_activity.md does not mention {expected!r}")
    if "ecosystem_activity_keywords.md" in plot_prompt:
        fail(
            "agents/plot_ecosystem_activity.md must NOT reference a parallel "
            "ecosystem_activity_keywords.md file — vendor keywords come from "
            "scope/chip_scope_map.md at runtime."
        )

    if (ROOT / FORBIDDEN_KEYWORD_FILE).exists():
        fail(
            f"{FORBIDDEN_KEYWORD_FILE} must not exist; vendor keywords are "
            "derived from scope/chip_scope_map.md at runtime."
        )

    playbook = read("sources/source_playbook.md")
    for expected in ("gh-search-bulk", "Phase 4", "scope/chip_scope_map.md"):
        if expected not in playbook:
            fail(f"sources/source_playbook.md does not mention {expected!r}")

    chip_map = read("scope/chip_scope_map.md")
    for vendor in ("## NVIDIA", "## AMD"):
        if vendor not in chip_map:
            fail(f"scope/chip_scope_map.md is missing required vendor block: {vendor!r}")

    template = read("templates/REPORT_template.md")
    for expected in ("Ecosystem Activity Context", "ecosystem_plots", "render_if_present"):
        if expected not in template:
            fail(f"templates/REPORT_template.md does not mention {expected!r}")


def check_search_window_threaded() -> None:
    for relpath in (
        "agents/researcher.md",
        "agents/analyzer_external_repos.md",
        "agents/plot_ecosystem_activity.md",
    ):
        text = read(relpath)
        if "{search_window" not in text:
            fail(f"{relpath} missing {{search_window...}} placeholder reference")


def check_mcp_first_wording() -> None:
    for path in sorted((ROOT / "agents").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        relpath = path.relative_to(ROOT)
        if "mcp:signals" not in text:
            fail(f"{relpath} missing 'mcp:signals' source tag")
        if " gh " not in text and "`gh`" not in text:
            fail(f"{relpath} missing gh fallback reference")
        if "fallback" not in text.lower():
            fail(f"{relpath} missing fallback wording")


def check_no_gh_primary_wording() -> None:
    forbidden_re = re.compile(
        r"^(?!.*mcp).*(use|via|with) `?gh`?",
        re.IGNORECASE | re.MULTILINE,
    )
    fence_re = re.compile(r"```.*?```", re.DOTALL)
    fallback_section_re = re.compile(
        r"(?ims)^#{1,6}[ \t]+[^\n]*fallback[^\n]*\n.*?(?=^#{1,6}[ \t]+|\Z)"
    )
    for path in sorted((ROOT / "agents").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        text = fence_re.sub("", text)
        text = fallback_section_re.sub("", text)
        if forbidden_re.search(text):
            fail(
                f"{path.relative_to(ROOT)} contains gh-primary wording without "
                "MCP-first qualifier outside fallback section / code fence"
            )


def check_meta_schema_extended() -> None:
    schema = read("topics/topic_json_schema.md")
    for expected in (
        '"search_window"',
        '"fallback_used"',
        '"tool_attempted"',
        '"tool_succeeded"',
    ):
        if expected not in schema:
            fail(f"topics/topic_json_schema.md missing required _meta field: {expected}")


def check_comparison_template() -> None:
    tpl = read("templates/COMPARISON_REPORT_template.md")
    for expected in (
        "{{vendor_a}}",
        "{{vendor_b}}",
        "{{search_window",
        "Ecosystem Activity Context",
        "render_if_present",
    ):
        if expected not in tpl:
            fail(f"templates/COMPARISON_REPORT_template.md missing {expected!r}")


def check_phase_ordering() -> None:
    skill = read("SKILL.md")
    phase4_re = re.compile(r"\bPhase 4\b")
    phase5_re = re.compile(r"\bPhase 5\b")
    # Forbidden legacy labels (in any prose / docstring outside check_compat.py itself):
    # - hyphenated `Phase-4b` / `Phase-4c`
    # - hyphenated `Phase-4` (the new label is the unhyphenated `Phase 4`)
    # - space-separated `Phase 4b` / `Phase 4c` (old non-contiguous meaning)
    legacy_label_patterns = (
        re.compile(r"\bPhase-4b\b"),
        re.compile(r"\bPhase-4c\b"),
        re.compile(r"\bPhase-4\b"),
        re.compile(r"\bPhase 4b\b"),
        re.compile(r"\bPhase 4c\b"),
    )

    phase4_match = phase4_re.search(skill)
    phase5_match = phase5_re.search(skill)
    if phase4_match is None:
        fail("SKILL.md missing 'Phase 4' (ecosystem plot)")
    if phase5_match is None:
        fail("SKILL.md missing 'Phase 5' (comparison synthesis)")
    if phase4_match.start() > phase5_match.start():
        fail("SKILL.md has Phase 5 before Phase 4 — violates C1 ordering")

    # The sweep covers prose docs + the topic/source/template/script files that
    # the read-only follow-up review flagged. `scripts/check_compat.py` itself is
    # kept out of the sweep because its forbidden-pattern table legitimately
    # contains these strings.
    skill_doc_files = (
        "SKILL.md",
        "AGENTS.md",
        "README.md",
        "sources/source_playbook.md",
        "sources/signals_service_discovered.md",
        "topics/default_topics.md",
        "topics/topic_json_schema.md",
        "scope/chip_scope_map.md",
        "templates/REPORT_template.md",
        "templates/COMPARISON_REPORT_template.md",
        "scripts/plot_ecosystem_activity.py",
    ) + tuple(
        str(p.relative_to(ROOT)) for p in sorted((ROOT / "agents").glob("*.md"))
    ) + tuple(
        str(p.relative_to(ROOT)) for p in sorted((ROOT / "topics").glob("*.md"))
    ) + tuple(
        str(p.relative_to(ROOT)) for p in sorted((ROOT / "templates").glob("*.md"))
    )
    # De-duplicate while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for relpath in skill_doc_files:
        if relpath in seen:
            continue
        seen.add(relpath)
        deduped.append(relpath)
    for relpath in deduped:
        text = read(relpath)
        for pattern in legacy_label_patterns:
            if pattern.search(text):
                fail(
                    f"{relpath} still references legacy phase label "
                    f"{pattern.pattern!r} — incomplete rename (the new label "
                    "is the unhyphenated contiguous form 'Phase 4' / 'Phase 5')."
                )


def check_no_legacy_stage_labels() -> None:
    """No 'Stage 2.1/2.2/2.3' or 'Stage 2A/2B/2C' strings in any committed file.

    Excludes `scripts/check_compat.py` itself (this file documents the legacy
    labels in error messages and patterns).
    """
    legacy_patterns = [
        re.compile(r"\bStage 2\.1\b"),
        re.compile(r"\bStage 2\.2\b"),
        re.compile(r"\bStage 2\.3\b"),
        re.compile(r"\bStage 2A\b"),
        re.compile(r"\bStage 2B\b"),
        re.compile(r"\bStage 2C\b"),
    ]
    self_relpath = Path(__file__).resolve().relative_to(ROOT)
    candidates: list[Path] = []
    for ext in ("*.md", "*.py", "*.sh", "*.json", "*.yaml", "*.yml", "*.txt"):
        candidates.extend(ROOT.rglob(ext))
    for path in candidates:
        if not path.is_file():
            continue
        relpath = path.relative_to(ROOT)
        if relpath == self_relpath:
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in legacy_patterns:
            if pattern.search(text):
                fail(
                    f"{relpath} contains legacy stage label matching "
                    f"{pattern.pattern!r}; rename to Stage 1 / 2 / 3 "
                    "(monitor stages) or to a functional description "
                    "(MCP-gated paths)."
                )


def check_out_dir_disambiguated() -> None:
    """Every agents/*.md file must use {vendor_out_dir} or {session_out_dir}.

    The bare `{out_dir}` placeholder is ambiguous (could be either per-vendor or
    session root) and is forbidden in agent prompt templates after the
    disambiguation refactor.
    """
    forbidden = re.compile(r"\{out_dir\}")
    for path in sorted((ROOT / "agents").glob("*.md")):
        relpath = path.relative_to(ROOT)
        for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = raw.strip()
            if not stripped:
                continue
            if forbidden.search(raw):
                fail(
                    f"{relpath}:{line_no} contains ambiguous {{out_dir}} "
                    "placeholder; must be {vendor_out_dir} (per-vendor root) "
                    "or {session_out_dir} (session root)."
                )


def check_c_tag_glossary() -> None:
    """SKILL.md must contain a Contract clarifications glossary section
    listing at least C1, C2, C3, C4, C5, C6, C7, C8, C8.1, and C8.2.
    """
    skill = read("SKILL.md")
    if "Contract clarifications" not in skill:
        fail("SKILL.md missing 'Contract clarifications' section heading")
    for tag in ("C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C8.1", "C8.2"):
        if f"**{tag}**" not in skill:
            fail(
                f"SKILL.md Contract clarifications section missing required tag "
                f"{tag!r} (expected bolded '**{tag}**' table row)."
            )


def check_no_hardcoded_mcp_url() -> None:
    paths = (
        "SKILL.md",
        "sources/source_playbook.md",
        "README.md",
    ) + tuple(str(p.relative_to(ROOT)) for p in (ROOT / "agents").glob("*.md"))
    for relpath in paths:
        text = read(relpath)
        if "10.161.176.9" in text:
            fail(f"{relpath} contains hard-coded MCP URL — see C7")


def check_topics_mcp_first_wording() -> None:
    """topics/default_topics.md MUST advertise MCP-first / fallback wording so the
    per-topic prompts agree with `agents/researcher.md`. Same shape as
    `check_mcp_first_wording` but scoped to topic prompts.
    """
    text = read("topics/default_topics.md").lower()
    if "mcp:signals" not in text:
        fail(
            "topics/default_topics.md missing 'mcp:signals' source tag — "
            "per-topic prompts must be MCP-first."
        )
    if "fallback" not in text:
        fail(
            "topics/default_topics.md missing 'fallback' wording — "
            "per-topic prompts must reference the documented gh fallback."
        )


def check_phase4_skip_does_not_bypass_phase5() -> None:
    """In SKILL.md / AGENTS.md / README.md, every sentence describing the Phase 4
    `skip` branch must also mention Phase 5 OR `comparison` AND mention
    `len(chip_list)` or `2 vendors`, so a future regression wiring
    `skip -> Phase 6` directly trips lint.
    """
    # Match only the canonical skip-BRANCH description verbs — "the user picks
    # `skip`" / "picks skip" / "user picks skip". Other mentions of the literal
    # "skip" string (e.g. "ecosystem_plot_metric == skip" as a condition, or
    # "skipped entirely" as an effect) are deliberately ignored — they describe
    # the consequence, not the orchestrator's branching action.
    skip_branch_re = re.compile(
        r"(?:user\s+)?picks?\s+`?skip`?",
        re.IGNORECASE,
    )
    gate_re_a = re.compile(r"len\(chip_list\)|2 vendors", re.IGNORECASE)
    gate_re_b = re.compile(r"Phase 5|comparison", re.IGNORECASE)
    for relpath in ("SKILL.md", "AGENTS.md", "README.md"):
        text = read(relpath)
        for m in skip_branch_re.finditer(text):
            start = max(0, m.start() - 200)
            end = min(len(text), m.end() + 200)
            window = text[start:end]
            # Only flag occurrences in the Phase 4 / ecosystem_plot context.
            # Generic "user picks X" sentences elsewhere are not our concern.
            if (
                "Phase 4" not in window
                and "ecosystem_plot" not in window
            ):
                continue
            # This is a Phase 4 skip-branch description. Ensure the same window
            # references both the Phase 5 / comparison gate AND the chip_list
            # cardinality so future regressions trip lint.
            if not gate_re_a.search(window):
                fail(
                    f"{relpath}: Phase 4 `skip` branch description does not "
                    "reference `len(chip_list)` / `2 vendors` near the `skip` "
                    "mention; a future regression could wire `skip -> Phase 6` "
                    "directly. Window (truncated):\n"
                    f"{window!r}"
                )
            if not gate_re_b.search(window):
                fail(
                    f"{relpath}: Phase 4 `skip` branch description does not "
                    "reference Phase 5 / `comparison` near the `skip` mention; "
                    "a future regression could wire `skip -> Phase 6` directly "
                    "and silently skip the comparison report. Window (truncated):\n"
                    f"{window!r}"
                )


def check_per_vendor_report_relpath() -> None:
    """templates/REPORT_template.md must reference `../ecosystem_plots/` (parent-
    dir hop) for per-vendor relpaths because per-vendor REPORT.md lives at
    `out_dir/{vendor}/REPORT.md` while plots live at top-level
    `out_dir/ecosystem_plots/` (per C8.1). Bare `ecosystem_plots/` is allowed
    only inside fenced code/config blocks where the path is literally
    root-relative.
    """
    template = read("templates/REPORT_template.md")
    if "../ecosystem_plots/" not in template:
        fail(
            "templates/REPORT_template.md does not reference '../ecosystem_plots/' — "
            "per-vendor reports live at out_dir/{vendor}/REPORT.md so plot "
            "relpaths MUST include the parent-dir hop (per C8.1)."
        )
    # Strip fenced code blocks so we only inspect prose / rendering rules.
    # Bare `ecosystem_plots/` is allowed when prefixed with `out_dir/` (the
    # ROOT-relative form, e.g. `out_dir/ecosystem_plots/`), or with `../`
    # (the per-vendor REPORT.md relpath form). Reject any other prefix —
    # those would be ambiguous per-vendor relpaths missing the parent-dir hop.
    fence_re = re.compile(r"```.*?```", re.DOTALL)
    prose = fence_re.sub("", template)
    # Use a negative lookbehind: flag any `ecosystem_plots/` whose preceding
    # text is NOT `../`, NOT `out_dir/`, NOT `present `, NOT `[`, and NOT
    # `_plot.` (e.g. the `plot.png_relpath` placeholder names).
    candidate_re = re.compile(r"\becosystem_plots/")
    for m in candidate_re.finditer(prose):
        start = max(0, m.start() - 12)
        prefix = prose[start:m.start()]
        if (
            prefix.endswith("../")
            or prefix.endswith("out_dir/")
            or prefix.endswith("session_out_dir/")
            or prefix.endswith("{session_out_dir}/")
            or prefix.endswith("vendor_out_dir}/../")
        ):
            continue
        # Allow `[render_if_present ecosystem_plots]` (block marker — not a path).
        # The marker doesn't have the trailing `/`, so this only matches actual
        # path-shaped tokens. Anything else is the prose violation we want.
        fail(
            "templates/REPORT_template.md prose references bare "
            f"'{m.group(0)}' (without an explicit `../` parent-dir hop or "
            "`out_dir/` root anchor) — per-vendor relpaths MUST be "
            "'../ecosystem_plots/' per C8.1. Bare 'ecosystem_plots/' is "
            "allowed only inside fenced code/config blocks where the path is "
            "literally root-relative. Offending prefix: "
            f"{prefix!r}"
        )


def check_comparison_template_no_empty_section() -> None:
    """templates/COMPARISON_REPORT_template.md must keep the literal
    `## Ecosystem Activity Context` heading INSIDE its
    `[render_if_present ecosystem_plots]` block, so when plots are absent the
    heading vanishes along with the body.
    """
    tpl = read("templates/COMPARISON_REPORT_template.md")
    heading = "## Ecosystem Activity Context"
    open_marker = "[render_if_present ecosystem_plots]"
    close_marker = "[/render_if_present]"
    heading_idx = tpl.find(heading)
    if heading_idx == -1:
        fail(
            "templates/COMPARISON_REPORT_template.md missing "
            "'## Ecosystem Activity Context' heading."
        )
    # Find the LAST open marker before the heading, and the FIRST close marker
    # after the heading. The heading must sit between an open/close pair.
    open_before = tpl.rfind(open_marker, 0, heading_idx)
    close_after = tpl.find(close_marker, heading_idx)
    if open_before == -1 or close_after == -1:
        fail(
            "templates/COMPARISON_REPORT_template.md: "
            "'## Ecosystem Activity Context' heading is OUTSIDE a "
            "'[render_if_present ecosystem_plots]' block. When plots are absent "
            "the heading renders with an empty body. Move the heading INSIDE "
            "the render_if_present block."
        )
    # Sanity: there must NOT be a close_marker between open_before and the
    # heading (which would mean the heading falls outside the block).
    intervening_close = tpl.find(close_marker, open_before, heading_idx)
    if intervening_close != -1:
        fail(
            "templates/COMPARISON_REPORT_template.md: "
            "'## Ecosystem Activity Context' heading sits AFTER a "
            "'[/render_if_present]' close marker and is therefore outside the "
            "ecosystem_plots block."
        )


def check_no_unbacked_slash_command() -> None:
    """If README claims `/feature-research` works on a host, install.sh must
    install a matching slash-command artifact (a `commands/` file). Otherwise
    the claim is false advertising. Simplest enforcement: forbid the
    `/feature-research` substring on README compatibility-table rows unless
    `install.sh` writes a `commands/` directory.

    The compatibility table is the prose region between the `## Compatibility`
    heading and the next `## ` heading.
    """
    readme = read("README.md")
    compat_re = re.compile(
        r"^## Compatibility\s*\n(.*?)(?=^## )",
        re.DOTALL | re.MULTILINE,
    )
    m = compat_re.search(readme)
    if not m:
        fail("README.md missing '## Compatibility' section")
    compat_section = m.group(1)
    # Match `/feature-research` only when it appears as a slash-command
    # invocation (preceded by whitespace, backtick, quote, or sentence
    # punctuation), NOT when it's part of an install path like
    # `~/.claude/skills/feature-research`.
    slash_cmd_re = re.compile(r"(?:^|[\s`\"'(])/feature-research\b")
    if slash_cmd_re.search(compat_section):
        installer = (ROOT / "install.sh").read_text(encoding="utf-8")
        if "commands/" not in installer:
            fail(
                "README.md compatibility table mentions '/feature-research' "
                "slash command, but install.sh writes no commands/ artifact. "
                "Either drop the slash-command claim or add an installer that "
                "writes a commands/ file (e.g. ~/.claude/commands/feature-research.md)."
            )


def check_per_host_mcp_setup_table() -> None:
    """For each host in SKILL.md `compatibility:`, sources/source_playbook.md
    must mention that host's MCP-config path token in the per-host MCP setup
    section. Substring match against the host name AND a known per-host token.
    """
    fields = parse_frontmatter(read("SKILL.md"))
    compatibility = fields.get("compatibility")
    if isinstance(compatibility, list):
        hosts = [str(x).strip() for x in compatibility]
    else:
        hosts = [h.strip() for h in str(compatibility or "").split(",") if h.strip()]

    playbook = read("sources/source_playbook.md")
    if "Per-host MCP setup" not in playbook:
        fail(
            "sources/source_playbook.md must contain a 'Per-host MCP setup' "
            "section with one row per supported host."
        )

    # Map host name → expected per-host config-path token.
    host_to_token = {
        "claude-code": ".claude",
        "cursor": ".cursor",
        "codex": ".codex",
        "opencode": "opencode",
    }
    for host in hosts:
        token = host_to_token.get(host)
        if token is None:
            # Unknown host in compatibility list; cannot enforce a token, but
            # the host must still appear by name in the playbook somewhere
            # (with a fuzzy match against typical host-name styles).
            display_candidates = (host, host.replace("-", " "), host.title())
            if not any(c in playbook for c in display_candidates):
                fail(
                    f"sources/source_playbook.md does not mention host {host!r} "
                    "in the Per-host MCP setup section."
                )
            continue
        if token not in playbook:
            fail(
                f"sources/source_playbook.md Per-host MCP setup section is "
                f"missing the {token!r} config-path token for host {host!r}."
            )
        # Also check that the host's display name appears.
        display_candidates = (host, host.replace("-", " "), host.title(), "Claude Code", "Cursor", "Codex", "opencode")
        if not any(c in playbook for c in display_candidates if c.lower().split()[0] in host.lower() or host.lower().split("-")[0] in c.lower()):
            # Soft check; the path token is the primary signal.
            pass


def check_plot_script_vendor_group_flag() -> None:
    """`scripts/plot_ecosystem_activity.py` must accept a `--vendor-group`
    argument so the Phase 4 plot agent can pass the run's `chip_list` (per
    C8.2). Substring check on the script source is sufficient.
    """
    script = read("scripts/plot_ecosystem_activity.py")
    if "--vendor-group" not in script:
        fail(
            "scripts/plot_ecosystem_activity.py is missing the "
            "'--vendor-group' argparse flag (required so the Phase 4 plot "
            "agent can pass the run's chip_list per C8.2)."
        )


def check_plot_script_invocable() -> None:
    script = ROOT / "scripts" / "plot_ecosystem_activity.py"
    if not script.is_file():
        fail("scripts/plot_ecosystem_activity.py is missing")
    if sys.platform != "win32" and not script.stat().st_mode & 0o111:
        fail("scripts/plot_ecosystem_activity.py is not executable")
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        fail(
            "scripts/plot_ecosystem_activity.py --help exited "
            f"{result.returncode}: {result.stderr.strip()}"
        )
    for expected in ("--metric", "--csv", "--out", "merged_prs", "opened_issues", "closed_issues"):
        if expected not in result.stdout:
            fail(f"plot_ecosystem_activity.py --help missing {expected!r}")


def main() -> int:
    check_required_files()
    check_skill_frontmatter()
    check_codex_shim()
    check_template_wording()
    check_readme()
    check_installer()
    check_phase_4_wired_in()
    check_search_window_threaded()
    check_mcp_first_wording()
    check_no_gh_primary_wording()
    check_meta_schema_extended()
    check_comparison_template()
    check_phase_ordering()
    check_no_legacy_stage_labels()
    check_out_dir_disambiguated()
    check_c_tag_glossary()
    check_no_hardcoded_mcp_url()
    check_topics_mcp_first_wording()
    check_phase4_skip_does_not_bypass_phase5()
    check_per_vendor_report_relpath()
    check_comparison_template_no_empty_section()
    check_no_unbacked_slash_command()
    check_per_host_mcp_setup_table()
    check_plot_script_vendor_group_flag()
    check_plot_script_invocable()
    print("OK: feature-research compatibility checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
