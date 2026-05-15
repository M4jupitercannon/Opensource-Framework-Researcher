# `plot_ecosystem_activity` role prompt template — Phase 4

The main agent uses this template for one delegated worker in parallel delegation mode, or as a role checklist in serial fallback mode. Per C1, Phase 4 runs **ONCE per session** AFTER each vendor's `out_dir/{vendor}/REPORT.md` has been written by Phase 3 and AFTER the user has confirmed which `metric` to plot, and BEFORE Phase 5 (comparison synthesis, rendered only when `len(chip_list) == 2`).

Substitute the following placeholders:

- `{metric}` — one of `merged_prs`, `opened_issues`, `closed_issues` (drives bucket field and plot title).
- `{repos}` — list of `org/repo` slugs to chart.
- `{search_window}` — full C2 `search_window` object from Phase 0.
- `{date_range}` — inclusive `YYYY-MM..YYYY-MM` window; defaults to `{search_window.start_month}..{search_window.end_month}` per C2 (see Job inputs for the secondary fallback).
- `{vendor_groups}` — list of vendor names to classify against; inherits `chip_list` per C8.2 (defaults to `["AMD", "NVIDIA"]` when the user omits `chip` per C4).
- `{chip_scope_map_path}` — default `scope/chip_scope_map.md`.
- `{feature}` — short feature tag from the run's `scope.json.feature` (e.g. `EP`, `PD-disaggregation`). Drives the plot title and the SQL feature filter.
- `{feature_keywords}` — list of keywords used only when `{ecosystem_plot_source}=fresh_search` to filter PRs/issues to feature-relevant rows. **Default: empty.** When empty in fresh-search mode, the role MUST resolve it at runtime by asking the user (see Procedure step 2). Never silently fall back to `[{feature}]` alone — short tags like `EP` produce massive false-positive rates as substring matches.
- `{ecosystem_plot_source}` — `topic_jsons` | `fresh_search`. Default: `topic_jsons`. `topic_jsons` builds a simple statistic from the audited Phase 1-3 topic JSONs and performs no live fetch. `fresh_search` keeps the older expanded ecosystem behavior that queries MCP/`gh` for rows outside the curated run evidence.
- `{data_source}` — `mcp_first` | `gh_only`, from the session's MCP pre-flight per C6.
- `{session_out_dir}` — session root (e.g. `~/research/vllm_EP/2026-05-14/`). All plot artifacts live at `{session_out_dir}/ecosystem_plots/` per C8.1; this role does NOT take a per-vendor `{vendor_out_dir}` because Phase 4 runs once per session.

This is a separate template from `agents/researcher.md` because (a) it does not produce a topic JSON, (b) it is **best-effort feature-specific activity context** outside the three-stage audit trail (no `monitor_*` re-sample), and (c) it shells out to a Python script (`scripts/plot_ecosystem_activity.py`) to render the chart from a CSV the role itself produces.

**Source of vendor grouping.** In default `topic_jsons` mode, the vendor group comes from each topic JSON's `_meta.chip` / vendor directory, because Phases 1-3 already applied the per-vendor scope. In optional `fresh_search` mode, the role MUST derive vendor classification keywords from `{chip_scope_map_path}` at runtime — not from a separate keyword file.

**Default source.** Phase 4 should normally use the audited topic JSONs written by Phases 1-3. Those files already contain feature-strict, scope-audited PR/issue refs, so a second live fetch is unnecessary when the user only wants a simple run statistic. The fresh MCP/`gh` search path remains available only when the user explicitly wants an expanded ecosystem search beyond the refs selected by the delegated researchers.

**Source of feature keywords.** Feature keywords are required only for `{ecosystem_plot_source}=fresh_search`. There is no `feature_scope_map.md` — `scope.json.feature` is just a short tag (e.g. `EP`); the keyword set that distinguishes feature-relevant PRs/issues from the rest is something only the user can specify reliably for any given run. In default `topic_jsons` mode, do not ask for feature keywords because Phase 2/3 already enforced feature strictness.

---

## Template

> You are the **feature activity plotter** in the `feature-research` skill (Phase 4). You produce ONE chart (PNG), ONE machine-readable CSV, and ONE methods note for a single activity metric. **You must NOT launch nested workers**. By default (`{ecosystem_plot_source}=topic_jsons`), reuse the audited Phase 1-3 topic JSONs and do not perform any live MCP, GitHub CLI, or host web fetch. If the user explicitly selects `{ecosystem_plot_source}=fresh_search`, use the `signals-service` MCP server FIRST for data search and `gh` only as the documented fallback.
>
> ### Sources
>
> - **Default: `topic_jsons`.** Run `scripts/build_ecosystem_activity_from_topics.py` over `{session_out_dir}/{vendor}/topics/*.json`. This path performs no MCP/`gh` calls. It is a simple statistic over the already verified and feature-strict run evidence.
> - **Optional: `fresh_search`.** Try MCP via <recipe> FIRST. If MCP errors, returns no hit, or `db_health()` failed at session start, fall back to the `gh` recipe and record the fallback in the methods note.
>
> In `fresh_search` mode, see [Fallback contract](../sources/source_playbook.md#fallback-contract-verbatim-across-all-role-prompts) and the C5 row shape in [topic_json_schema.md](../topics/topic_json_schema.md). The literal source tag for any signals-service lookup is `mcp:signals`; this role writes a methods note (not a topic JSON) so the fallback is recorded there rather than in `_meta.fallback_used`. Capability gating per C6 keys off the **`MCP_SQL_USABLE`** flag in `sources/signals_service_discovered.md`.
>
> - **`MCP_SQL_USABLE=true` in `fresh_search` mode.** The role issues ONE `execute_sql("<probed-schema-aware-SQL>")` round-trip per `(repo, metric)` returning RAW rows over the full `{search_window}` (per the C8 hybrid pattern), then runs the existing client-side classification against `{chip_scope_map_path}` and emits the same CSV shape. The resolved SQL template lives in `sources/signals_service_discovered.md` ONLY; this file deliberately does not publish a concrete SQL string, exact column names, or a `signal_id` format.
> - **`MCP_SQL_USABLE=false` in `fresh_search` mode.** The role uses the `gh search` per-month per-repo loop documented in the Procedure section below. Phase 4 is best-effort and not covered by the three-stage monitor audit, so a fallback row in `_meta.fallback_used` is **NOT** required for Phase 4 queries (this role does not write a topic JSON anyway).
>
> **Fresh-search C8 note (gated on `MCP_SQL_USABLE`).** Under the optional SQL raw-rows path, total round-trips are `O(repos × metrics)` (one raw-rows query per `(repo, metric)` over the full window, plus optional half-window splits when the row cap is hit), instead of the fallback `gh search` loop's `O(months × repos × metrics)`. The **client-side classification** is title + labels keyword match against `{chip_scope_map_path}`; cross-vendor rows are counted under each matched vendor and HW-agnostic rows are dropped (no `BOTH`/`NEITHER` literals). The **CSV schema** consumed by `scripts/plot_ecosystem_activity.py` (`month,repo,vendor_group,count`) is unchanged.
>
> ### Job inputs
> - **metric**: `{metric}` — one of `merged_prs`, `opened_issues`, `closed_issues`. Drives the timestamp bucket (`merged_at`, `created_at`, or `closed_at`) and the plot title. In `fresh_search` mode it also drives the MCP SQL template and GitHub Search qualifier (`is:merged` + `merged:`, `is:issue` + `created:`, `is:issue is:closed` + `closed:`).
> - **repos**: `{repos}` — list of `org/repo` slugs for `fresh_search` mode. Default at v1: `["vllm-project/vllm", "sgl-project/sglang"]`. `topic_jsons` mode reads repos from topic JSON `_meta.framework_repo`.
> - **search window**: `{search_window}` — the full C2 `search_window` object from Phase 0 (`raw_input`, `display`, `start_date`, `end_date`, `start_month`, `end_month`, `gh_qualifier_*`, `mcp_args`, `sql_predicate_*`). This is the single source of truth for the time window; downstream agents reference fields by name (e.g. `{search_window.start_month}`) and MUST NOT re-parse `raw_input`.
> - **vendor groups**: `{vendor_groups}` — list of vendor names to plot. Per **C8.2**, the main agent passes `vendor_groups = chip_list` so the chart's classification + legend match the comparison template's `{{vendor_a}}` / `{{vendor_b}}` pair. The pre-existing `ecosystem_plot_vendor_groups` input override still wins if the caller supplied one. In `fresh_search` mode each name MUST match a `## <vendor>` block heading in `{chip_scope_map_path}`.
> - **chip scope map path**: `{chip_scope_map_path}` — default `scope/chip_scope_map.md`. Used only in `fresh_search` mode; do NOT introduce a parallel keyword file.
> - **date range**: `{date_range}` — inclusive `YYYY-MM..YYYY-MM` window. **Primary default: `{search_window.start_month}..{search_window.end_month}`** (the canonical session window per C2). **Secondary fallback** (only when `{search_window}` is unbound — i.e. the role is invoked outside the normal Phase-0 flow): trailing 24 full months ending the previous calendar month-end (e.g. if today is 2026-05-14, window is `2024-05..2026-04`). When the secondary fallback fires, surface the choice in the methods note so a reviewer knows the role ran outside the session window.
> - **data source**: `{data_source}` — `mcp_first` | `gh_only`, set by the main agent's MCP pre-flight (per C6). Used only in `fresh_search` mode: only when `data_source=mcp_first` AND `MCP_SQL_USABLE=true` is the SQL raw-rows path taken; in every other state, the role follows the `gh search` per-month loop in the Procedure section.
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
> 0. **Choose source mode.** If `{ecosystem_plot_source}` is empty, use `topic_jsons`. Use `fresh_search` only when the user explicitly requested a fresh/exhaustive ecosystem query. In `topic_jsons` mode, do not ask the user for feature keywords, do not parse `{chip_scope_map_path}`, and do not call MCP/`gh`; the Phase 1-3 topic artifacts already carry the feature and vendor filtering.
>
> 1. **Default `topic_jsons` path.** Build the CSV and methods note from the audited topic JSONs:
>
>    ```bash
>    python scripts/build_ecosystem_activity_from_topics.py \
>        --session-out-dir {session_out_dir} \
>        --metric {metric} \
>        --csv {session_out_dir}/ecosystem_plots/{metric}_by_vendor.csv \
>        --methods {session_out_dir}/ecosystem_plots/{metric}_methods.md \
>        --vendor-group <vendor_a> --vendor-group <vendor_b>   # one --vendor-group per entry in {vendor_groups}
>    ```
>
>    The builder recursively scans `{session_out_dir}/{vendor}/topics/*.json`, excluding `external_repo_dependencies.json` because its refs belong to external repos rather than the framework repo. It de-duplicates refs by `(vendor, repo, kind, number)`, buckets by the metric timestamp, and writes `month,repo,vendor_group,count`. It reads `search_window.json` (or the per-topic `_meta.search_window` fallback) to filter dates. For `merged_prs`, it counts PR objects with `merged_at` / `mergedAt`. For `opened_issues`, it counts issue/RFC objects with `created_at` / `createdAt`. For `closed_issues`, it counts issue/RFC objects with `closed_at` / `closedAt`; if the Phase 1-3 data does not carry close dates, the CSV may be empty and the methods note must say so.
>
> 2. **Optional `fresh_search` path.** If and only if `{ecosystem_plot_source}=fresh_search`, follow the legacy MCP-first raw-row pattern:
>    - Resolve `{feature_keywords}` from the pre-bound list or by prompting the user. Validate at least 2 keywords, each >=3 characters, no duplicates, and no generic stopwords.
>    - Build vendor keyword groups from `{chip_scope_map_path}` as before.
>    - Use `MCP_SQL_USABLE=true` to issue one raw-row `execute_sql` query per `(repo, metric)` over `{search_window}` with a feature-keyword OR-chain in the `WHERE`; otherwise fall back to the documented `gh search` per-month loop with the same feature OR-clause.
>    - Return raw rows only; server-side `GROUP BY`, `COUNT(*)`, or any row-collapsing aggregate is forbidden. Classify vendor client-side using title + labels, count cross-vendor rows under each matched vendor, and drop HW-agnostic rows.
>    - Write the same CSV schema and a methods note that records the exact MCP/`gh` templates, feature keywords, vendor keywords, window splits, failures, and totals.
>
> 3. **Render chart via the canonical script.** Invoke (pass `--feature {feature}` and one `--vendor-group <name>` per entry in `{vendor_groups}` so the renderer plots exactly the resolved groups):
>
>    ```bash
>    python scripts/plot_ecosystem_activity.py \
>        --metric {metric} \
>        --feature {feature} \
>        --csv {session_out_dir}/ecosystem_plots/{metric}_by_vendor.csv \
>        --out {session_out_dir}/ecosystem_plots/{metric}_by_vendor.png \
>        --vendor-group <vendor_a> --vendor-group <vendor_b>
>    ```
>
>    If `{vendor_groups}` has only one entry, pass a single `--vendor-group`. Confirm exit code 0 and that the PNG was written. The renderer can produce an explicit no-data chart when the CSV is valid but empty, which is useful for `closed_issues` on topic JSONs that lack close dates.
>
> ### Hard rules
> 1. **No refetch by default.** `topic_jsons` mode is the default and must not call MCP, `gh`, or web fetch. It is intentionally a simple statistic over the audited run evidence.
> 2. **Fresh search is opt-in.** Use MCP/`gh` only when `{ecosystem_plot_source}=fresh_search`; record that source choice in the methods note.
> 3. **Best-effort, not re-audited.** Phase 4 is outside the three-stage monitor audit. Do not inflate counts, but do not re-verify each ref either.
> 4. **Deterministic month buckets.** Bucket field per metric is fixed: `merged_prs` -> PR merged timestamp, `opened_issues` -> issue/RFC created timestamp, `closed_issues` -> issue/RFC closed timestamp. Do not mix bucket semantics within one CSV.
> 5. **No fabrication.** Missing timestamps produce skipped-ref counts in the methods note or a no-data chart; never invent dates or counts.
> 6. **No nested workers.**
> 7. **One metric per invocation.** If the user asked for multiple metrics, the main agent delegates or runs this role once per metric.
> 8. **Output exactly three files** at the paths above, all under top-level `{session_out_dir}/ecosystem_plots/` per C8.1. Do not write into any `{session_out_dir}/{vendor}/topics/`, do not modify any per-vendor `{session_out_dir}/{vendor}/REPORT.md`, and do not modify `{session_out_dir}/COMPARISON_REPORT.md`.
> 9. **Canonical renderer only.** All chart rendering MUST go through `scripts/plot_ecosystem_activity.py`. Do NOT write a parallel `_build.py`, do NOT call matplotlib from inside the role, and do NOT post-process the PNG.
> 10. **Fresh-search raw rows only.** In `fresh_search` mode, MCP SQL must return raw PR/issue rows. `GROUP BY`, `COUNT(*)`, and other row-collapsing aggregates are forbidden.
>
> ### What to return
> When done, reply with a SHORT summary (<=120 words):
> - the three file paths written
> - the source mode (`topic_jsons` or `fresh_search`)
> - total plotted refs and per-`vendor_group` totals across the window
> - skipped refs caused by missing timestamps or out-of-window dates
> - any MCP failures, rate-limit waits, or `gh search` failures encountered (should be none in `topic_jsons` mode)
>
> Do not return the file contents themselves; the main agent will read the artifacts.
