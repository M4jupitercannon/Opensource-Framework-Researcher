# Synthesized REPORT.md template

The main agent renders this skeleton with substituted values from `scope.json` + the per-topic JSONs + all three verification files: `verification_existence.md` (Stage 1), `verification_scope.md` (Stage 2), `verification_feature.md` (Stage 3). Section headings come from `_meta.report_heading` of each topic file (NEVER `Q1`/`Q2`/etc).

Placeholders use `{{double-brace}}`. Any `[loop ...]` block is rendered once per topic (in the order topics were spawned).

---

```markdown
# {{framework}} {{feature}} on {{chip}} — Highlighted Report

**Generated:** {{date}} · **Scope:** {{scope_statement}}

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

- `sources_summary` is the union of all `_meta.sources_used` arrays, deduplicated. **When emitting `sources_summary` in the header, collapse all `WebFetch:*` tags to a single `WebFetch`** (e.g. `WebFetch:docs.vllm.ai` and `WebFetch:developer.nvidia.com/blog` both become `WebFetch`). The full per-host list lives in the per-topic JSONs. Example summary: `gh, WebFetch, WebSearch, mlperf, inferencex`.

- **`verbatim_quote_fixes` data source.** This loop is NOT sourced from any `_meta.*` field — instead, parse the `### Verbatim-quote drift` table in `verification_existence.md`. Each table row produces one entry: `{field: <Field column>, ref: <File column> (and any inline ref), was: <Claimed quote column>, now: <Actual quote column>}`. If the table is absent or empty, render the loop as the literal line `- (none)`.

- **`internal_conflicts` data source.** Same pattern — parse the `### Internal-consistency conflicts` table in `verification_existence.md`. Each row produces `{ref: <Ref column>, summary: "<file A claim> vs <file B claim>; correct: <which is correct>"}`. If the table is absent or empty, render `- (none)`.

- **`scope_mixing_narrowed` data source.** Per-topic `_meta.scope_mixing_narrowed` arrays, written by the synthesizer in Phase 2.2 step 4 when applying Stage-2 must-fixes. Concatenate across all topic files. Each entry has shape `{ref, kept_as, dropped_mention}`. If empty across all files, render `- (none)`.

- **`scope_ambiguity_annotated` data source.** Per-topic `_meta.scope_ambiguity_annotated` arrays, written by the synthesizer in Phase 2.2 step 4. Concatenate across all topic files. Each entry has shape `{ref, family, in_scope_members}`. If empty across all files, render `- (none)`.

- **`dropped_out_of_scope`, `removed_by_strictness_audit`, `recategorized_as_other`, `dedup_canonical` data sources.** Each is the concatenation of the same-named `_meta.*` array across all topic files (written by the synthesizer in Phase 2.2 step 4 and Phase 2.3 step 4 respectively). If empty across all files, render `- (none)`.
