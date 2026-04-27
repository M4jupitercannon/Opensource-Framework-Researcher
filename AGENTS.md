# Feature Research Agent Instructions

Use this repository as the `feature-research` workflow when the user asks for the state, roadmap, status, dashboard, or report for a `(chip vendor, framework, feature)` triple such as `NVIDIA + vLLM + EP` or `AMD + SGLang + PD-disaggregation`.

## Canonical Workflow

Read `SKILL.md` first. It is the source of truth for inputs, hard rules, phase order, output paths, audit requirements, and hand-off format.

Then read only the supporting files needed for the current phase:

- `scope/chip_scope_map.md` for chip-vendor scope.
- `sources/source_playbook.md` for GitHub, web, MLPerf, and InferenceX source conventions.
- `topics/default_topics.md` and `topics/topic_json_schema.md` for topic definitions and JSON shape.
- `agents/researcher.md`, `agents/analyzer_external_repos.md`, `agents/monitor_existence.md`, `agents/monitor_scope.md`, and `agents/monitor_feature.md` for role-specific checklists.
- `templates/REPORT_template.md` for final report synthesis.

## Codex Execution

Codex does not need native skill loading to use this repo. Treat `AGENTS.md` as the entry point and `SKILL.md` as the runbook.

If no sub-agent or delegation tool is available, use `SKILL.md` serial fallback mode:

1. Resolve scope and write `scope.json`.
2. Run each Phase-1a researcher role one at a time, writing one `topics/{topic_name}.json` file per role.
3. Run `analyzer_external_repos` after `completed_subfeatures.json`, `kernels_or_components.json`, and `open_issues.json` exist.
4. Run `monitor_existence`, `monitor_scope`, and `monitor_feature` in that order.
5. Apply required audit fixes to the topic JSON files before the next stage.
6. Synthesize `REPORT.md` from the verified topic JSONs and verification reports.

Keep the same artifact names, JSON schema, verification gates, and re-run budget as `SKILL.md`. A "re-spawn" in serial mode means re-running the relevant role from scratch with the offending refs or strictness failures embedded in the role prompt.

## Non-Negotiables

- Verify every included PR, issue, RFC, URL, and verbatim quote before writing a topic JSON.
- Do not fabricate PR numbers, issue states, dates, performance figures, or source quotes.
- Do not use generic `Q1`/`Q2` report sections; use the named topic headings.
- Preserve audit trail arrays in `_meta` for scope drops, feature strictness removals, recategorizations, and deduplication.
- Keep researcher/analyzer/monitor roles flat: role prompts must not launch nested workers.
