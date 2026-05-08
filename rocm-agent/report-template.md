# ROCm-agent Report Template

> Note: `REPORT.md` and `dashboard/report_citations.json` are rendered by the main agent during Phase 4; they are not produced by a delegated role. Use this file as the report shape source of truth for that synthesis step. The post-synthesis `monitor_evidence` rerun that re-verifies the drafted `REPORT.md` and `dashboard/report_citations.json` before publish is performed by `/home/ziwei/.cursor/skills/rocm-agent/agents/monitor_evidence.md`. After that rerun, the main agent refreshes dashboard provenance/final status and finalizes only the report footer unless citations must be regenerated.

Use this reference when synthesizing the dashboard-style `REPORT.md` for a ROCm-agent run. The first Phase 4 draft is written before the post-synthesis evidence verdict exists; after that rerun, finalize the footer from `monitors/*.md`, `dashboard/report_citations.json`, and refreshed `dashboard/dashboard_data.json` without changing citations.

## Rendering Rules

- Write the final report to `{out_dir}/REPORT.md`.
- Treat `REPORT.md` as a dashboard report: concise summary cards first, visualization-backed dashboard tables next, then drill-down sections.
- Build every dashboard card, table, and chart placeholder from `dashboard/dashboard_data.json`; do not compute dashboard numbers only in prose.
- Use chart placeholders that point to `dashboard/dashboard_data.json` chart specs so the data can be rendered later by another UI or notebook.
- Use ASCII markdown only.
- Do not invent sources, repos, PRs, issues, benchmark numbers, quotes, or monitor verdicts.
- Every non-obvious claim must cite evidence refs from collector or analysis artifacts.
- Use only two scored dimensions: `feature_relevance` and `performance_relevance`.
- Use 0 to 5 scores per side. Compute `gap = nvidia_score - amd_score`; positive means NVIDIA leads, negative means AMD leads.
- Sort dashboard and criteria rows by `abs(gap)` descending, then by confidence descending.
- Sort Stability Gap and Kernel/Performance Gap rows by `max(amd_severity, nvidia_severity)` descending, then by confidence descending. Use the stability enum order `none < low < medium < high < critical` for the stability comparison.
- Treat stability as evidence feeding `feature_relevance` or `performance_relevance`; never create a third stability/readiness score.
- If a source cannot be verified after monitor remediation, drop the claim and surface it in the evidence appendix.
- After drafting `REPORT.md`, write `dashboard/report_citations.json`, compare report refs against the manifest, then rerun `monitor_evidence`. After the rerun, refresh `dashboard/dashboard_data.json` provenance/final status and finalize the report footer without changing citations. If any finalization edit changes a report claim, cited ref, URL, quote, or citation entry, regenerate `dashboard/report_citations.json` and rerun post-synthesis `monitor_evidence`.
- Mark confidence clearly when comparison evidence is asymmetric, when quantitative benchmark methodology is incomplete, or when qualitative performance-path comparisons use different code paths.
- Do not publish a final report with unresolved `RED` monitor verdicts, a `RED` post-synthesis evidence rerun, a failing citation manifest check, stale dashboard/report final status, stale `remediation_state.json`, or citation entries that lack exact JSON Pointers plus stable `evidence_id`/`row_id`.

### No truncation - mandatory

NEVER truncate report content with three or more consecutive dots (`...`, `....`, etc.), Unicode `…`, `[truncated]`, `<truncated>`, or any other ellipsis/elision marker outside fenced quote blocks. NEVER drop facts (PR/issue refs, hardware codes, dtype, model names, kernel names, error classes, percentages, dispatch flags, comparability fields) from any rendered cell, sentence, or list.

The synthesis pattern is **summary plus detail**:

1. Render compact tables for Gap Dashboard, Stability Gap Analysis, Kernel and Performance Gap Analysis, Backend Repo Ownership Map, Subfeature Influence Matrix, and Feature/Performance Subcriteria Breakdown. Cells with source content `<= 140` characters render the source verbatim. Cells with source content `> 140` characters render a short non-truncating summary instead.
2. Immediately after each table that contains any summarized cell, render a "Per-row detail" subsection. Each subsection emits one block per row with the FULL prose copied verbatim from the matching `dashboard/dashboard_data.json` detail table (`tables.stability_gaps_detail`, `tables.performance_gaps_detail`) or, for tables without a dedicated detail table, from the upstream analysis artifact named in the citation manifest. The full prose lives in the detail subsection; the table cells never carry the only copy of any fact.
3. To produce a short cell summary for an over-long field, the main agent MAY invoke `agents/synthesis_field_summarizer.md` ONCE per field. The summarizer is bounded to a single field, returns a single-sentence string `<= max_chars` (default 140), and must preserve every distinct fact (refs, hardware, dtype, kernel name, error class, percentage, PR/issue ref) from the source. The full source text remains rendered verbatim in the per-row detail subsection regardless of whether the summarizer was invoked.
4. The summarizer is OPTIONAL. For fields where the source already fits in `max_chars`, the main agent renders the source text directly in the cell and may skip the per-row detail entry for that field (the detail subsection is required only when at least one cell in that row was summarized).
5. Quoted source text inside fenced code blocks is exempt from the truncation ban (a quoted source may legitimately end with `...` if that exact text is in the verified source). Outside fenced code blocks, regex `\.{3,}`, Unicode `…`, and explicit truncation/elision tokens are FORBIDDEN.

## Dashboard Data Contract

The final report must be backed by `dashboard/dashboard_data.json`.

Required dashboard blocks:

- `_meta.source_artifacts`: provenance list including `scope.json`, `subfeatures.json`, every collector JSON, every analysis JSON used by the dashboard, all three monitor files, and `dashboard/report_citations.json` once created. The `monitor_evidence.md` file must include the post-synthesis rerun after `REPORT.md` and `dashboard/report_citations.json` exist.
- `_meta.final_status`: `draft` before the post-synthesis evidence rerun, then refreshed after that rerun to `publishable`, `publishable-with-caveats`, or `blocked` with post-synthesis evidence verdict and citation manifest status.
- Every rendered table row must carry or be traceable to a stable `row_id`; every citation in `dashboard/report_citations.json` must resolve through exact JSON Pointers plus `evidence_id`/`row_id`. Do not use array position as the only provenance key.
- `counts`: structured counts that back every required count in this template (`total_subfeatures`, `support_state.{amd,nvidia}`, `framework_refs.{amd,nvidia}`, `enablement_state.{amd,nvidia}`, `backend_repo_influence`, `stability_gaps_by_dimension`, `performance_gaps_by_kind`, `criteria_by_dimension`, `dropped_unverified_total`, `dropped_out_of_scope_total`, `dropped_below_threshold_total`). `enablement_state.{amd,nvidia}` must include `unknown`.
- `cards`: top-level KPI cards such as total subfeatures, largest score gap, AMD high-confidence blockers, NVIDIA high-confidence advantages, dropped claims. Cards may use `value_ref` paths into `counts`.
- `tables.gap_dashboard`: one row per important subfeature with both `feature_gap` and `perf_gap` populated.
- `tables.score_rows`: one row per `(criterion, subfeature, dimension)` so visualizations can group by dimension. If `analysis/criteria_scores.json` uses `subfeatures: [...]`, dashboard data must explode that array into singular subfeature rows. Each row must include `rationale`, `evidence_tier`, `comparability_note`, `primary_amd_owner`, `primary_nvidia_owner`, `amd_co_owners`, `nvidia_co_owners`, `amd_integration_surface`, and `nvidia_integration_surface`. Owner-field enrichment ordering is defined in `criteria.md` § Criteria Row Requirements.
- `tables.repo_influence`: one row per backend repo and side.
- `tables.performance_gaps`: one row per allowed performance gap `kind`, with zero counts included.
- `tables.support_state_distribution`: one row per `(side, support_state)` combination, including zero-count rows for every allowed state on both sides.
- `tables.enablement_state_distribution`: one row per `(side, enablement_state)` combination, including zero-count rows for `default_on`, `flag_gated`, `unavailable`, and `unknown` on both sides.
- `tables.framework_refs_by_side`: one row per `(side, kind)` for `pr`, `issue`, and `recent_activity`.
- `charts`: chart specs pointing to tables, with chart types such as `bar`, `stacked_bar`, `heatmap`, `scatter`, `line`, or `table`.

The Markdown report should include a short "Chart Data" note for each chart with `chart_id`, `type`, `data_table`, `x`, `y`, and optional `series`.

## Required Counts

Surface these counts explicitly in `REPORT.md`:

- Total subfeatures discovered.
- AMD support-state counts: supported, experimental, missing, broken.
- NVIDIA support-state counts: supported, experimental, missing, broken.
- AMD-tagged framework PR count and issue count.
- NVIDIA-tagged framework PR count and issue count.
- Recent activity counts per side within `time_window_days`.
- Default-on, flag-gated, and unavailable subfeature counts per side.
- Unknown enablement-state counts per side.
- Number of AMD subfeatures influenced by ROCm or ROCm third-party repos.
- Number of NVIDIA subfeatures influenced by NVIDIA or NVIDIA third-party repos.
- Per-repo influenced subfeature counts for AMD/ROCm repos.
- Per-repo influenced subfeature counts for NVIDIA/CUDA repos.
- Stability gap count by `feeds_score`.
- Stability severity histogram per side: counts of `none`, `low`, `medium`, `high`, `critical` for AMD and for NVIDIA (from `counts.stability_severity.{amd,nvidia}`).
- Performance gap count by `kind`: `missing_kernel`, `immature_kernel`, `fallback_path`, `missing_fusion`, `poor_lowering`, `excessive_host_sync`.
- Performance severity histogram per side: counts of `0`, `1`, `2`, `3`, `4`, `5` for AMD and for NVIDIA (from `counts.performance_severity.{amd,nvidia}`).
- Criteria row counts by dimension: `feature_relevance`, `performance_relevance`.
- Count of dropped or unverified claims from all artifact `_meta.dropped_unverified` fields.
- Count of dropped out-of-scope claims from all artifact `_meta.dropped_out_of_scope` fields.
- Count of dropped below-threshold analysis rows from all artifact `_meta.dropped_below_threshold` fields.

Every count above must resolve through `dashboard/dashboard_data.json` (typically `counts.*` or a `tables.*` row). Do not compute report counts only from raw collector or analysis JSON.

## Dashboard Fields

The gap dashboard must include one row per important subfeature or blocker:

- `Subfeature`
- `AMD state`
- `NVIDIA state`
- `Feature score (AMD/NVIDIA)`
- `Perf score (AMD/NVIDIA)`
- `Feature gap`
- `Perf gap`
- `Max abs gap`
- `Primary AMD owner`
- `Primary NVIDIA owner`
- `Top blocker`
- `Evidence tier`
- `Confidence`
- `Evidence refs`

Keep cells short. Move detailed rationale to the relevant section.

## Final REPORT.md Skeleton

```markdown
# {framework} {feature}: AMD vs NVIDIA Dashboard Report

Generated: {date}
Output directory: `{out_dir}`
Scope: `{framework_repo}`, feature `{feature}`, hardware focus `{amd_hw_focus}` vs `{nv_hw_focus}`
Chip scope source: `scope.md`
Monitor verdicts: evidence={evidence_verdict}, scope={scope_verdict}, comparison={comparison_verdict}

Dashboard data: `dashboard/dashboard_data.json`
Citation manifest: `dashboard/report_citations.json`

## Summary cards

Render `dashboard_data.cards` as compact KPI cards:

| Metric | Value | Unit | Note |
|---|---:|---|---|
| ... | ... | ... | ... |

## Executive summary

- AMD support state and top blockers in 3 to 5 bullets.
- NVIDIA support state and top advantages in 3 to 5 bullets.
- Top 5 gaps sorted by `abs(nvidia_score - amd_score)`.
- One sentence on evidence quality and monitor outcome.

## Gap dashboard

Data source: `dashboard_data.tables.gap_dashboard`

| Subfeature | AMD state | NVIDIA state | Feature score (A/N) | Perf score (A/N) | Feature gap | Perf gap | Max abs gap | Primary AMD owner | Primary NVIDIA owner | Top blocker | Evidence tier | Confidence | Evidence refs |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

Chart Data:
- `score_gap_by_subfeature_dimension`: bar chart from `score_rows`, x=`subfeature`, y=`gap`, series=`dimension`. Per-dimension series comes from `tables.score_rows`, not `gap_dashboard`.
- `support_state_distribution`: stacked bar from `support_state_distribution`, x=`state`, y=`count`, series=`side`.
- `enablement_state_distribution`: stacked bar from `enablement_state_distribution`, x=`state`, y=`count`, series=`side`.
- `framework_refs_by_side`: stacked bar from `framework_refs_by_side`, x=`kind`, y=`count`, series=`side`.

Required counts:
- Total subfeatures: {n}
- AMD support states: supported={n}, experimental={n}, missing={n}, broken={n}
- NVIDIA support states: supported={n}, experimental={n}, missing={n}, broken={n}
- AMD-tagged framework PRs/issues: {counts.framework_refs.amd.prs}/{counts.framework_refs.amd.issues}
- NVIDIA-tagged framework PRs/issues: {counts.framework_refs.nvidia.prs}/{counts.framework_refs.nvidia.issues}
- Recent AMD activity within `time_window_days`: {counts.framework_refs.amd.recent_activity}
- Recent NVIDIA activity within `time_window_days`: {counts.framework_refs.nvidia.recent_activity}
- Default-on / flag-gated / unavailable / unknown AMD subfeatures: {counts.enablement_state.amd.default_on}/{counts.enablement_state.amd.flag_gated}/{counts.enablement_state.amd.unavailable}/{counts.enablement_state.amd.unknown}
- Default-on / flag-gated / unavailable / unknown NVIDIA subfeatures: {counts.enablement_state.nvidia.default_on}/{counts.enablement_state.nvidia.flag_gated}/{counts.enablement_state.nvidia.unavailable}/{counts.enablement_state.nvidia.unknown}
- AMD subfeatures influenced by ROCm or ROCm third-party repos: {counts.backend_repo_influence.amd_subfeatures_with_rocm_backend}
- NVIDIA subfeatures influenced by NVIDIA or NVIDIA third-party repos: {counts.backend_repo_influence.nvidia_subfeatures_with_cuda_backend}
- AMD stability severity (none/low/medium/high/critical): {counts.stability_severity.amd.none}/{counts.stability_severity.amd.low}/{counts.stability_severity.amd.medium}/{counts.stability_severity.amd.high}/{counts.stability_severity.amd.critical}
- NVIDIA stability severity (none/low/medium/high/critical): {counts.stability_severity.nvidia.none}/{counts.stability_severity.nvidia.low}/{counts.stability_severity.nvidia.medium}/{counts.stability_severity.nvidia.high}/{counts.stability_severity.nvidia.critical}
- AMD performance severity (0/1/2/3/4/5): {counts.performance_severity.amd."0"}/{counts.performance_severity.amd."1"}/{counts.performance_severity.amd."2"}/{counts.performance_severity.amd."3"}/{counts.performance_severity.amd."4"}/{counts.performance_severity.amd."5"}
- NVIDIA performance severity (0/1/2/3/4/5): {counts.performance_severity.nvidia."0"}/{counts.performance_severity.nvidia."1"}/{counts.performance_severity.nvidia."2"}/{counts.performance_severity.nvidia."3"}/{counts.performance_severity.nvidia."4"}/{counts.performance_severity.nvidia."5"}
- Dropped or unverified claims: {counts.dropped_unverified_total}
- Dropped out-of-scope claims: {counts.dropped_out_of_scope_total}
- Dropped below-threshold rows: {counts.dropped_below_threshold_total}

## Framework-level status

Summarize framework support by side: merged coverage, open issues, recent activity, default-on flags, experimental flags, unavailable paths, and roadmap signals. Cite framework PRs, issues, docs, and release notes.

## Subfeature influence matrix

One row per subfeature. Show AMD and NVIDIA framework PRs/issues, backend repos, support state, and whether the subfeature is default-on, flag-gated, or unavailable.

## Backend repo ownership map

One row per `(subfeature, side)`. Include `primary_owner`, `co_owners`, `integration_surface`, `confidence`, and evidence refs.

Counts to surface:
- Per AMD/ROCm repo: influenced subfeature count and top affected subfeatures.
- Per NVIDIA/CUDA repo: influenced subfeature count and top affected subfeatures.

Chart Data:
- `repo_influence_by_side`: bar chart from `repo_influence`, x=`repo`, y=`influenced_subfeatures`, series=`side`.

## Stability gap analysis

Data source: `dashboard_data.tables.stability_gaps_detail`

Render a compact table sorted by `max(amd_severity, nvidia_severity)` desc (stability enum order `none < low < medium < high < critical`), then by confidence desc:

| Subfeature | AMD severity | NVIDIA severity | Side affected | Symptom (summary) | Feeds score | AMD owner | NVIDIA owner | Confidence | Evidence refs |
|---|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

`AMD severity` and `NVIDIA severity` are rendered verbatim from `tables.stability_gaps_detail[*].amd_severity` and `nvidia_severity` (one of `none`, `low`, `medium`, `high`, `critical`). `Symptom (summary)` carries the full source text when `<= 140` chars; otherwise it carries the optional `synthesis_field_summarizer` output and the FULL prose appears in the per-row detail subsection below.

### Stability gap detail

For every row in the compact table whose `Symptom (summary)`, `Comparison baseline`, or `Rationale` was summarized, render one block of the following form (sourced verbatim from `tables.stability_gaps_detail`):

```
### Stability gap detail - {subfeature} ({side_affected})
- AMD severity: {amd_severity}
- NVIDIA severity: {nvidia_severity}
- Feeds score: {feeds_score}
- AMD owner candidate: {amd_owner_candidate}
- NVIDIA owner candidate: {nvidia_owner_candidate}
- Confidence: {confidence}
- Symptom: {full prose symptom from tables.stability_gaps_detail[*].symptom}
- Comparison baseline: {full prose comparison_baseline}
- Rationale: {full prose rationale}
- Evidence refs: {evidence_refs joined by comma}
```

Detail blocks render the full prose verbatim with no ellipsis or truncation markers outside verified fenced quotes. Always render at least the detail block for any row where any cell was summarized; for rows where every cell already fit, the detail block is optional but recommended for severity `>= high`.

Chart Data:
- `stability_severity_by_side`: stacked bar from `stability_severity_by_side`, x=`severity`, y=`count`, series=`side`.

## Kernel and performance gap analysis

Data source: `dashboard_data.tables.performance_gaps_detail`

Cover missing kernels, immature kernels, fallback paths, missing fusion, poor lowering, excessive host sync, communication bottlenecks, memory-system gaps, graph capture gaps, and benchmark deltas. Separate quantitative benchmark claims from qualitative performance-path claims. Include quantitative deltas only when evidence is `primary` or `secondary` and the benchmark comparability note is acceptable; otherwise state that evidence is anecdotal or insufficient. For qualitative path claims, name the compared code paths or explicitly state why they are not directly comparable.

Render a compact table sorted by `max(amd_severity, nvidia_severity)` desc (numeric), then by `evidence_tier` (`primary` > `secondary` > `anecdotal`), then by confidence desc:

| Subfeature | Kind | Claim type | AMD severity | NVIDIA severity | Delta estimate (summary) | AMD owner | NVIDIA owner | Confidence | Evidence tier | Evidence refs |
|---|---|---|---|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

`AMD severity` and `NVIDIA severity` are integers in `[0, 5]` rendered verbatim from `tables.performance_gaps_detail[*].amd_severity` and `nvidia_severity`. `Delta estimate (summary)` carries the full source text when `<= 140` chars; otherwise it carries the optional `synthesis_field_summarizer` output and the FULL prose appears in the per-row detail subsection below.

### Performance gap detail

For every row in the compact table whose `Delta estimate (summary)`, `nv_state`, `amd_state`, or any `comparability` value was summarized, render one block of the following form (sourced verbatim from `tables.performance_gaps_detail`):

```
### Performance gap detail - {subfeature} ({kind})
- Claim type: {claim_type}
- AMD severity: {amd_severity}
- NVIDIA severity: {nvidia_severity}
- AMD owner candidate: {amd_owner_candidate}
- NVIDIA owner candidate: {nvidia_owner_candidate}
- Confidence: {confidence}
- Evidence tier: {evidence_tier}
- NV state: {full prose nv_state}
- AMD state: {full prose amd_state}
- Delta estimate: {full prose delta_estimate}
- Comparability:
  - model: {comparability.model}
  - dtype: {comparability.dtype}
  - batch_size: {comparability.batch_size}
  - sequence_lengths: {comparability.sequence_lengths}
  - feature_flags: {comparability.feature_flags}
  - warmup: {comparability.warmup}
  - metric: {comparability.metric}
  - hardware_generation: {comparability.hardware_generation}
  - power_clock_policy: {comparability.power_clock_policy}
  - evidence_type: {comparability.evidence_type}
  - code_path_note: {comparability.code_path_note}
  - (for performance_path rows, also: nv_code_path, amd_code_path, feature_flags_or_dispatch_conditions, dependency_backend_versions per the source)
- Evidence refs: {evidence_refs joined by comma}
```

Detail blocks render the full prose and the entire `comparability` block verbatim with no ellipsis or truncation markers outside verified fenced quotes. Always render at least the detail block for any row where any cell was summarized; for rows where every cell already fit, the detail block is optional but recommended for severity `>= 4` on either side.

Chart Data:
- `performance_gap_kinds`: bar chart from `performance_gaps`, x=`kind`, y=`count`.
- `performance_severity_by_side`: stacked bar from `performance_severity_by_side`, x=`severity`, y=`count`, series=`side`.

## Feature/performance subcriteria breakdown

Render every row from `dashboard_data.tables.score_rows` (sourced from `analysis/criteria_scores.json` and enriched from `analysis/backend_repo_map.json` when needed). Include criterion, subfeature, dimension, AMD score, NVIDIA score, gap, evidence tier, comparability note, rationale, side-specific AMD/NVIDIA owners and integration surfaces, and evidence refs.

Chart Data:
- `score_gap_by_subfeature_dimension`: bar chart from `score_rows`, x=`subfeature`, y=`gap`, series=`dimension`.

## Fix roadmap

- Short-term framework fixes that unblock AMD subfeatures.
- Backend repo fixes for ROCm and NVIDIA stacks.
- Upstream dependency asks for kernel libraries, attention libraries, communication libraries, compiler/runtime, benchmark harnesses, or docs.
- Recommended owner and confidence for each action.

## Evidence appendix

Group cited evidence by artifact:
- `collectors/framework_amd.json`
- `collectors/framework_nvidia.json`
- `collectors/rocm_stack.json`
- `collectors/nvidia_stack.json`
- `collectors/official_web.json`
- `collectors/third_party_perf.json`
- `analysis/subfeature_influence_matrix.json`
- `analysis/backend_repo_map.json`
- `analysis/stability_gaps.json`
- `analysis/performance_kernel_gaps.json`
- `analysis/criteria_scores.json`
- `dashboard/dashboard_data.json`
- `dashboard/report_citations.json`

For each group, list cited PRs, issues, URLs, titles, verified state, evidence tier, and short quotes where available.

Citation manifest:
- `dashboard/report_citations.json` must include every non-obvious report claim, PR/issue ref, URL, and quote.
- The manifest check must report no refs missing from the manifest and no manifest refs missing from the report.
- Every manifest ref must include exact `artifact`, JSON Pointer, stable `evidence_id` or `row_id`, `source_url`, `verified_state`, and `quote_sha256` when a quote is present. The post-synthesis evidence monitor must resolve the pointer and confirm the ID at that location matches.
- Do not cite a ref in `REPORT.md` unless it is present in the manifest and points to a verified collector or analysis artifact.

- Dropped evidence:
- Include `_meta.dropped_unverified`, `_meta.dropped_out_of_scope`, and `_meta.dropped_below_threshold` from every artifact.
- Include any claims dropped by monitor remediation.

## Monitor verdict footer

Evidence monitor: {GREEN|YELLOW|RED} - {one-line reason}. File: `monitors/monitor_evidence.md`
Post-synthesis evidence rerun: {GREEN|YELLOW|RED} - verified `REPORT.md` and `dashboard/report_citations.json` refs before publish.
Scope monitor: {GREEN|YELLOW|RED} - {one-line reason}. File: `monitors/monitor_scope.md`
Comparison monitor: {GREEN|YELLOW|RED} - {one-line reason}. File: `monitors/monitor_comparison.md`
Citation manifest: {pass|fail} - File: `dashboard/report_citations.json`
Dashboard final status: {publishable|publishable-with-caveats|blocked} - refreshed after post-synthesis evidence rerun.
Remediation rounds used: {0|1|2}
Remediation state: `remediation_state.json` ({rounds_remaining} rounds remaining)
Final report status: {publishable|publishable-with-caveats|blocked}
```

## Section Guidance

### Executive Summary

Keep it decision-oriented. Name the highest-impact AMD blockers, NVIDIA advantages, any AMD advantages, and whether evidence is strong enough to act on.

### Gap Dashboard

Use it as the report index. Prefer high-confidence blockers and large absolute score gaps. Avoid long prose inside the table. Every displayed row must come from `dashboard_data.tables.gap_dashboard`.

### Chart Data

Do not embed rendered images. Instead, include chart metadata blocks that reference `dashboard/dashboard_data.json`. This makes the report visualizable in a notebook, BI tool, or future UI without scraping prose.

### Framework-Level Status

Focus on the requested framework repo. Include default behavior, user-visible flags, merged support, open gaps, and whether docs advertise the feature on each side.

### Subfeature Influence Matrix

Use the discovered subfeature taxonomy. Every row needs at least one framework anchor from docs, code, PRs, or issues.

### Backend Repo Ownership Map

Separate framework ownership from backend ownership. Use `primary_owner` for the most likely fix location and `co_owners` for integration dependencies.

### Stability Gap Analysis

Include only stability issues that affect scoped feature availability, correctness, or performance behavior. Drop unrelated CI flakes and operational noise.

Render BOTH the compact table AND the per-row detail subsection per the No-Truncation rule. Every retained row must show `AMD severity`, `NVIDIA severity`, `AMD owner`, and `NVIDIA owner` sourced from `dashboard_data.tables.stability_gaps_detail`. Sort by `max(amd_severity, nvidia_severity)` desc, then by confidence desc. Detail blocks render the full prose `symptom`, `comparison_baseline`, and `rationale` verbatim.

### Kernel and Performance Gap Analysis

For quantitative benchmark claims, prefer comparable model, dtype, batch size, sequence length, feature flags, warmup, metric definition, hardware generation, and power/clock policy when available. For qualitative performance-path claims, prefer comparable framework/feature/subfeature, named side-specific code paths, feature flags or dispatch conditions, hardware generation, and backend versions when known. If the applicable comparability checklist is incomplete, lower confidence and state what is missing.

Render BOTH the compact table AND the per-row detail subsection per the No-Truncation rule. Every retained row must show integer `AMD severity`, `NVIDIA severity`, `AMD owner`, and `NVIDIA owner` sourced from `dashboard_data.tables.performance_gaps_detail`. Sort by `max(amd_severity, nvidia_severity)` desc, then by `evidence_tier` (`primary` > `secondary` > `anecdotal`), then by confidence desc. Detail blocks render the full prose `nv_state`, `amd_state`, `delta_estimate`, and the entire `comparability` block verbatim.

### Criteria Breakdown

Every criterion must be tagged `feature_relevance` or `performance_relevance`. Include rationale and evidence refs; do not add operational/readiness criteria unless they directly affect the requested feature.

### Fix Roadmap

Group fixes by short-term framework work, backend repo work, and upstream dependency asks. Each action needs an owner candidate, linked evidence, and confidence.

## Evidence Appendix Rules

- Group evidence by source artifact.
- Preserve source refs exactly as verified.
- Include short verbatim quotes for web/blog/doc sources when available.
- Include PR/issue state and `verified_state`.
- Include evidence tier: `primary`, `secondary`, or `anecdotal`.
- Include dropped claims and the reason they were dropped.
- Keep URLs visible; do not hide critical source identity behind vague link text.

## Synthesis Field Summarizer Sub-Agent (Optional)

When a single source field is too long to fit in a markdown table cell, the main agent MAY invoke `agents/synthesis_field_summarizer.md` to produce the short cell summary. Contract:

- Inputs: one field's full source text, `max_chars` (default `140`), the field name (e.g., `symptom`, `delta_estimate`, `top_blocker`, `rationale`), and row context (`subfeature`, `side`).
- Output: a single string `<= max_chars` that preserves every distinct fact in the input - PR/issue refs, URLs, hardware codes, dtype, model name, kernel name, error class, percentages, dispatch flags. The summarizer must not invent facts and must not drop any verifiable fact.
- Used only for cell-level compression. The full source text is ALWAYS rendered verbatim in the matching per-row detail subsection regardless of summarizer invocation.
- The summarizer is OPTIONAL. For fields with source `<= max_chars`, the main agent renders the source text directly in the cell and may skip the per-row detail entry for that specific field.
- The summarizer must not spawn further sub-agents and must not edit any artifact; it returns the summary string only.

## Detail Appendix (Optional)

For other tables (Gap Dashboard, Backend Repo Ownership Map, Subfeature Influence Matrix, Feature/Performance Subcriteria Breakdown) that contain summarized cells, render a "## Detail Appendix" section after the Evidence Appendix containing the per-row detail blocks for those tables, following the same pattern as the Stability and Performance Gap detail subsections. Detail blocks always render full prose verbatim with no ellipsis or truncation markers outside verified fenced quotes.

## Monitor Verdict Footer Rules

- Always include all three monitor verdicts.
- The footer must name each monitor audit file.
- The evidence monitor footer must state the post-synthesis rerun verdict after `REPORT.md` and `dashboard/report_citations.json` exist. Finalize this footer only after the rerun and dashboard final-status refresh.
- Finalization may update only dashboard provenance/final-status fields and this footer. Any citation-affecting edit requires regenerating `dashboard/report_citations.json` and rerunning post-synthesis `monitor_evidence`.
- `GREEN` means proceed.
- `YELLOW` means remediation is required while recollection rounds remain. After the maximum rounds, `YELLOW` may remain only for documented non-blocking caveats that do not affect citation validity, scope correctness, score correctness, or comparison fairness.
- `RED` means the report is blocked unless the bad claims were dropped or recollected.
- Maximum remediation rounds: 2 total across all monitors.
- Set final report status:
  - `publishable` when all verdicts are `GREEN`, the post-synthesis evidence rerun is `GREEN`, and the citation manifest check passes.
  - `publishable-with-caveats` when the citation manifest check passes, no monitor verdict or post-synthesis evidence rerun is `RED`, and any remaining `YELLOW` findings are documented non-blocking caveats after the maximum remediation rounds.
  - `blocked` when any verdict or post-synthesis evidence rerun remains `RED`, any blocking `YELLOW` finding remains, or the citation manifest check fails.
