# Synthesized REPORT.md template

The main agent renders this skeleton with substituted values from `scope.json` + the per-topic JSONs + `verification.md`. Section headings come from `_meta.report_heading` of each topic file (NEVER `Q1`/`Q2`/etc).

Placeholders use `{{double-brace}}`. Any `[loop ...]` block is rendered once per topic (in the order topics were spawned).

---

```markdown
# {{framework}} {{feature}} on {{chip}} — Highlighted Report

**Generated:** {{date}} · **Scope:** {{scope_statement}}

**Verification:** every PR# / issue# below was checked live via `gh {pr,issue} view` against `{{framework_repo}}`. The independent monitor agent re-sampled ≥80 % of PRs and ≥90 % of issues; verdict was **{{verdict}}**. {{verdict_summary_line}}

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

**Verdict:** {{verdict}}. Full detail in [`verification.md`](./verification.md).

**Dropped (out-of-scope hardware) during verification:**
[loop drop in dropped_out_of_scope]
- {{drop.ref}} — {{drop.reason}}
[/loop]

**Internal conflicts reconciled:**
[loop conflict in internal_conflicts]
- {{conflict.summary}}
[/loop]

**Sources used:** {{sources_summary}}

**Dashboard-ready inputs:**
- `topics/*.json` — one machine-readable file per topic, stable schema (see `topic_json_schema.md`)
- `scope.json` — chip + framework + scope spec used for this run
- `verification.md` — full audit trail
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
