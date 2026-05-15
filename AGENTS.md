# Feature Research Agent Instructions

Use this repository as the `feature-research` workflow when the user asks for the state, roadmap, status, dashboard, or report for a `(chip vendor, framework, feature)` triple such as `NVIDIA + vLLM + EP` or `AMD + SGLang + PD-disaggregation`.

## Canonical Workflow

Read `SKILL.md` first. It is the source of truth for inputs, hard rules, phase order, output paths, audit requirements, and hand-off format.

Then read only the supporting files needed for the current phase:

- `scope/chip_scope_map.md` for chip-vendor scope.
- `sources/source_playbook.md` for GitHub, web, MLPerf, and InferenceX source conventions.
- `topics/default_topics.md` and `topics/topic_json_schema.md` for topic definitions and JSON shape.
- `agents/researcher.md`, `agents/analyzer_external_repos.md`, `agents/monitor_existence.md`, `agents/monitor_scope.md`, and `agents/monitor_feature.md` for role-specific checklists.
- `agents/plot_ecosystem_activity.md` and `scripts/plot_ecosystem_activity.py` for the optional Phase 4 ecosystem activity plot.
- `templates/REPORT_template.md` for per-vendor report synthesis, and `templates/COMPARISON_REPORT_template.md` for the Phase-5 side-by-side comparison report (rendered only when `len(chip_list) == 2` per `SKILL.md` hard rule 9).
- `sources/signals_service_discovered.md` for the live `signals-service` MCP probe verdict (`MCP_DETAIL_USABLE` / `MCP_SQL_USABLE` capability flags + resolved canonical strings) consumed by the Session-intake / MCP pre-flight step in `SKILL.md`.

## Codex / opencode Execution

Codex and opencode both read `AGENTS.md` natively and do not need separate skill loading to use this repo. Treat `AGENTS.md` as the entry point and `SKILL.md` as the runbook.

If no sub-agent or delegation tool is available, use `SKILL.md` serial fallback mode:

1. Resolve scope per vendor in `chip_list` and write `out_dir/{vendor}/scope.json` for each. The session-wide `out_dir/search_window.json` and `out_dir/_signals_schema.json` are written once at the session root.
2. Run each Phase-1a researcher role one at a time per vendor, writing one `out_dir/{vendor}/topics/{topic_name}.json` file per role.
3. Run `analyzer_external_repos` per vendor after that vendor's three prerequisite topic JSONs (`completed_subfeatures.json`, `kernels_or_components.json`, `open_issues.json`) exist.
4. Run the three monitors per vendor in order — `monitor_existence`, `monitor_scope`, then `monitor_feature` — each writing its `verification_*.md` under `out_dir/{vendor}/`.
5. Apply required audit fixes per vendor to that vendor's topic JSON files before the next stage.
6. Synthesize `out_dir/{vendor}/REPORT.md` per vendor from the verified topic JSONs and verification reports.
7. Run the `plot_ecosystem_activity` role once per chosen metric (`merged_prs`, `opened_issues`, `closed_issues`) — Phase 4 in `SKILL.md`. This is best-effort context outside the three-stage audit trail; if the user picks `skip`, do NOT create `out_dir/ecosystem_plots/`, continue to Phase 5 when `len(chip_list) == 2`, otherwise advance directly to Phase 6. (Phase 4 being skipped does NOT change the Phase 5 gate — the gate is purely `len(chip_list) == 2`.) Each invocation writes one CSV + PNG + methods note under top-level `out_dir/ecosystem_plots/` (per C8.1, NOT under any vendor folder). Requires `python` ≥ 3.9 with `matplotlib` available (`pip install matplotlib`).
8. **Only when `len(chip_list) == 2`**, render `templates/COMPARISON_REPORT_template.md` to `out_dir/COMPARISON_REPORT.md` — Phase 5 in `SKILL.md`. Always after Phase 4 so the comparison report can embed the ecosystem plots via `[render_if_present ecosystem_plots]`. Skipped when `len(chip_list) == 1`.
9. Print the Phase-6 hand-off paragraph naming every artifact produced by steps 1–8: per-vendor `out_dir/{vendor}/REPORT.md` + the three `out_dir/{vendor}/verification_*.md` files + `out_dir/{vendor}/scope.json` + per-vendor topic JSONs, plus session-wide `out_dir/search_window.json`, `out_dir/_signals_schema.json`, the `out_dir/ecosystem_plots/` set when Phase 4 ran, and `out_dir/COMPARISON_REPORT.md` when Phase 5 ran.

Keep the same artifact names, JSON schema, verification gates, and re-run budget as `SKILL.md`. A "re-spawn" in serial mode means re-running the relevant role from scratch with the offending refs or strictness failures embedded in the role prompt.

## Non-Negotiables

- Verify every included PR, issue, RFC, URL, and verbatim quote before writing a topic JSON.
- Do not fabricate PR numbers, issue states, dates, performance figures, or source quotes.
- Do not use generic `Q1`/`Q2` report sections; use the named topic headings.
- Preserve audit trail arrays in `_meta` for scope drops, feature strictness removals, recategorizations, and deduplication.
- Keep researcher/analyzer/monitor roles flat: role prompts must not launch nested workers.
