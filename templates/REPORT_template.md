# Synthesized REPORT.md template

The main agent renders this skeleton with substituted values from `scope.json` + the per-topic JSONs + all three verification files: `verification_existence.md` (Stage 1), `verification_scope.md` (Stage 2), `verification_feature.md` (Stage 3). Section headings come from `_meta.report_heading` of each topic file (NEVER `Q1`/`Q2`/etc).

Placeholders use `{{double-brace}}`. Any `[loop ...]` block is rendered once per topic (in the order topics were spawned).

---

```markdown
# {{framework}} {{feature}} on {{chip}} — Highlighted Report

**Generated:** {{date}} · **Window:** {{search_window.display}} · **Vendor:** {{vendor}} · **Scope:** {{scope_statement}}

**Verification (three-stage):** **Stage 1** (`monitor_existence`) independently re-checked ≥80 % of PRs and ≥90 % of issues exist on `{{framework_repo}}` and that every verbatim source quote matches its source — verdict **{{existence_verdict}}**. **Stage 2** (`monitor_scope`) audited each surviving entry's hardware against the chip-vendor scope — verdict **{{scope_verdict}}**. **Stage 3** (`monitor_feature`) audited each surviving entry for `{{feature}}`-strictness (must directly influence `{{feature}}`'s functionality or performance) — verdict **{{feature_verdict}}**. {{verdict_summary_line}}

---

## At-a-Glance Dashboard

| Topic | Headline metric | Key insight |
|---|---:|---|
[loop topic in topics]
| **{{topic.report_heading}}** | {{topic.headline_metric}} | {{topic.headline_insight}} |
[/loop]

---

[loop topic in topics]
## {{topic.report_heading}}

{{topic.intro_paragraph}}

{{topic.primary_table}}

{{topic.secondary_notes_optional}}

---

[/loop]

[render_if_present ecosystem_plots]
## Feature Activity Context

This section shows monthly activity in the listed framework repos that mentions the run's feature `{{feature}}` AND a target vendor (one line per `(repo, vendor)`). Vendor classification is derived from `scope/chip_scope_map.md` at runtime; the feature-keyword filter comes from the user prompt at Phase 4 time. See each `*_methods.md` for the exact data-fetch query and both resolved keyword sets. This section is best-effort context — it is NOT covered by the three-stage monitor audit.

[loop plot in ecosystem_plots]
![{{plot.title}}]({{plot.png_relpath}})

Window: {{plot.window}}. Repos: {{plot.repos_summary}}. Feature: `{{plot.feature}}`. Vendor groups: {{plot.vendor_groups_summary}}. Source: `{{plot.source_tag}}` (see [`{{plot.methods_relpath}}`]({{plot.methods_relpath}})). CSV: [`{{plot.csv_relpath}}`]({{plot.csv_relpath}}).

[/loop]

---

[/render_if_present]

## Verification Footer

**Stage-1 (existence) verdict:** {{existence_verdict}} — full detail in [`verification_existence.md`](./verification_existence.md).
**Stage-2 (chip-vendor scope) verdict:** {{scope_verdict}} — full detail in [`verification_scope.md`](./verification_scope.md).
**Stage-3 (`{{feature}}`-strictness) verdict:** {{feature_verdict}} — full detail in [`verification_feature.md`](./verification_feature.md).

**Stage-1 — Verbatim-quote drift corrected:**
[loop fix in verbatim_quote_fixes]
- {{fix.field}} on {{fix.ref}} — replaced "{{fix.was}}" with "{{fix.now}}"
[/loop]

**Stage-1 — Internal-consistency conflicts reconciled:**
[loop conflict in internal_conflicts]
- {{conflict.ref}} — {{conflict.summary}}
[/loop]

**Stage-2 — Dropped (out-of-scope hardware):**
[loop drop in dropped_out_of_scope]
- {{drop.ref}} — {{drop.reason}}
[/loop]

**Stage-2 — Scope-mixing entries narrowed:**
[loop nit in scope_mixing_narrowed]
- {{nit.ref}} — kept as {{nit.kept_as}}, dropped mention of {{nit.dropped_mention}}
[/loop]

**Stage-2 — Scope-ambiguity entries annotated:**
[loop nit in scope_ambiguity_annotated]
- {{nit.ref}} — family cited: {{nit.family}}; in-scope members: {{nit.in_scope_members}}
[/loop]

**Stage-3 — Removed for failing `{{feature}}`-strictness:**
[loop drop in removed_by_strictness_audit]
- {{drop.ref}} (was in {{drop.original_bucket}}) — {{drop.reason}}
[/loop]

**Stage-3 — Recategorized (entry primary purpose was a different topic):**
[loop r in recategorized_as_other]
- {{r.ref}} — moved from {{r.original_bucket}} to {{r.target_bucket}} ({{r.reason}})
[/loop]

**Stage-3 — Cross-listed entries deduped to canonical bucket:**
[loop d in dedup_canonical]
- {{d.ref}} — kept under {{d.canonical_bucket}}; removed from {{d.also_listed_under_dropped}}
[/loop]

**Fallback usage (mcp:signals → gh):** {{fallback_count}} of {{ref_total}} refs fell back from `mcp:signals` to `gh`.

**Sources used:** {{sources_summary}}

**Dashboard-ready inputs:**
- `topics/*.json` — one machine-readable file per topic, stable schema (see `topic_json_schema.md`); every removed/recategorized item is preserved in `_meta.{dropped_out_of_scope, removed_by_strictness_audit, recategorized_as_other, dedup_canonical}` for full reversibility
- `scope.json` — chip + framework + scope spec used for this run
- `verification_existence.md` — Stage-1 audit trail (PR/issue/URL existence + verbatim-quote integrity)
- `verification_scope.md` — Stage-2 audit trail (chip-vendor scope strictness)
- `verification_feature.md` — Stage-3 audit trail (`{{feature}}`-strictness)
```

---

## Rendering rules

- `topic.headline_metric` is derived per topic:
  - `completed_subfeatures` → `{N} subfeatures, {M} merged PRs` — quantities defined as:
    - **{N}** — `len(entries)` from `completed_subfeatures.json` (count of subfeatures).
    - **{M}** — `sum(len(entries[*].prs))` from `completed_subfeatures.json` (total merged PRs across all subfeatures).
  - `open_issues` → `{N} open ({direct} direct + {tangential} tangential)` — quantities defined as:
    - **{N}** — `sum(entries[*].open_count)` from `open_issues.json` (total open issues across all subfeature buckets; canonical per the schema — `len(entries[*].issues)` should be equal but `open_count` is authoritative).
    - **{direct}** — `sum(entries[*].direct_count)` from `open_issues.json`.
    - **{tangential}** — `sum(entries[*].tangential_count)` from `open_issues.json`.
  - `roadmap` → `{N} items ({in_flight} in-flight · {planned} planned · {stretch} stretch)` — quantities defined as:
    - **{N}** — `len(roadmap_items)` from `roadmap.json` (count of roadmap items; does NOT include `recent_rfcs`).
    - **{in_flight}** — count of `roadmap_items[*]` where the `category` field equals the literal string `"in-flight"` (see `topics/default_topics.md` §3 entry schema).
    - **{planned}** — count of `roadmap_items[*]` where the `category` field equals the literal string `"planned"`.
    - **{stretch}** — count of `roadmap_items[*]` where the `category` field equals the literal string `"stretch"`.
  - `perf_numbers` → `{N} verified perf numbers` — quantities defined as:
    - **{N}** — `len(entries)` from `perf_numbers.json` (count of verified perf-number entries).
  - `kernels_or_components` → `{N} kernels in {K} categories` — quantities defined as:
    - **{N}** — `sum(len(categories[*].kernels))` from `kernels_or_components.json` (total kernels across all categories).
    - **{K}** — `len(categories)` from `kernels_or_components.json` (count of kernel categories).
  - `external_repo_dependencies` → `{S} subfeatures touch {R} external repos · {P} {{framework}} PRs · {I} {{framework}} issues` — quantities defined as:
    - **{S}** — count of subfeatures with at least one external repo (i.e. `external_repos` non-empty).
    - **{R}** — count of distinct external repo slugs cited across all subfeatures.
    - **{P}** — the **sum of `len(prs)` from `completed_subfeatures.json`** across the {S} subfeatures (each subfeature counted once even if it touches multiple external repos).
    - **{I}** — the **sum of `open_count` from `open_issues.json`** across the open-issue buckets that map to those subfeatures by **verbatim subfeature-name match** (`open_issues.json` `entries[*].subfeature` MUST equal `completed_subfeatures.json` `entries[*].name` exactly — see `topics/default_topics.md` §2 subfeature-name rule). Each bucket is counted once even if it covers many subfeatures; the literal `"(cross-cutting)"` bucket is NOT counted in {I} and instead surfaces in the section's cross-cutting footer.

- `topic.primary_table` is a Markdown table optimized for dashboard ingestion (one row per entity). Per-topic table specs:
  - `completed_subfeatures` → columns: `# | Subfeature | Status | Hardware | Landmark PRs | First merged`
  - `open_issues` → columns: `Subfeature | Open direct | Open tangential | Total | Notable open issues`
  - `roadmap` → columns: `Item | Category | Linked PRs / RFCs | Priority`
  - `perf_numbers` → columns: `Subfeature | Metric | Baseline | Improved | Δ | Source`
  - `kernels_or_components` → one sub-table per category; columns: `Kernel | Library | PRs | Hardware | Notes`
  - `external_repo_dependencies` → columns: `External repo | # subfeatures | Subfeatures (short list) | {{framework}} PRs | {{framework}} issues` (one row per external repo, **aggregated across subfeatures**; sort by `# subfeatures` descending then by repo name; subfeature short-list cell uses `;`-separated short titles, truncate any single subfeature title to ≤40 chars). The `{{framework}} PRs` column is the **sum of `len(prs)` from `completed_subfeatures.json`** across the listed subfeatures (subfeature names match verbatim — the analyzer inherits names from `completed_subfeatures.json`). The `{{framework}} issues` column is the **sum of `open_count` from `open_issues.json`** across the open-issue buckets that map to the listed subfeatures by **verbatim subfeature-name match** (`open_issues.json` `entries[*].subfeature` MUST equal a `completed_subfeatures.json` `entries[*].name` exactly — see `topics/default_topics.md` §2 subfeature-name rule; the literal `"(cross-cutting)"` bucket is NOT attributed to any external repo). Append two footer lines below the table: (a) `Subfeatures with no external deps (N): name; name; name` (subfeature names absent from `external_repo_dependencies.json` `entries[*].subfeature`), and (b) `Cross-cutting open-issue buckets not attributed to any external repo (X issues): bucket(Y); bucket(Y); …` for buckets named `"(cross-cutting)"`. The per-(subfeature, repo) view is intentionally not rendered — the per-repo aggregation + zero-deps footer + cross-cutting footer fully cover the data.

- `topic.intro_paragraph` is one sentence noting source(s) used and any caveats (e.g. "13 perf numbers verified verbatim against PR bodies").

- `sources_summary` is the union of all `_meta.sources_used` arrays, deduplicated. **When emitting `sources_summary` in the header, collapse all `web_fetch:*` tags to a single `web_fetch`** (e.g. `web_fetch:docs.vllm.ai` and `web_fetch:developer.nvidia.com/blog` both become `web_fetch`). The full per-host list lives in the per-topic JSONs. Example summary: `gh, web_fetch, web_search, mlperf, inferencex`.

- **`verbatim_quote_fixes` data source.** This loop is NOT sourced from any `_meta.*` field — instead, parse the `### Verbatim-quote drift` table in `verification_existence.md`. Each table row produces one entry: `{field: <Field column>, ref: <File column> (and any inline ref), was: <Claimed quote column>, now: <Actual quote column>}`. If the table is absent or empty, render the loop as the literal line `- (none)`.

- **`internal_conflicts` data source.** Same pattern — parse the `### Internal-consistency conflicts` table in `verification_existence.md`. Each row produces `{ref: <Ref column>, summary: "<file A claim> vs <file B claim>; correct: <which is correct>"}`. If the table is absent or empty, render `- (none)`.

- **`scope_mixing_narrowed` data source.** Per-topic `_meta.scope_mixing_narrowed` arrays, written by the synthesizer when applying Stage 2 (`monitor_scope`) must-fixes. Concatenate across all topic files. Each entry has shape `{ref, kept_as, dropped_mention}`. If empty across all files, render `- (none)`.

- **`scope_ambiguity_annotated` data source.** Per-topic `_meta.scope_ambiguity_annotated` arrays, written by the synthesizer when applying Stage 2 (`monitor_scope`) must-fixes. Concatenate across all topic files. Each entry has shape `{ref, family, in_scope_members}`. If empty across all files, render `- (none)`.

- **`dropped_out_of_scope`, `removed_by_strictness_audit`, `recategorized_as_other`, `dedup_canonical` data sources.** Each is the concatenation of the same-named `_meta.*` array across all topic files. `dropped_out_of_scope` is written by the synthesizer when applying Stage 2 (`monitor_scope`) must-fixes; `removed_by_strictness_audit`, `recategorized_as_other`, and `dedup_canonical` are written when applying Stage 3 (`monitor_feature`) must-fixes. If empty across all files, render `- (none)`.

- **`{{vendor}}` and `{{search_window.display}}` substitutions (header line).** Both come from build-time / Phase-0 outputs:
  - `{{vendor}}` — the active per-vendor identifier for this `REPORT.md`. Sourced from the per-vendor `out_dir/{vendor}/scope.json` (`vendor` field, normalized to the canonical capitalization used in `chip_list`, e.g. `NVIDIA`, `AMD`, `Intel`, `Google`). Each per-vendor `REPORT.md` substitutes its OWN vendor name; the synthesized comparison report (`COMPARISON_REPORT.md`) instead uses `{{vendor_a}}` / `{{vendor_b}}` from the comparison template.
  - `{{search_window.display}}` — the human-readable window string, sourced from `out_dir/search_window.json` (`display` field, e.g. `trailing 1 year (2025-05-14..2026-05-14)`). This is the same value embedded into each topic JSON's `_meta.search_window.display` per C5, so it is identical across every per-vendor `REPORT.md` for a given session.

- **`fallback_count` and `ref_total` (Verification Footer fallback line).** Both are derived by the synthesizer from the per-topic `_meta.fallback_used` arrays (per C5):
  - `fallback_count` — `sum(len(_meta.fallback_used))` across every topic JSON for this vendor (one entry per ref that fell back from `mcp:signals` to `gh`).
  - `ref_total` — total ref count across all topic JSONs for this vendor (sum of every PR/issue ref appearing in any topic's `entries[*]`, deduplicated by `org/repo#N` so a ref cited under multiple topics counts once).
  - If both `fallback_count` and `ref_total` are `0`, render the line as the literal string `**Fallback usage (mcp:signals → gh):** none — every ref resolved on the MCP path.` instead of the `{{fallback_count}} of {{ref_total}} refs ...` form.
  - If `_meta.fallback_used` is missing on any topic file, `monitor_existence` (Stage 1) has RED-failed already per C5, so this loop should never see a file without the field at render time.

- **`ecosystem_plots` data source — SESSION-SETTING based, not filesystem-presence based.** This loop is enumerated from the session-wide setting `ecosystem_plot_metric` known at Phase 3 write time (NOT from `out_dir/ecosystem_plots/` filesystem state, because Phase 3 writes `REPORT.md` BEFORE Phase 4 writes the plots and the plot role does NOT modify per-vendor reports). The synthesizer expands `ecosystem_plot_metric` into the concrete metric list (`merged_prs`, `opened_issues`, `closed_issues`, or all three when the user picked `all`) and emits one `plot` block per metric. The referenced plot files will be written later by Phase 4 at top-level `out_dir/ecosystem_plots/`; the relative paths in the rendered REPORT.md resolve once the user reads the file (after Phase 4 completes). Phase 5 (comparison) re-uses the same Phase 4 artifacts via its own `[render_if_present ecosystem_plots]` block. For each metric in the expanded list the synthesizer constructs:
  - `plot.title` — derived from the metric and the run's feature (`merged_prs` → "Monthly Merged PRs Touching <feature> on <vendor1> vs <vendor2>", `opened_issues` → "Monthly Opened Issues Touching <feature> on <vendor1> vs <vendor2>", `closed_issues` → "Monthly Closed Issues Touching <feature> on <vendor1> vs <vendor2>"); the vendor names come from the session-wide `ecosystem_plot_vendor_groups` (which defaults to `chip_list` per C8.2); the feature comes from `scope.json.feature`.
  - `plot.feature` — the run's feature tag (e.g. `EP`), sourced from `scope.json.feature`. Surfaces in the per-plot caption so a reader can tell at a glance which feature the chart is filtered to.
  - `plot.png_relpath` / `plot.csv_relpath` / `plot.methods_relpath` — paths relative to `REPORT.md`. Because per-vendor reports live at `out_dir/{vendor}/REPORT.md` and the plot artifacts live at top-level `out_dir/ecosystem_plots/` (per C8.1), the relative paths include one parent-dir hop: `../ecosystem_plots/<metric>_by_vendor.png`, `../ecosystem_plots/<metric>_by_vendor.csv`, `../ecosystem_plots/<metric>_methods.md`.
  - `plot.window` — the inclusive `YYYY-MM..YYYY-MM` window (the session-wide `ecosystem_plot_window`, which defaults to `{search_window.start_month}..{search_window.end_month}` per C2 and the Fix 4 contract).
  - `plot.repos_summary` — comma-separated `org/repo` slugs from the session-wide `ecosystem_plot_repos`.
  - `plot.vendor_groups_summary` — comma-separated vendor names from the session-wide `ecosystem_plot_vendor_groups`.
  - `plot.source_tag` — the expected data-source tag (`mcp:signals` when `MCP_SQL_USABLE=true`; `gh-search-bulk` when the per-month `gh search` fallback path will be taken). Mirrors the same placeholder in `templates/COMPARISON_REPORT_template.md` so per-vendor and comparison reports stay in sync.

  The entire `## Feature Activity Context` section is wrapped in `[render_if_present ecosystem_plots]` and is omitted entirely when the session-wide `ecosystem_plot_metric == skip` (the synthesizer renders no `plot` blocks and the wrapper collapses to empty). In that case the report jumps straight from the per-topic loop to `## Verification Footer` with no placeholder gap.
