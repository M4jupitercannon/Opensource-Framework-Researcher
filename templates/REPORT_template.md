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
- `topics/*.json` — one machine-readable file per topic, stable schema (see `topic_json_schema.md`); every removed/recategorized item is preserved in `_meta.{dropped_out_of_scope, removed_by_strictness_audit, recategorized_as_*, dedup_canonical}` for full reversibility
- `scope.json` — chip + framework + scope spec used for this run
- `verification_existence.md` — Stage-1 audit trail (PR/issue/URL existence + verbatim-quote integrity)
- `verification_scope.md` — Stage-2 audit trail (chip-vendor scope strictness)
- `verification_feature.md` — Stage-3 audit trail (`{{feature}}`-strictness)
```

---

## Rendering rules

- `topic.headline_metric` is derived per topic:
  - `completed_subfeatures` → `{N} subfeatures, {M} merged PRs`
  - `open_issues` → `{N} open ({direct} direct + {tangential} tangential)`
  - `roadmap` → `{N} items ({in_flight} in-flight · {planned} planned · {stretch} stretch)`
  - `perf_numbers` → `{N} verified perf numbers`
  - `kernels_or_components` → `{N} kernels in {K} categories`

- `topic.primary_table` is a Markdown table optimized for dashboard ingestion (one row per entity). Per-topic table specs:
  - `completed_subfeatures` → columns: `# | Subfeature | Status | Hardware | Landmark PRs | First merged`
  - `open_issues` → columns: `Subfeature | Open direct | Open tangential | Total | Notable open issues`
  - `roadmap` → columns: `Item | Category | Linked PRs / RFCs | Priority`
  - `perf_numbers` → columns: `Subfeature | Metric | Baseline | Improved | Δ | Source`
  - `kernels_or_components` → one sub-table per category; columns: `Kernel | Library | PRs | Hardware | Notes`

- `topic.intro_paragraph` is one sentence noting source(s) used and any caveats (e.g. "13 perf numbers verified verbatim against PR bodies").

- `sources_summary` is the union of all `_meta.sources_used` arrays, deduplicated (e.g. `gh, WebFetch:docs.vllm.ai, WebSearch, mlperf, inferencex`).
