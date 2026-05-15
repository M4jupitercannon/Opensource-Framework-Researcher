---
name: feature-research
description: "Researches open-source AI inference/training feature status for a (chip vendor list, framework, feature) target and produces dashboard-ready JSON plus Markdown reports. Use when the user asks for a roadmap, status, comparison, dashboard, or research report such as 'NVIDIA + vLLM + EP' or '[AMD, NVIDIA] + vLLM + EP'."
compatibility:
  - claude-code
  - cursor
  - codex
  - opencode
metadata:
  workflow: research
  audience: researchers, perf engineers, product
  distribution: standalone-skill-repo
---

# feature-research

Multi-agent investigation of a single feature (e.g. Expert Parallelism, Prefill-Decode disaggregation, speculative decoding, paged-KV) in an open-source AI inference/training framework (vLLM, SGLang, TGI, TensorRT-LLM, …) on one or two chip vendors' datacenter accelerators (NVIDIA, AMD, Intel, Google TPU). Generalizes a prior NVIDIA + vLLM + EP research workflow.

## Inputs

**Required** (resolved during the **Session intake** step below — most can be supplied either at invocation time or captured by the intake prompts):
- `chip_list` — list of chip vendors to research. Each entry one of `NVIDIA`, `AMD`, `Intel`, `Google` (TPU). Replaces the legacy single `chip` field per C4 (multi-vendor / comparison support). Drives per-vendor scope filtering, the shared Phase 4 feature-activity plot, and the Phase 5 comparison fan-out (the latter only when `len(chip_list) == 2`). See **Session intake** for default + cap rules.
- `framework` — `vLLM`, `SGLang`, `TGI`, `TensorRT-LLM`, `llama.cpp`, etc. Drives the GitHub repo to query.
- `feature` — short tag for the area: `EP`, `PD-disaggregation`, `speculative-decoding`, `paged-KV`, `MoE`, `LoRA`, `quantization`, …
- `search_window` — canonical time-window object that bounds **all** Phase 1 PR/issue searches and (by default) the Phase 4 plot window. Phase 0 normalizes the user's raw input (`1y`, `YYYY-MM..YYYY-MM`, or `YYYY-MM-DD..YYYY-MM-DD`) into the full C2 schema. Pass either the resolved object or the raw string form (the latter is captured by the **Session intake** prompt). Full schema in **Session intake** below.

**Optional**:
- `topics` — override the default topic list (see `topics/default_topics.md`). Pass either a subset of default names or a list of custom topic specs (each with name + prompt + entry schema).
- `scope_override` — explicit scope spec; wins over the chip-vendor default.
- `out_dir` — defaults to `~/research/{framework}_{feature}/{YYYY-MM-DD}/`.
- `gh_repo_override` — explicit `org/repo` if the framework→repo map doesn't cover it.
- `feature_strictness_criteria` — optional plain-text block of feature-specific strictness rules to inject into Stage 3's `monitor_feature` prompt via the `{feature_strictness_criteria}` placeholder. If omitted, the placeholder is left empty and the monitor falls back to its built-in default 6-criterion test.
- `ecosystem_plot_metric` — optional. One of `merged_prs`, `opened_issues`, `closed_issues`, `all`, or `skip`. Drives the Phase 4 feature-activity plot. If absent, the main agent asks the user once after Phase 3 (default if the user accepts defaults: `merged_prs`). Name kept for back-compat with the legacy `ecosystem_plots/` directory.
- `ecosystem_plot_source` — optional. One of `topic_jsons` or `fresh_search`. Default: `topic_jsons`. The default builds Phase 4 from the audited Phase 1-3 topic JSONs without live MCP/GitHub fetches; `fresh_search` preserves the older expanded ecosystem search path when the user explicitly wants coverage outside the curated run evidence.
- `ecosystem_plot_window` — optional. `YYYY-MM..YYYY-MM` inclusive month range. Default: the session-wide `search_window` (per C2; falls back to trailing 24 full months ending the previous calendar month-end if `search_window` is somehow absent).
- `ecosystem_plot_repos` — optional. List of `org/repo` slugs to chart. Default: `["vllm-project/vllm", "sgl-project/sglang"]`.
- `ecosystem_plot_vendor_groups` — optional. List of vendor names to plot. Default: inherits `chip_list` (per C8.2; which itself defaults to `["AMD", "NVIDIA"]` when neither is supplied). In `fresh_search` mode each name MUST match a `## <vendor>` heading in `scope/chip_scope_map.md`; in default `topic_jsons` mode it filters vendor topic directories / `_meta.chip` values.
- `feature_keywords` — **not a session-intake input.** Used only when `ecosystem_plot_source=fresh_search`; the Phase 4 plot role prompts the user for this list at runtime (case-insensitive substring keywords used to filter PRs/issues to feature-relevant rows; e.g. for `feature: EP` the user might supply `["EP", "expert parallel", "expert-parallel", "EPLB"]`). Default `topic_jsons` mode does not ask for it. The bare `feature` tag alone is rejected as too generic — see the `fresh_search` procedure in `agents/plot_ecosystem_activity.md`.

## Session intake

The main agent runs four short prompts at session start (before Phase 0) to capture the global inputs that bound every downstream phase. All four are captured into named variables that downstream agents reference by name — researchers / analyzers / monitors MUST NOT re-parse the user's raw strings.

### (a) Time-window prompt → `search_window`

Ask the user for a time window that bounds all Phase 1 PR/issue searches and (by default) the Phase 4 plot window. Accept three input formats:
- preset, e.g. `1y` (trailing 1 year), `6mo`, `2y`
- inclusive month range, e.g. `2025-05..2026-04`
- inclusive day range, e.g. `2025-05-14..2026-05-14`

Phase 0 normalizes the raw input into the canonical `search_window` object (per C2):

```jsonc
{
  "search_window": {
    "raw_input":                   "1y",
    "display":                     "trailing 1 year (2025-05-14..2026-05-14)",
    "start_date":                  "2025-05-14",
    "end_date":                    "2026-05-14",
    "start_month":                 "2025-05",
    "end_month":                   "2026-05",
    "gh_qualifier_pr_merged":      "merged:2025-05-14..2026-05-14",
    "gh_qualifier_issue_created":  "created:2025-05-14..2026-05-14",
    "gh_qualifier_issue_closed":   "closed:2025-05-14..2026-05-14",
    "gh_qualifier_issue_updated":  "updated:2025-05-14..2026-05-14",
    "mcp_args":                    {"since": "2025-05-14T00:00:00Z", "until": "2026-05-14T23:59:59Z"},
    "sql_predicate_merged":        "json_extract(github_json, '$.pr_merged') = 1 AND json_extract(github_json, '$.pr_merged_at') >= '2025-05-14' AND json_extract(github_json, '$.pr_merged_at') < '2026-05-15'",
    "sql_predicate_created":       "source_type = 'github_issue' AND created_at >= '2025-05-14' AND created_at < '2026-05-15'",
    "sql_predicate_closed":        "source_type = 'github_issue' AND json_extract(github_json, '$.closed_at') >= '2025-05-14' AND json_extract(github_json, '$.closed_at') < '2026-05-15'"
  }
}
```

The `mcp_args` and `sql_predicate_*` fields mirror the redacted
`signals-service` schema guide. The Stage-1.5 appendix
`sources/signals_service_discovered.md` remains the source of truth for portable
date-filter support and column names; if a future host exposes a different
schema, refresh that appendix without committing host-specific probe output.

Phase 0 writes the **full** `search_window` object to `out_dir/search_window.json` and embeds a **4-field subset** (`raw_input`, `display`, `start_date`, `end_date`) into each topic JSON's `_meta.search_window` (per C5). Downstream researcher / analyzer / monitor / plot agents reference fields by name (e.g. `{search_window.gh_qualifier_pr_merged}`) and MUST NOT re-parse `raw_input`.

### (b) Vendor list prompt → `chip_list`

Ask the user which chip vendor(s) to research. Accept zero, one, or two vendor names from the supported set (`NVIDIA`, `AMD`, `Intel`, `Google`). `chip_list` size handling per C4:

- `len(chip_list) == 0` → default `["AMD", "NVIDIA"]`, comparison report rendered (Phase 5 runs).
- `len(chip_list) == 1` → single-vendor flow, no comparison report, Phase 5 skipped.
- `len(chip_list) == 2` → comparison report rendered (Phase 5 runs).
- `len(chip_list) > 2` → error out at session intake with the EXACT message:
  `comparison report supports exactly 2 vendors; you supplied N. Re-run with chip=[A,B] or accept default [AMD, NVIDIA].`

(N>2 is documented as a known v2 work item in `templates/COMPARISON_REPORT_template.md`.)

### (c) Framework + feature prompt → `framework`, `feature`

Unchanged from today. Capture the framework (e.g. `vLLM`) and the feature tag (e.g. `EP`, `speculative-decoding`). The framework drives the `framework_repo` lookup in `sources/source_playbook.md`.

### (d) Chip-scope confirmation step

After Phase 0 derives the per-vendor scope (in-scope SM/CDNA/XPU codes + scope statement) for each vendor in `chip_list`, the main agent presents the derived `in_scope` lists back to the user and offers three choices:
- **accept** the derived scope as-is, or
- **narrow** to a subset of the derived `in_scope` codes (e.g. drop SM86 from NVIDIA's list), or
- **override** with an explicit `scope_override` value (wins over the chip-vendor default per existing rule).

Only after the user confirms (or accepts the default by no-op) does the main agent fan out the per-vendor pipelines (Phase 1 → Phase 2 → Phase 3 per vendor branch).

## MCP pre-flight

Immediately after Session intake (still before Phase 0), the main agent performs a one-shot MCP pre-flight against the `signals-service` MCP server (referenced by its **registered name only** per C7 — the URL lives in your host's MCP config; per-host paths are listed in the **Per-host MCP setup** table in `sources/source_playbook.md`, and MUST NOT be hard-coded into committed docs):

1. Call `db_health()` — record availability.
2. Call `get_stats()` — record total row count, table list (when exposed), and latest update timestamp.

The pre-flight result is summarized into **two independent capability flags** (per C6):

- `MCP_DETAIL_USABLE` — controls the per-PR `get_signal_detail` path used by the per-PR MCP path (used by Phase-1 researchers and Phase-2 monitors). True iff `db_health()` passes AND the Stage-1.5 probe established a usable `signal_id` format. Defaults to **False** if `db_health()` errors.
- `MCP_SQL_USABLE` — controls the optional Phase 4 `fresh_search` raw-rows pattern (per C8) used by the Phase 4 SQL raw-rows path. True iff `MCP_DETAIL_USABLE` is True AND the Stage-1.5 probe succeeded against `execute_sql()` for a Phase 4–shaped query. Defaults to **False** if `db_health()` errors.

Both flags are persisted to `out_dir/_signals_schema.json` alongside the discovered canonical strings (`signal_id_format`, column names, date-filter support).

Do not assume the flags are true on a new host. The committed `sources/signals_service_discovered.md` file is a redacted schema guide, not a host-specific verdict; the session pre-flight resolves the per-run flags, and a host with `signals-service` unreachable falls back to `gh` automatically.

The flags fold into a single `data_source` variable consumed by every downstream agent's prompt:

- `data_source = mcp_first` when **either** `MCP_DETAIL_USABLE` or `MCP_SQL_USABLE` is True.
- `data_source = gh_only` when **both** flags are False.

When `data_source == gh_only` the agents still wire the MCP-first language for future runs (the host environment may differ at runtime); they simply never reach the MCP path because the fallback contract sees the failed `db_health()` and short-circuits to `gh`.

## Contract clarifications (C-tags)

The skill prose references contract clarifications by short tag (`C1`…`C8.2`). Each tag is a one-line invariant the rest of the runbook may assume.

| Tag | One-line contract |
|---|---|
| **C1** | Canonical phase order — Phase 4 (feature-activity plot) ALWAYS runs before Phase 5 (comparison synthesis) so the comparison report can embed the plots. See **Hard rule 8** for the full ordering and Phase-5 skip condition. |
| **C2** | Canonical `search_window` object schema, normalized at Phase 0 (`raw_input`, `display`, `start_date`, `end_date`, `start_month`, `end_month`, plus pre-baked `gh_qualifier_*` / `mcp_args` / `sql_predicate_*` strings); written once to `out_dir/search_window.json` and consumed by every downstream agent. |
| **C3** | Open-issue activity-based windowing — "in window" means `state:open AND updated:in_window`; researchers use `{search_window.gh_qualifier_issue_updated}` verbatim (long-lived important tickets touched in the window are included; stale untouched tickets are excluded). |
| **C4** | Comparison report supports **exactly two vendors** in v1 — `len(chip_list) > 2` errors out at Session intake with the verbatim message in **Session intake (b)**. `N>2` is a documented v2 work item in `templates/COMPARISON_REPORT_template.md`. |
| **C5** | Every topic JSON's `_meta` MUST include the 4-field `search_window` subset (`raw_input`, `display`, `start_date`, `end_date`) AND a `fallback_used` array (one row `{ref, tool_attempted, tool_succeeded, reason}` per `mcp:signals → gh` fallback). Stage 1 (`monitor_existence`) RED-fails files missing either field. |
| **C6** | Two independent MCP capability flags — `MCP_DETAIL_USABLE` (controls the per-PR `search_signals` + `get_signal_detail` path) and `MCP_SQL_USABLE` (controls the optional Phase 4 `fresh_search` SQL raw-rows path). Both default to **False** if `db_health()` errors. Folded into a single `data_source` variable: `mcp_first` when either is True, `gh_only` when both are False. |
| **C7** | `signals-service` MCP server is referenced by its **registered name only** in committed docs; the URL lives in the host's MCP config (per-host paths in the **Per-host MCP setup** table in `sources/source_playbook.md`). Committed docs, including `sources/signals_service_discovered.md`, use redacted placeholders rather than actual MCP URLs. |
| **C8** | Phase 4 defaults to `ecosystem_plot_source=topic_jsons`: build `month,repo,vendor_group,count` from audited Phase 1-3 topic JSON refs with no live fetch. `fresh_search` is opt-in and preserves the raw-rows pattern: one `execute_sql` per `(repo, metric)` over the full `search_window` with a feature-keyword OR-chain in the `WHERE`, returning RAW rows (`number, title, labels, bucket_at, repo`); the plot agent classifies vendor client-side. Server-side `GROUP BY` aggregation is forbidden. Both paths emit the same CSV schema; `BOTH` / `NEITHER` literals are no longer emitted. |
| **C8.1** | `ecosystem_plots/` lives at top-level `out_dir/` (NOT under any vendor folder). Phase 4 runs ONCE per session. Directory name kept for back-compat with downstream tools. |
| **C8.2** | Phase 4 `vendor_groups` defaults to `chip_list` so the plot legend matches the comparison-report `{{vendor_a}}` / `{{vendor_b}}` pair. |
| **C8.3** | Phase 4 feature-keyword filter is required only for `ecosystem_plot_source=fresh_search`; it is sourced from the user prompt at Phase 4 time (no `feature_scope_map.md`, no silent fallback to `[feature]` alone). Default `topic_jsons` mode does not ask for feature keywords because Phase 2/3 already enforced feature strictness. |

## Hard rules

1. **Use the best available execution mode.** Prefer parallel delegation mode when the host agent supports delegated workers; otherwise use serial fallback mode in the main agent.
2. **Flat delegation.** Researcher/analyzer/monitor roles must NOT launch nested workers. Nested delegation is not supported.
3. **Verify before write.** Every PR / issue / URL claim in any topic JSON MUST be live-verified by the producing researcher (via `mcp:signals` first, then `gh` / web fetch on documented fallback) before the JSON is written. The monitor re-samples but does not substitute. **Documented exception**: `monitor_existence` (Stage 1) does NOT re-sample refs in `external_repo_dependencies.json`, because those refs point to EXTERNAL repos (e.g. `deepseek-ai/DeepEP`, `NVIDIA/cutlass`), not `{framework_repo}`. The Phase-1b `analyzer_external_repos` is the authoritative verifier for external-repo refs — it ran the same MCP-first / `gh`-fallback verification against each external repo before write and recorded any failures in `_meta.dropped_unverifiable`. Re-sampling external refs in `monitor_existence` would duplicate analyzer work and risk falsely flagging valid refs (or coincidentally validating the wrong PR in `{framework_repo}`). Stage 1 still enforces the `_meta` schema on `external_repo_dependencies.json`, including the additional `_meta.dropped_unverifiable` requirement.
4. **No q1/q2/q3 labels.** Section headings in the synthesized report use the topic names directly (e.g. `## Completed Subfeatures`, `## Open Issues`, `## Roadmap`).
5. **Required JSON metadata.** Every topic JSON file has a top-level `_meta` block with at least: `scope`, `sources_used`, `verified_at`, `framework_repo`. See `templates/` notes (schema lives in `topics/topic_json_schema.md`).
6. **Three-stage audit trail.** Stage-1 (`monitor_existence`) catches hallucinated PRs/issues/URLs and verbatim-quote drift; failures here force a researcher re-spawn. Stage-2 (`monitor_scope`) drops out-of-scope items and logs them in `verification_scope.md` plus `_meta.dropped_out_of_scope`. Stage-3 (`monitor_feature`) drops/recategorizes items that fail feature-strictness and logs them in `verification_feature.md` plus `_meta.{removed_by_strictness_audit, recategorized_as_other, dedup_canonical}`. All three sets surface in the report's Verification Footer — nothing is silently discarded.
7. **External-repo analyzer is serial after the subfeature researcher.** The `analyzer_external_repos` role (Phase 1b) MUST NOT run in parallel with the `completed_subfeatures` researcher — it consumes that researcher's output. It also requires `kernels_or_components.json` and `open_issues.json`. The other two default topics (`roadmap`, `perf_numbers`) may still be in flight when the analyzer starts.
8. **Canonical phase order (per C1).** The main agent MUST execute phases in this exact order: `Phase 0 → Phase 1 (1a + 1b) → Phase 2 → Phase 3 → Phase 4 → Phase 5 (only when len(chip_list) == 2) → Phase 6 (hand-off)`. Phase 4 (feature-activity plot) ALWAYS runs before Phase 5 (comparison synthesis) so the comparison template can embed the plots via `[render_if_present ecosystem_plots]` (loop variable name kept for back-compat). Phase 5 is skipped entirely when `len(chip_list) == 1`.
9. **Multi-vendor cap (per C4).** Comparison mode supports **exactly two vendors** in v1. `len(chip_list) > 2` errors out at Session intake with the verbatim message documented under **Session intake (b)**. N>2 is a documented v2 work item in `templates/COMPARISON_REPORT_template.md`.
10. **MCP server URL handling (per C7).** The `signals-service` MCP server is referenced by its **registered name only** in committed docs. The URL is configured at install/host time in the host's MCP config (per-host paths in the **Per-host MCP setup** table in `sources/source_playbook.md` — Claude Code, Cursor, Codex, and opencode each have their own). `install.sh` MAY emit a warning if `signals-service` is not registered, but MUST NOT write the URL. Committed files, including `sources/signals_service_discovered.md`, MUST use redacted placeholders instead of actual MCP URLs.

## Execution modes

**Parallel delegation mode (Claude Code / Cursor / opencode / any host with delegated workers):**
- The main agent performs Phase 0, launches one delegated worker per Phase-1a topic, launches the Phase-1b analyzer after its three prerequisites exist, then launches the three monitor roles serially.
- Each delegated role receives the matching prompt template from `agents/`, writes exactly one artifact, and returns only a short summary.

**Serial fallback mode (Codex / any host without delegation):**
- The main agent performs the same roles itself, one at a time, using the prompt templates as role checklists.
- Preserve the same phase order, output paths, JSON schemas, verification gates, and re-spawn budget. A "re-spawn" in fallback mode means re-running that topic role from scratch with the offending refs embedded in the prompt.
- Do not skip verification because the run is serial; every included claim still needs MCP-first verification, with `gh` and web-source confirmation on documented fallback, before write.

## Workflow

### Phase 0 — Scope resolution (main agent)

Phase 0 is a session-wide setup followed by a per-vendor fan-out across `chip_list`. The orchestrator uses two placeholder shorthands consistently from here on:

- `{session_out_dir} = out_dir/` — session root (one per session).
- `{vendor_out_dir} = out_dir/{vendor}/` — per-vendor root (one per entry in `chip_list`).

1. **Per-vendor scope derivation.** For each `vendor` in `chip_list`: read `scope/chip_scope_map.md`, look up the matching vendor block, and derive `{in_scope, out_of_scope_drops, scope_statement}`. If `scope_override` is supplied for that vendor, replace the derived spec.
2. **Framework → repo lookup (once per session).** Read `sources/source_playbook.md` and resolve `framework` → `org/repo` for the GitHub queries (use `gh_repo_override` if given) — this is session-wide and shared across every vendor.
3. **Session-wide artifacts.** Create `out_dir/` and write the session-wide files at the session root: `out_dir/search_window.json` (the full C2 `search_window` object) and `out_dir/_signals_schema.json` (MCP pre-flight result + the `MCP_DETAIL_USABLE` / `MCP_SQL_USABLE` capability flags + the discovered canonical strings).
4. **Per-vendor artifacts.** For each `vendor` in `chip_list`: create `out_dir/{vendor}/topics/`, then write `out_dir/{vendor}/scope.json` with `{vendor, framework, framework_repo, feature, in_scope, out_of_scope_drops, scope_statement, generated_at}`. The orchestrator passes `{vendor_out_dir} = out_dir/{vendor}/` and `{session_out_dir} = out_dir/` into every delegated worker in Phases 1–3 so the worker writes to the correct per-vendor or session-wide path.

### Phase 1 — Research

Phase 1 fans out per vendor in `chip_list`. The orchestrator passes `{vendor_out_dir} = out_dir/{vendor}/` and `{session_out_dir} = out_dir/` into every delegated worker so files land under the correct vendor root.

#### Phase 1a — Default researchers

1. Read `topics/default_topics.md` (or use the user's `topics` override).
2. For each `vendor` in `chip_list`: in parallel delegation mode, launch one `researcher` worker per default topic in a single message. In serial fallback mode, run those researcher roles one at a time in the main agent. Each researcher's prompt is built from `agents/researcher.md` + the per-topic spec from `default_topics.md` + the resolved per-vendor scope + the source playbook + the target output path `{vendor_out_dir}/topics/{topic_name}.json`. NOTE: do NOT run a researcher for `external_repo_dependencies` here — it is produced by an analyzer in Phase 1b, not a generic researcher.
3. Wait for all Phase-1a researchers (across every vendor) to finish. Each returns: file path written, entry count, count of `gh`/web-fetch verifications performed.
4. If any researcher reports an error, surface it and stop before Phase 1b / Phase 2.

#### Phase 1b — External-repo analyzer (serial after subset of Phase 1a)

1. For each `vendor` in `chip_list`: once `{vendor_out_dir}/topics/completed_subfeatures.json`, `{vendor_out_dir}/topics/kernels_or_components.json`, AND `{vendor_out_dir}/topics/open_issues.json` have all been written by that vendor's Phase-1a researchers, run ONE `analyzer_external_repos` role (prompt from `agents/analyzer_external_repos.md`). In parallel delegation mode this can be delegated while the other independent Phase-1a researchers (`roadmap`, `perf_numbers`) are still running; in serial fallback mode run it after its prerequisites finish.
2. The analyzer's prompt is built from `agents/analyzer_external_repos.md` + the resolved per-vendor scope + the three input JSON paths + the target output path `{vendor_out_dir}/topics/external_repo_dependencies.json`.
3. Wait for ALL of Phase 1a + Phase 1b (across every vendor) to complete before advancing to Phase 2.
4. If the analyzer reports an error, surface it and stop before Phase 2.

**Topic-override prerequisites.** If the user passed a `topics:` override that includes `external_repo_dependencies` but omits any of its three prerequisites (`completed_subfeatures`, `kernels_or_components`, `open_issues`), error out at Phase 0 with a clear message naming the missing prerequisites — do NOT auto-include them.

### Phase 2 — Three-stage verification (serial)

Verification runs per vendor in `chip_list` as **three independent monitor roles in series**. Stage 1 audits existence (do the cited PRs/issues/URLs really exist?); Stage 2 audits chip-vendor scope; Stage 3 audits feature-strictness. Each stage writes its own `verification_*.md` under that vendor's `{vendor_out_dir}`. A later stage runs only after the prior stage reaches GREEN/YELLOW. The orchestrator binds `{vendor_out_dir} = out_dir/{vendor}/` and `{session_out_dir} = out_dir/` into every monitor invocation so the per-vendor verification reports land under `out_dir/{vendor}/`.

**Stage 1 — Existence & facts (`monitor_existence`)**
1. Run one `monitor_existence` role (prompt from `agents/monitor_existence.md`) with `out_dir/{vendor}/topics/` as input. No scope.json needed — this stage is purely "does this exist?".
2. Wait for `out_dir/{vendor}/verification_existence.md` and the verdict (`GREEN` / `YELLOW` / `RED` + must-fix list).
3. If `RED` (hallucinated PR/issue/URL or missing `_meta` fields): re-spawn the relevant researcher(s), then re-run Stage 1, subject to the phase-level re-spawn budget (see end of Phase 2). Do NOT advance to Stage 2. **The re-spawn prompt MUST embed the offending refs / hallucinated PR numbers / failing-strictness items from the punch-list verbatim, with an explicit instruction `do not re-introduce the following items: …`.**
4. If `YELLOW` (verbatim-quote drift or internal-consistency conflict): the main agent applies the must-fixes to the topic JSONs (correct quotes, reconcile state mismatches) before Stage 2.

**Stage 2 — Chip-vendor scope (`monitor_scope`)**
1. Run one `monitor_scope` role (prompt from `agents/monitor_scope.md`) with `out_dir/{vendor}/topics/`, `out_dir/{vendor}/scope.json`, and `out_dir/{vendor}/verification_existence.md` as inputs.
2. Wait for `out_dir/{vendor}/verification_scope.md` and the verdict (`GREEN` / `YELLOW` / `RED` + must-fix list).
3. If `RED` (a single topic loses majority of entries to scope filtering): re-spawn that researcher with a tightened scope reminder and re-run Stages 1 + 2, subject to the phase-level re-spawn budget (see end of Phase 2). Do NOT advance to Stage 3. **The re-spawn prompt MUST embed the offending refs / out-of-scope hardware items from the punch-list verbatim, with an explicit instruction `do not re-introduce the following items: …`.**
4. If `YELLOW` (out-of-scope drops, scope-mixing, or scope-ambiguity nits): the main agent applies the must-fixes to the topic JSONs (drop entries, narrow hardware lists, annotate ambiguous families) before Stage 3. Audit-trail entries are written to the appropriate per-topic `_meta.*` arrays:
   - **drops** → `_meta.dropped_out_of_scope` with `{ref, reason}`
   - **scope-mixing narrows** → `_meta.scope_mixing_narrowed` with `{ref, kept_as, dropped_mention}`
   - **scope-ambiguity annotations** → `_meta.scope_ambiguity_annotated` with `{ref, family, in_scope_members}`

**Stage 3 — Feature strictness (`monitor_feature`)**
1. Run one `monitor_feature` role (prompt from `agents/monitor_feature.md`) with `out_dir/{vendor}/topics/`, `out_dir/{vendor}/scope.json`, `out_dir/{vendor}/verification_existence.md`, and `out_dir/{vendor}/verification_scope.md`. **Source of `{feature_strictness_criteria}`**: if the user passed the optional `feature_strictness_criteria` input (see Inputs section), the main agent substitutes it verbatim into the placeholder. Otherwise, the main agent leaves the placeholder empty and the monitor falls back to its built-in default 6-criterion test (defined in `agents/monitor_feature.md` under "Default strictness test"). There is no separate per-feature criteria file — feature-specific strictness rules live entirely in the user-supplied input or in the monitor's default test.
2. Wait for `out_dir/{vendor}/verification_feature.md` and the verdict (`GREEN` / `AMBER` / `RED`).
3. If `RED` (a topic loses majority of entries or a headline subfeature itself fails strictness): re-spawn the relevant researcher(s) with a tightened `topic_prompt` and re-run all three stages, subject to the phase-level re-spawn budget (see end of Phase 2). **The re-spawn prompt MUST embed the offending refs / failing-strictness items from the punch-list verbatim, with an explicit instruction `do not re-introduce the following items: …`.**
4. If `AMBER` (recategorize / drop recommendations): the main agent applies the punch-list to the topic JSONs (move entries to canonical buckets, delete entries) while preserving every change in the appropriate per-topic `_meta.*` audit array:
   - **DROP** → `_meta.removed_by_strictness_audit` with `{ref, original_bucket, reason}`
   - **RECATEGORIZE** → `_meta.recategorized_as_other` with `{ref, original_bucket, target_bucket, reason}`
   - **DEDUP (cross-listed)** → `_meta.dedup_canonical` with `{ref, canonical_bucket, also_listed_under_dropped}`
   Apply BEFORE Phase 3.

**Re-spawn budget across the whole phase: at most 2 rounds total.** **Definition of one round**: one re-spawn of any single researcher, regardless of which stage triggered it. The budget is a single counter spanning all three stages combined — re-spawning researcher A from Stage 1 and then re-spawning researcher B from Stage 3 counts as **2 rounds** (not 1 per stage). **Re-spawning N researchers in a single stage counts as N rounds against the cap of 2.** (E.g. Stage-3 RED requiring re-spawn of `completed_subfeatures` researcher AND `perf_numbers` researcher = 2 rounds, exhausting the budget; the next RED escalates to the user.) If the second round still produces a RED verdict at any stage, escalate to the user rather than looping further.

### Phase 3 — Synthesis (main agent)

Phase 3 runs once per vendor in `chip_list`. Note Phase 3 writes `REPORT.md` BEFORE Phase 4 writes the feature-activity plot artifacts, so the per-vendor REPORT renders its `## Feature Activity Context` section optimistically from the SESSION-WIDE setting `ecosystem_plot_metric` (NOT from filesystem state under `out_dir/ecosystem_plots/`). The plot files will be written later by Phase 4 at top-level `out_dir/ecosystem_plots/`; the relative paths in `REPORT.md` (`../ecosystem_plots/<metric>_by_vendor.png`, etc.) resolve once the user reads the file after Phase 4 completes. See `templates/REPORT_template.md` rendering rules for the full enumeration contract.

1. By the time Phase 3 starts, the must-fix lists from all three stages (`monitor_existence`, `monitor_scope`, `monitor_feature`) have already been applied to the per-vendor topic JSONs in Phase 2. Re-confirm the JSONs match the punch-lists; spot-fix anything missed.
2. Read `templates/REPORT_template.md` and populate it with the per-topic JSON contents from `out_dir/{vendor}/topics/`:
   - Title: `# {framework} {feature} on {vendor} — Highlighted Report`
   - Header: date + scope statement (verbatim from `out_dir/{vendor}/scope.json`) + **all three** verification verdicts (existence, scope, feature-strictness).
   - **At-a-Glance Dashboard** table — one row per topic with count + headline insight.
   - One `##` section per topic with a primary table (one row per entity).
   - **`## Feature Activity Context`** — emitted iff the session-wide setting `ecosystem_plot_metric != skip` (known at Phase 3 time). The synthesizer enumerates one `plot` block per expanded metric and resolves each `plot.png_relpath` / `plot.csv_relpath` / `plot.methods_relpath` to `../ecosystem_plots/<metric>_by_vendor.png` (etc.) so the path is correct from `out_dir/{vendor}/REPORT.md`, and resolves `plot.feature` to `scope.json.feature`. The referenced files are written by Phase 4; this section is intentionally optimistic.
   - **Verification Footer** — verbatim-quote / internal-conflict fixes from Stage 1, scope drops from Stage 2, recategorize/drop punch-list from Stage 3, and links to all three `verification_*.md` files.
3. Write `out_dir/{vendor}/REPORT.md`.

### Phase 4 — Feature activity plot (main agent + plot worker)

Phase 4 runs **after Phase 3 has written `REPORT.md`** and **before the Phase-6 hand-off paragraph**. Unlike Phases 1–3, Phase 4 is **best-effort feature-specific activity context** — it is NOT covered by the three-stage monitor audit (no `monitor_*` re-sample). Its default purpose is to give the report a cross-vendor monthly activity series from the refs already collected and audited by the Phase 1-3 subagents. This avoids fetching the same feature area again just to compute simple statistics. The legacy directory name `ecosystem_plots/` is kept for back-compat with downstream tools and the Phase-3 optimistic section.

**Ordering contract (per C1).** Phase 3 has already written each per-vendor `out_dir/{vendor}/REPORT.md` with an optimistic `## Feature Activity Context` section referencing `../ecosystem_plots/<metric>_by_vendor.png` (etc.). Phase 4 writes those referenced files now; the plot role does NOT modify any `REPORT.md`. Phase 5 (comparison synthesis, when `len(chip_list) == 2`) re-uses the same Phase 4 artifacts via its own `[render_if_present ecosystem_plots]` block referencing `ecosystem_plots/<metric>_by_vendor.png` (relative to `out_dir/`). When `ecosystem_plot_metric == skip`, Phase 4 writes no artifacts; per-vendor REPORT.md and the comparison report omit the `## Feature Activity Context` section entirely because their `[render_if_present ecosystem_plots]` blocks resolve to empty.

1. **Resolve the metric set.**
   - If `ecosystem_plot_metric` is one of `merged_prs`, `opened_issues`, `closed_issues`, `all`, or `skip`, use it as-is (`all` expands to all three single-metric values).
   - Otherwise, the main agent asks the user once (using the host's interactive prompt capability, plain conversational prompt, or equivalent) which metric(s) to plot. If the user picks `skip`, do NOT create `out_dir/ecosystem_plots/`. Continue to Phase 5 when `len(chip_list) == 2`; otherwise advance directly to Phase 6. (Phase 4 being skipped does NOT change the Phase 5 gate per hard rule 8 — the gate is purely `len(chip_list) == 2`. When the gate is satisfied, the Phase 5 comparison report's `[render_if_present ecosystem_plots]` block simply resolves to empty.)
2. **Resolve the plot source.** If `ecosystem_plot_source` is absent, use `topic_jsons`. In this default mode, Phase 4 reads `out_dir/{vendor}/topics/*.json` after the Phase 1-3 monitor fixes have been applied, excludes `external_repo_dependencies.json` (external repo refs are not framework activity), de-duplicates refs, buckets them by month, and performs no MCP/`gh`/web fetch. If the user explicitly sets `ecosystem_plot_source=fresh_search`, use the older expanded ecosystem search path.
3. **Resolve the window** from `ecosystem_plot_window` (PRIMARY default per C2: the session-wide `search_window` resolved at Phase 0 — concretely `{search_window.start_month}..{search_window.end_month}`. SECONDARY fallback: trailing 24 full months ending the previous calendar month-end, used only when `search_window` is unbound — i.e. Phase 4 is invoked outside the normal Phase-0 flow) and the **repos** from `ecosystem_plot_repos` only for `fresh_search` mode (default `["vllm-project/vllm", "sgl-project/sglang"]`). `topic_jsons` mode uses the `framework_repo` recorded in each topic JSON.
4. **Resolve the vendor groups** from `ecosystem_plot_vendor_groups` (default inherits `chip_list`). In `topic_jsons` mode, the vendor group is the topic JSON `_meta.chip` / vendor directory. In `fresh_search` mode, the plot role reads the canonical `scope/chip_scope_map.md` at runtime to derive the keyword set per vendor.
5. **Resolve the feature keyword filter only for `fresh_search`.** The default `topic_jsons` source does not ask for feature keywords because the monitored topic JSONs are already feature-strict. When `ecosystem_plot_source=fresh_search`, the main agent does NOT pre-bind `feature_keywords` from anywhere — there is no `feature_scope_map.md`; the plot role prompts the user for the keyword list at runtime unless the user supplied it with the metric choice.
6. **Run the plot role.** In parallel delegation mode, launch one `plot_ecosystem_activity` worker per chosen metric in a single message; in serial fallback mode, run the role once per metric in the main agent. Each invocation receives the prompt template at `agents/plot_ecosystem_activity.md` with `{metric}`, `{ecosystem_plot_source}`, `{repos}`, `{date_range}`, `{vendor_groups}`, `{chip_scope_map_path}`, `{feature}`, `{feature_keywords}`, and `{session_out_dir}` bound (where `{session_out_dir} = out_dir/`, `{feature}` from `scope.json.feature`), and writes exactly three artifacts:
   - `{session_out_dir}/ecosystem_plots/{metric}_by_vendor.csv`
   - `{session_out_dir}/ecosystem_plots/{metric}_by_vendor.png`
   - `{session_out_dir}/ecosystem_plots/{metric}_methods.md`
7. **Wait for all launched plot roles to finish.** If any role reports a hard failure, record the failure in the hand-off but do not block Phase 6 — Phase 4 is best-effort.

**Hard rules specific to Phase 4:**
- Phase 4 is NOT covered by the three-stage audit; the plot role does not produce `_meta.dropped_*` arrays.
- `topic_jsons` is the default source and MUST NOT perform live data fetches. It is a simple statistic over the audited run evidence, not an exhaustive ecosystem search.
- `fresh_search` is opt-in. In that mode, vendor classification keywords MUST be derived from `scope/chip_scope_map.md` at runtime, and feature filter keywords MUST come from the user prompt at Phase 4 time (no `feature_scope_map.md`, no silent fallback to `[feature]` alone).
- In `fresh_search` mode, title + labels only for classification (no PR/issue body fetch in the bulk pass — see `agents/plot_ecosystem_activity.md` for rationale).
- Bucket field per metric is fixed: `merged_prs` → `mergedAt`, `opened_issues` → `createdAt`, `closed_issues` → `closedAt`. Never mix bucket fields within one CSV.
- In `fresh_search` mode, the MCP `execute_sql` query MUST return raw rows (one per matching PR/issue). Server-side `GROUP BY` / `COUNT(*)` aggregation is forbidden.
- All chart rendering MUST go through `scripts/plot_ecosystem_activity.py`. Writing a one-off `_build.py`, calling matplotlib from inside the role, or post-processing the PNG are forbidden — see hard rule 10 in `agents/plot_ecosystem_activity.md`.
- Phase 4 runs ONCE per session (not per vendor) and writes to top-level `out_dir/ecosystem_plots/` (NOT under any vendor folder) per C8.1. The comparison report references plots with relative paths from `out_dir/` (i.e. `ecosystem_plots/{metric}_by_vendor.png`); per-vendor `out_dir/{vendor}/REPORT.md` files reference the same plots with `../ecosystem_plots/{metric}_by_vendor.png`.
- `vendor_groups` defaults to `chip_list` per C8.2 (the user-supplied `ecosystem_plot_vendor_groups` override still wins if set).

### Phase 5 — Comparison synthesis

Phase 5 runs **only when `len(chip_list) == 2`** and **always after Phase 4** (per the canonical phase order in C1, hard rule 8). It synthesizes a side-by-side comparison report from the two per-vendor pipelines' outputs.

1. Read the two vendors' per-topic JSONs (`out_dir/{vendor_a}/topics/*.json` and `out_dir/{vendor_b}/topics/*.json`) plus their per-vendor `REPORT.md` headlines.
2. Read `templates/COMPARISON_REPORT_template.md`. Bind `{{vendor_a}}`, `{{vendor_b}}`, `{{framework}}`, `{{feature}}`, `{{date}}`, `{{search_window.display}}`, the per-topic `{{topic.count_a}}` / `{{topic.count_b}}` / `{{topic.delta_note}}` / `{{topic.headline_a}}` / `{{topic.headline_b}}` / `{{topic.common}}` / `{{topic.unique}}` values, and the per-vendor `{{fallback_count_*}}` / `{{ref_total_*}}` totals.
3. Resolve the `[render_if_present ecosystem_plots]` block — Phase 4 ran first per C1, so when the feature-activity plot artifacts exist under `out_dir/ecosystem_plots/`, the comparison report embeds them with paths relative to `out_dir/` (per C8.1). When Phase 4 was skipped (`ecosystem_plot_metric=skip`) or all plot roles failed, the `render_if_present` block resolves to empty.
4. Write `out_dir/COMPARISON_REPORT.md`.

Phase 5 is best-effort synthesis only — it does NOT re-verify any underlying refs (those are already covered by each per-vendor pipeline's three-stage audit). It does roll up each vendor's `_meta.fallback_used` counts into a single Verification Footer line.

### Phase 6 — Hand-off

Print a single short paragraph naming, per vendor, `out_dir/{vendor}/REPORT.md`, the three `out_dir/{vendor}/verification_existence.md` / `verification_scope.md` / `verification_feature.md` files, and the per-topic JSON files. Then list the session-wide artifacts: `out_dir/search_window.json` (the canonical C2 object), `out_dir/_signals_schema.json` (the MCP pre-flight + Stage-1.5 capability flags + discovered canonical strings), and — when Phase 4 ran — every `out_dir/ecosystem_plots/*.png`, `out_dir/ecosystem_plots/*.csv`, and `out_dir/ecosystem_plots/*_methods.md` (feature-activity plots; directory name kept for back-compat). When Phase 5 ran (`len(chip_list) == 2`), also name `out_dir/COMPARISON_REPORT.md`. Note that the topic JSONs are the dashboard-ready inputs (stable schema across runs), every drop/recategorize is recorded in `_meta` for full reversibility, and the feature-activity plot artifacts + the comparison report are best-effort context outside the three-stage audit trail.

## Defaults & framework→repo map

See `sources/source_playbook.md`. Quick reference:
- `vLLM` → `vllm-project/vllm`
- `SGLang` → `sgl-project/sglang`
- `TGI` → `huggingface/text-generation-inference`
- `TensorRT-LLM` → `NVIDIA/TensorRT-LLM`
- `llama.cpp` → `ggerganov/llama.cpp`

If the user names a framework not in the map and does not pass `gh_repo_override`, ask the user for the repo before Phase 0.

## File index

| Path | Purpose |
|---|---|
| `topics/default_topics.md` | The 6 default research topics + their prompts and entry schemas (5 Phase-1a researchers + 1 Phase-1b analyzer topic) |
| `topics/topic_json_schema.md` | Required JSON shape every topic file must conform to (includes the C5 `_meta.search_window` and `_meta.fallback_used` fields). |
| `scope/chip_scope_map.md` | Vendor → in/out scope SM/CDNA/XPU codes and scope statements |
| `sources/source_playbook.md` | `mcp:signals` (PRIMARY) + `gh` (DOCUMENTED FALLBACK) + host web-fetch/search / MLPerf / InferenceX recipes |
| `sources/signals_service_discovered.md` | Redacted Stage-1.5 MCP discovery guide. Records portable `signals-service` schema strings (`signal_id_format`, column names, date-filter support) and the Phase 4 SQL template shape without actual MCP URLs or host-specific verdict flags. |
| `agents/researcher.md` | Per-topic researcher worker prompt template |
| `agents/analyzer_external_repos.md` | Phase-1b external-repo analyzer worker prompt template — runs after `completed_subfeatures` + `kernels_or_components` + `open_issues` are on disk; produces `topics/external_repo_dependencies.json` |
| `agents/monitor_existence.md` | Stage-1 verification worker prompt — every cited PR/issue/URL must really exist on `{framework_repo}`; verbatim quotes must match their source |
| `agents/monitor_scope.md` | Stage-2 verification worker prompt — chip-vendor scope strictness (every entry must target in-scope hardware) |
| `agents/monitor_feature.md` | Stage-3 verification worker prompt — feature-strictness audit (every entry must directly influence `{feature}`'s functionality or performance) |
| `agents/plot_ecosystem_activity.md` | Phase 4 feature-activity plot worker prompt — produces one CSV + PNG + methods note per metric. Default source is audited topic JSONs; optional `fresh_search` derives vendor keywords from `scope/chip_scope_map.md` and feature keywords from a runtime prompt. File name kept for back-compat. |
| `scripts/build_ecosystem_activity_from_topics.py` | Phase 4 default topic-JSON builder. Reads audited `out_dir/{vendor}/topics/*.json`, de-duplicates refs, buckets by metric timestamp, and writes the canonical `month,repo,vendor_group,count` CSV plus methods note without live fetches. |
| `scripts/plot_ecosystem_activity.py` | Phase 4 CSV → PNG renderer (one line per `(repo, vendor)`). Pure file-in / file-out so the chart can be regenerated independently of the plot worker. Pass `--feature` to interpolate the run's feature into the title. |
| `templates/REPORT_template.md` | Synthesized per-vendor report skeleton |
| `templates/COMPARISON_REPORT_template.md` | Side-by-side comparison report skeleton rendered by Phase 5 when `len(chip_list) == 2`. Uses `{{vendor_a}}` / `{{vendor_b}}` placeholders and a `[render_if_present ecosystem_plots]` block (loop variable name kept for back-compat) populated by Phase 4 feature-activity plot artifacts. |
