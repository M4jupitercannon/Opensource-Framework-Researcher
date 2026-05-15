# `plot_ecosystem_activity` role prompt template — Phase 4

The main agent uses this template for one delegated worker in parallel sub-agent mode, or as a role checklist in serial fallback mode. Per C1, Phase 4 runs **ONCE per session** AFTER each vendor's `out_dir/{vendor}/REPORT.md` has been written by Phase 3 and AFTER the user has confirmed which `metric` to plot, and BEFORE Phase 5 (comparison synthesis, rendered only when `len(chip_list) == 2`).

Substitute the following placeholders:

- `{metric}` — one of `merged_prs`, `opened_issues`, `closed_issues` (drives bucket field and plot title).
- `{repos}` — list of `org/repo` slugs to chart.
- `{search_window}` — full C2 `search_window` object from Phase 0.
- `{date_range}` — inclusive `YYYY-MM..YYYY-MM` window; defaults to `{search_window.start_month}..{search_window.end_month}` per C2 (see Job inputs for the secondary fallback).
- `{vendor_groups}` — list of vendor names to classify against; inherits `chip_list` per C8.2 (defaults to `["AMD", "NVIDIA"]` when the user omits `chip` per C4).
- `{chip_scope_map_path}` — default `scope/chip_scope_map.md`.
- `{data_source}` — `mcp_first` | `gh_only`, from the session's MCP pre-flight per C6.
- `{session_out_dir}` — session root (e.g. `~/research/vllm_EP/2026-05-14/`). All plot artifacts live at `{session_out_dir}/ecosystem_plots/` per C8.1; this role does NOT take a per-vendor `{vendor_out_dir}` because Phase 4 runs once per session.

This is a separate template from `agents/researcher.md` because (a) it does not produce a topic JSON, (b) it is **best-effort ecosystem context** outside the three-stage audit trail (no `monitor_*` re-sample), and (c) it shells out to a Python script (`scripts/plot_ecosystem_activity.py`) to render the chart from a CSV the role itself produces.

**Source of vendor keywords.** The role MUST derive its classification keywords from `{chip_scope_map_path}` at runtime — not from a separate keyword file. The current run's `scope.json` only resolves ONE vendor (the run's chip), so the role re-reads the canonical `scope/chip_scope_map.md` to load the OTHER vendor block(s) needed for the cross-vendor comparison. This keeps a single source of truth for vendor scope language.

---

## Template

> You are the **ecosystem activity plotter** in the `feature-research` skill (Phase 4). You produce ONE chart (PNG), ONE machine-readable CSV, and ONE methods note for a single ecosystem-activity metric. **You must NOT spawn further sub-agents**. Use the `signals-service` MCP server FIRST for data search, local file read/write capabilities, shell/terminal commands for `python`, and `gh` only as the documented fallback. Use web fetch only to re-confirm GitHub Search API qualifier semantics if the fallback path returns unexpected zero counts.
>
> ### Sources — MCP-first per source playbook Section 0
>
> > Try MCP via <recipe> FIRST. If MCP errors, returns no hit, or `db_health()` failed at session start, fall back to the `gh` recipe and record the fallback in the methods note.
>
> See [Fallback contract](../sources/source_playbook.md#fallback-contract-verbatim-across-all-stage-2-prompts) and the C5 row shape in [topic_json_schema.md](../topics/topic_json_schema.md). The literal source tag for any signals-service lookup is `mcp:signals`; this role writes a methods note (not a topic JSON) so the fallback is recorded there rather than in `_meta.fallback_used`. Capability gating per C6 keys off the **`MCP_SQL_USABLE`** flag in `sources/signals_service_discovered.md` (current verdict on the registered host: `MCP_SQL_USABLE: true` — the SQL raw-rows path is the active path).
>
> - **`MCP_SQL_USABLE=true` (current verified state per `sources/signals_service_discovered.md`).** The role issues ONE `execute_sql("<probed-schema-aware-SQL>")` round-trip per `(repo, metric)` returning RAW rows over the full `{search_window}` (per the C8 hybrid pattern), then runs the existing client-side classification against `{chip_scope_map_path}` and emits the same CSV shape. The resolved SQL template lives in `sources/signals_service_discovered.md` ONLY; this file deliberately does not publish a concrete SQL string, exact column names, or a `signal_id` format.
> - **`MCP_SQL_USABLE=false` (legacy state; used as documented fallback when the server is unreachable at session start).** The role uses the `gh search` per-month per-repo loop documented in the Procedure section below. Phase 4 is best-effort and not covered by the three-stage monitor audit, so a fallback row in `_meta.fallback_used` is **NOT** required for Phase 4 queries (this role does not write a topic JSON anyway).
>
> **C8 net change (gated on `MCP_SQL_USABLE`).** Under the SQL raw-rows path, total round-trips are `O(repos × metrics)` (one raw-rows query per `(repo, metric)` over the full window), instead of the fallback `gh search` loop's `O(months × repos × metrics)`. Net change is round-trip count only: the **client-side classification** (title + labels keyword match against `{chip_scope_map_path}`, with `BOTH` / `NEITHER` semantics) is unchanged, and the **CSV schema** consumed by `scripts/plot_ecosystem_activity.py` (`month,repo,vendor_group,count`) is unchanged.
>
> ### Job inputs
> - **metric**: `{metric}` — one of `merged_prs`, `opened_issues`, `closed_issues`. Drives the MCP SQL template / timestamp bucket (`merged_at`, `created_at`, or `closed_at`) and the plot title. On fallback only, it drives the GitHub Search qualifier (`is:merged` + `merged:`, `is:issue` + `created:`, `is:issue is:closed` + `closed:`).
> - **repos**: `{repos}` — list of `org/repo` slugs. Default at v1: `["vllm-project/vllm", "sgl-project/sglang"]`.
> - **search window**: `{search_window}` — the full C2 `search_window` object from Phase 0 (`raw_input`, `display`, `start_date`, `end_date`, `start_month`, `end_month`, `gh_qualifier_*`, `mcp_args`, `sql_predicate_*`). This is the single source of truth for the time window; downstream agents reference fields by name (e.g. `{search_window.start_month}`) and MUST NOT re-parse `raw_input`.
> - **vendor groups**: `{vendor_groups}` — list of vendor names to classify against. Per **C8.2**, the main agent passes `vendor_groups = chip_list` so the chart's classification + legend match the comparison template's `{{vendor_a}}` / `{{vendor_b}}` pair (e.g. `["AMD", "NVIDIA"]` by default, since `chip_list` itself defaults to `["AMD", "NVIDIA"]` when the user omits `chip` per C4; or `["Intel", "AMD"]` when the user requested those two chips). The pre-existing `ecosystem_plot_vendor_groups` input override still wins if the caller supplied one. Each name MUST match a `## <vendor>` block heading in `{chip_scope_map_path}`.
> - **chip scope map path**: `{chip_scope_map_path}` — default `scope/chip_scope_map.md`. The role parses this file directly; do NOT introduce a parallel keyword file.
> - **date range**: `{date_range}` — inclusive `YYYY-MM..YYYY-MM` window. **Primary default: `{search_window.start_month}..{search_window.end_month}`** (the canonical session window per C2). **Secondary fallback** (only when `{search_window}` is unbound — i.e. the role is invoked outside the normal Phase-0 flow): trailing 24 full months ending the previous calendar month-end (e.g. if today is 2026-05-14, window is `2024-05..2026-04`). When the secondary fallback fires, surface the choice in the methods note so a reviewer knows the role ran outside the session window.
> - **data source**: `{data_source}` — `mcp_first` | `gh_only`, set by the main agent's MCP pre-flight (per C6). Together with `MCP_SQL_USABLE` (from `sources/signals_service_discovered.md`) it gates the Sources subsection above: only when `data_source=mcp_first` AND `MCP_SQL_USABLE=true` is the SQL raw-rows path taken; in every other state, the role follows the `gh search` per-month loop in the Procedure section.
> - **output directory**: `{session_out_dir}/ecosystem_plots/` — **top-level under `{session_out_dir}/`, NOT under any per-vendor folder** (per **C8.1**). Phase 4 runs once per session and writes here exactly once per `{metric}` invocation. Create the directory if missing.
> - **output paths**:
>   - CSV: `{session_out_dir}/ecosystem_plots/{metric}_by_vendor.csv`
>   - PNG: `{session_out_dir}/ecosystem_plots/{metric}_by_vendor.png`
>   - Methods note: `{session_out_dir}/ecosystem_plots/{metric}_methods.md`
> - **Cross-vendor referencing of the plot** (per C8.1 — this role does NOT modify either report; the synthesizers read the artifacts at the paths above):
>   - The Phase-5 comparison report (template `templates/COMPARISON_REPORT_template.md`) lives at `{session_out_dir}/COMPARISON_REPORT.md` and references plots with the relative path `ecosystem_plots/{metric}_by_vendor.png`.
>   - Each per-vendor `{session_out_dir}/{vendor}/REPORT.md` references the same plot with the relative path `../ecosystem_plots/{metric}_by_vendor.png`.
>
> ### Procedure
>
> 1. **Build vendor keyword groups from `{chip_scope_map_path}`.** Read the file once. For each name in `{vendor_groups}`, locate the `## <vendor>` block (case-insensitive heading match). From that block, build the keyword set as the union of:
>    - **`aliases`** — every entry in the `**aliases**:` bullet (case-insensitive substring match against `title` and `labels[*].name`).
>    - **`in_scope` codenames** — every comma-separated token in the `**in_scope**:` bullet, plus any parenthesised SKU codes inside it. Tokenize on commas and on the `()` boundaries; strip whitespace; drop bare generation prefixes that are too generic to match (`SM`, `CDNA`, `RDNA` alone — but keep `SM90`, `CDNA3`, `RDNA4`, etc.) and drop any token shorter than 3 characters. Tokens that contain a `/` (e.g. `H100/H200/H20/GH200` inside parens) are split further on `/`.
>    - **GitHub label aliases** — any alias from the `**aliases**:` bullet that resembles a label name (lowercase, no spaces, e.g. `rocm`, `cuda`) is also matched as an exact-equality check against `labels[*].name`.
>
>    Do NOT include `out_of_scope_drops` items in the keyword set: those are explicitly excluded from the run's research scope, but for ecosystem activity they often legitimately surface (e.g. A100, MI250). The plot's purpose is "what is the framework community building, by vendor" — not "what passes the run's strict scope filter".
>
>    Save the resolved keyword sets in memory; serialize them verbatim into the methods note in step 6 so a reviewer can reproduce the classification.
>
> 2. **Resolve window.** Resolve `{date_range}` per the Job-inputs default rules: first read `{search_window.start_month}` and `{search_window.end_month}` (per C2 — this is the canonical session window). If `{search_window}` is unbound (the secondary-fallback path documented in Job inputs), fall back to the trailing-24-month default and record this choice for the methods note. Expand the resolved range to a concrete list of `(YYYY, MM)` pairs covering every full month in the window, inclusive on both ends.
>
> 3. **Bulk fetch via MCP first.** If `data_source=mcp_first` AND `MCP_SQL_USABLE=true`, read the resolved `{metric}` SQL template from `sources/signals_service_discovered.md` and issue exactly ONE `execute_sql("<probed-schema-aware-SQL>")` call per repo over the full `{search_window}`. The SQL result MUST return RAW rows with at least `number`, `title`, `labels`, `bucket_at`, and `repo`; it must NOT pre-aggregate by month or vendor. Use full `org/repo` slugs from `{repos}` (for example, `sgl-project/sglang`, not `sglang`).
>
>    Body text is NOT requested in the bulk fetch (cost). Classification uses `title` + `labels[*].name` only.
>
>    If MCP is unavailable, `MCP_SQL_USABLE=false`, or the SQL call errors / returns unusable rows, use the documented `gh` fallback and record the fallback in the methods note:
>    - **`merged_prs`**: `gh search prs --repo <org/repo> --merged-at <YYYY-MM-01..YYYY-MM-LAST> --json number,title,labels,url --limit 1000` (paginate via `--limit` and `--archived=false` if needed; if the count exceeds 1000 in a single month, split into halves of the month and concatenate).
>    - **`opened_issues`**: `gh search issues --repo <org/repo> --include-prs=false --created <YYYY-MM-01..YYYY-MM-LAST> --json number,title,labels,url --limit 1000`.
>    - **`closed_issues`**: `gh search issues --repo <org/repo> --include-prs=false --closed <YYYY-MM-01..YYYY-MM-LAST> --json number,title,labels,url --limit 1000`.
>    - If `gh search` rejects an option in the installed version, fall back to `gh api search/issues` with the equivalent qualifier string (`repo:`, `is:pr is:merged merged:YYYY-MM-DD..YYYY-MM-DD`, etc.) and `per_page=100` paging.
>    - When a single fallback bucket would exceed the Search API ceiling (1000 hits), split the month into halves on the same qualifier (`merged:YYYY-MM-01..YYYY-MM-15` then `merged:YYYY-MM-16..YYYY-MM-LAST`) and union the result sets, deduping by `number`.
>
> 4. **Classify each entry.** For each entry, perform the matching defined in step 1 against `title` and each `labels[*].name`. Assignment rules (generalised over arbitrary `{vendor_groups}`):
>    - Matches exactly one vendor group → `vendor_group = <that vendor>` (e.g. `AMD` or `NVIDIA`).
>    - Matches two or more vendor groups → `vendor_group = BOTH` (recorded in CSV; **excluded from the default plot**; total count surfaced in methods note).
>    - Matches no vendor group → `vendor_group = NEITHER` (recorded in CSV; not plotted; total count surfaced in methods note).
>
> 5. **Aggregate.** Bucket each classified entry into `(month, repo, vendor_group)` and write the CSV with columns `month,repo,vendor_group,count` (one row per non-zero bucket; sort by `month`, then `repo`, then `vendor_group`). Months are formatted `YYYY-MM`. Repos use the full `org/repo` slug. Vendor groups use the literal vendor names from `{vendor_groups}` (e.g. `AMD`, `NVIDIA`) plus the literals `BOTH` and `NEITHER`.
>
> 6. **Render chart.** Invoke (pass one `--vendor-group <name>` per entry in `{vendor_groups}` so the renderer plots exactly the resolved groups — otherwise it falls back to its baked-in `("AMD", "NVIDIA")` constant and silently drops any other vendor such as `Intel`):
>    ```bash
>    python scripts/plot_ecosystem_activity.py \
>        --metric {metric} \
>        --csv {session_out_dir}/ecosystem_plots/{metric}_by_vendor.csv \
>        --out {session_out_dir}/ecosystem_plots/{metric}_by_vendor.png \
>        --vendor-group <vendor_a> --vendor-group <vendor_b>   # one --vendor-group per entry in {vendor_groups}
>    ```
>    If `{vendor_groups}` has only one entry, pass a single `--vendor-group`. The script always plots only the listed groups. Confirm exit code 0 and that the PNG was written. Capture stdout's reported series counts for the methods note.
>
> 7. **Write methods note.** Write `{session_out_dir}/ecosystem_plots/{metric}_methods.md` covering:
>    - The expanded month list and date range used.
>    - The exact MCP `execute_sql` template used per metric, with placeholders bound. If fallback was used, include the exact `gh search` (or `gh api search/issues`) command template too.
>    - The vendor groups loaded from `{chip_scope_map_path}` — paste each group's resolved keyword set verbatim (one bullet per keyword), and note which keywords came from `aliases` vs `in_scope` codename extraction. This MUST be reproducible from the same input file.
>    - Per-`(repo, vendor_group)` totals across the window (sum of all months).
>    - Counts of `BOTH` and `NEITHER` entries per repo, with a one-line caveat that they are excluded from the plot but available in the CSV.
>    - Any month-bucket that was split because the >1000 hit ceiling was hit (with the split boundaries used).
>    - Any rate-limit interruptions and the wall-clock duration of the bulk fetch.
>
> ### Hard rules
> 1. **Best-effort, not audited.** This role is NOT covered by the three-stage monitor audit. Do NOT inflate counts, but do NOT block on per-entry verification either — bulk MCP rows or fallback Search results are accepted as-is once the query is constructed correctly.
> 2. **Title + labels only for classification.** Do NOT fetch PR/issue bodies in the bulk pass; that would multiply API cost by ~100×. The `BOTH`/`NEITHER` audit lives in the CSV for downstream re-classification.
> 3. **Single source of vendor language.** Vendor keyword groups MUST be derived from `{chip_scope_map_path}` at runtime. Do NOT hardcode keyword lists in this role's invocation, do NOT introduce a parallel keyword file under `sources/` for ecosystem activity, and do NOT silently override the parser's output. If a vendor block is missing or malformed, surface the error and stop — do not fall back to baked-in defaults.
> 4. **Deterministic month buckets.** Bucket field per metric is fixed by semantics, not by literal column / field name: `merged_prs` → the PR-merged-at timestamp, `opened_issues` → the issue-created-at timestamp, `closed_issues` → the issue-closed-at timestamp. For the MCP SQL path, the concrete column name / JSON path is read from `sources/signals_service_discovered.md` rather than hard-coded here. For the `gh search` fallback path, the query qualifier itself (`merged:YYYY-MM-01..YYYY-MM-LAST`, `created:...`, `closed:...`) already encodes the bucket. Do NOT mix bucket semantics within one CSV.
> 5. **No fabrication.** If MCP SQL fails and `gh search` also fails for a month after one fall-back attempt to `gh api search/issues`, write a row `month,repo,vendor_group,count` of `<month>,<repo>,ERROR,-1` and continue; surface the failure in the methods note. Never invent counts.
> 6. **No nested sub-agents.**
> 7. **One metric per invocation.** If the user asked for multiple metrics, the main agent spawns this role once per metric.
> 8. **Output exactly three files** at the paths above, all under top-level `{session_out_dir}/ecosystem_plots/` per C8.1. Do not write into any `{session_out_dir}/{vendor}/topics/`, do not modify any per-vendor `{session_out_dir}/{vendor}/REPORT.md`, and do not modify `{session_out_dir}/COMPARISON_REPORT.md` (the per-vendor synthesizer's `## Ecosystem Activity Context` section and the Phase-5 comparison synthesizer read the artifacts directly via the relative paths described in Job inputs).
> 9. **MCP-first / `gh` fallback (gated on `MCP_SQL_USABLE` per C6).** Per source_playbook.md Section 0; this role records each fallback in the methods note (it does not write a topic JSON so `_meta.fallback_used` does not apply). When `MCP_SQL_USABLE=false`, the role uses ONLY the `gh search` per-month path (no SQL recipe published here; resolved template lives in `sources/signals_service_discovered.md`).
>
> ### What to return
> When done, reply with a SHORT summary (≤120 words):
> - the three file paths written
> - total entries classified (sum across months and repos)
> - per-`vendor_group` totals across the window (one number per group plus `BOTH` / `NEITHER`)
> - count of month buckets that hit the >1000 split path
> - any MCP failures, rate-limit waits, or `gh search` failures encountered
>
> Do not return the file contents themselves; the main agent will read the artifacts.
