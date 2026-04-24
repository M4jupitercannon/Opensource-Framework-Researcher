---
name: feature-research
description: "Multi-agent research on the state of a hot/key feature in an open-source AI framework on a specific chip vendor. Trigger when the user names a (chip vendor, framework, feature) triple — e.g. 'NVIDIA + vLLM + EP', 'AMD + SGLang + PD-disaggregation', 'NVIDIA + TensorRT-LLM + speculative decoding' — and asks for a report, overview, dashboard, status, roadmap, or 'what's the state of X' investigation. Produces dashboard-ready per-topic JSON files plus a synthesized Markdown report."
compatibility: claude-code
metadata:
  workflow: research
  audience: researchers, perf engineers, product
  distribution: standalone-skill-repo
---

# feature-research

Multi-agent investigation of a single feature (e.g. Expert Parallelism, Prefill-Decode disaggregation, speculative decoding, paged-KV) in an open-source AI inference/training framework (vLLM, SGLang, TGI, TensorRT-LLM, …) on one chip vendor's datacenter accelerators (NVIDIA, AMD, Intel, Google TPU). Generalizes the methodology of `~/vllm_research/v2/` (NVIDIA + vLLM + EP).

## Inputs

**Required**:
- `chip` — vendor: `NVIDIA`, `AMD`, `Intel`, `Google` (TPU). Drives scope filtering.
- `framework` — `vLLM`, `SGLang`, `TGI`, `TensorRT-LLM`, `llama.cpp`, etc. Drives the GitHub repo to query.
- `feature` — short tag for the area: `EP`, `PD-disaggregation`, `speculative-decoding`, `paged-KV`, `MoE`, `LoRA`, `quantization`, …

**Optional**:
- `topics` — override the default topic list (see `topics/default_topics.md`). Pass either a subset of default names or a list of custom topic specs (each with name + prompt + entry schema).
- `scope_override` — explicit scope spec; wins over the chip-vendor default.
- `out_dir` — defaults to `~/research/{framework}_{feature}/{YYYY-MM-DD}/`.
- `gh_repo_override` — explicit `org/repo` if the framework→repo map doesn't cover it.
- `feature_strictness_criteria` — optional plain-text block of feature-specific strictness rules to inject into Stage 2.3's `monitor_feature` prompt via the `{feature_strictness_criteria}` placeholder. If omitted, the placeholder is left empty and the monitor falls back to its built-in default 6-criterion test.

## Hard rules

1. **Orchestration-only.** The main agent never executes a researcher or monitor runbook itself. It resolves scope, fans out sub-agents, then synthesizes their outputs.
2. **Flat sub-agents.** Researchers and the monitor must NOT call the Agent tool. (Nested sub-agents are not supported.)
3. **Verify before write.** Every PR / issue / URL claim in any topic JSON MUST be live-verified by the producing researcher (via `gh` / `WebFetch`) before the JSON is written. The monitor re-samples but does not substitute. **Documented exception**: `monitor_existence` (Stage 1) does NOT re-sample refs in `external_repo_dependencies.json`, because those refs point to EXTERNAL repos (e.g. `deepseek-ai/DeepEP`, `NVIDIA/cutlass`), not `{framework_repo}`. The Phase-1b `analyzer_external_repos` is the authoritative verifier for external-repo refs — it ran `gh pr/issue view` against each external repo before write and recorded any failures in `_meta.dropped_unverifiable`. Re-sampling external refs in `monitor_existence` would duplicate analyzer work and risk falsely flagging valid refs (or coincidentally validating the wrong PR in `{framework_repo}`). Stage 1 still enforces the `_meta` schema on `external_repo_dependencies.json`, including the additional `_meta.dropped_unverifiable` requirement.
4. **No q1/q2/q3 labels.** Section headings in the synthesized report use the topic names directly (e.g. `## Completed Subfeatures`, `## Open Issues`, `## Roadmap`).
5. **Required JSON metadata.** Every topic JSON file has a top-level `_meta` block with at least: `scope`, `sources_used`, `verified_at`, `framework_repo`. See `templates/` notes (schema lives in `topics/topic_json_schema.md`).
6. **Three-stage audit trail.** Stage-1 (`monitor_existence`) catches hallucinated PRs/issues/URLs and verbatim-quote drift; failures here force a researcher re-spawn. Stage-2 (`monitor_scope`) drops out-of-scope items and logs them in `verification_scope.md` plus `_meta.dropped_out_of_scope`. Stage-3 (`monitor_feature`) drops/recategorizes items that fail feature-strictness and logs them in `verification_feature.md` plus `_meta.{removed_by_strictness_audit, recategorized_as_other, dedup_canonical}`. All three sets surface in the report's Verification Footer — nothing is silently discarded.
7. **External-repo analyzer is serial after the subfeature researcher.** The `analyzer_external_repos` sub-agent (Phase 1b) MUST NOT be spawned in parallel with the `completed_subfeatures` researcher — it consumes that researcher's output. It also requires `kernels_or_components.json` and `open_issues.json`. The other two default topics (`roadmap`, `perf_numbers`) may still be in flight when the analyzer starts.

## Workflow

### Phase 0 — Scope resolution (main agent)

1. Read `scope/chip_scope_map.md`. Look up the `chip` argument and derive a scope spec (in-scope SM/CDNA/XPU codes + out-of-scope SKUs to drop + a one-line "scope statement" string for the report header).
2. If `scope_override` is supplied, replace the derived spec.
3. Read `sources/source_playbook.md` and resolve `framework` → `org/repo` for the GitHub queries (use `gh_repo_override` if given).
4. Create `out_dir/` and write `out_dir/scope.json` with: `{chip, framework, framework_repo, feature, in_scope, out_of_scope_drops, scope_statement, generated_at}`.

### Phase 1 — Parallel research (main agent fans out)

#### Phase 1a — Default researchers (parallel)

1. Read `topics/default_topics.md` (or use the user's `topics` override).
2. **In a single message, spawn one `researcher` sub-agent per default topic** (parallel tool calls). Each researcher's prompt is built from `agents/researcher.md` + the per-topic spec from `default_topics.md` + the resolved scope + the source playbook + the target output path `out_dir/topics/{topic_name}.json`. NOTE: do NOT spawn a researcher for `external_repo_dependencies` here — it is produced by an analyzer in Phase 1b, not a generic researcher.
3. Wait for all Phase-1a researchers to return. Each returns: file path written, entry count, count of `gh`/`WebFetch` verifications performed.
4. If any researcher reports an error, surface it and stop before Phase 1b / Phase 2.

#### Phase 1b — External-repo analyzer (serial after subset of Phase 1a)

1. Once `out_dir/topics/completed_subfeatures.json`, `out_dir/topics/kernels_or_components.json`, AND `out_dir/topics/open_issues.json` have all been written by their Phase-1a researchers, spawn ONE `analyzer_external_repos` sub-agent (prompt from `agents/analyzer_external_repos.md`). The other Phase-1a researchers (`roadmap`, `perf_numbers`) may still be running in parallel — the analyzer does not depend on them.
2. The analyzer's prompt is built from `agents/analyzer_external_repos.md` + the resolved scope + the three input JSON paths + the target output path `out_dir/topics/external_repo_dependencies.json`.
3. Wait for ALL of Phase 1a + Phase 1b to complete before advancing to Phase 2.
4. If the analyzer reports an error, surface it and stop before Phase 2.

**Topic-override prerequisites.** If the user passed a `topics:` override that includes `external_repo_dependencies` but omits any of its three prerequisites (`completed_subfeatures`, `kernels_or_components`, `open_issues`), error out at Phase 0 with a clear message naming the missing prerequisites — do NOT auto-include them.

### Phase 2 — Three-stage verification (serial)

Verification runs as **three independent monitor sub-agents in series**. Stage 1 audits existence (do the cited PRs/issues/URLs really exist?); Stage 2 audits chip-vendor scope; Stage 3 audits feature-strictness. Each stage writes its own `verification_*.md`. A later stage runs only after the prior stage reaches GREEN/YELLOW.

**Stage 2.1 — Existence & facts (`monitor_existence`)**
1. Spawn one `monitor_existence` sub-agent (prompt from `agents/monitor_existence.md`) with `out_dir/topics/` as input. No scope.json needed — this stage is purely "does this exist?".
2. Wait for `out_dir/verification_existence.md` and the verdict (`GREEN` / `YELLOW` / `RED` + must-fix list).
3. If `RED` (hallucinated PR/issue/URL or missing `_meta` fields): re-spawn the relevant researcher(s), then re-run Stage 2.1, subject to the phase-level re-spawn budget (see end of Phase 2). Do NOT advance to Stage 2.2. **The re-spawn prompt MUST embed the offending refs / hallucinated PR numbers / failing-strictness items from the punch-list verbatim, with an explicit instruction `do not re-introduce the following items: …`.**
4. If `YELLOW` (verbatim-quote drift or internal-consistency conflict): the main agent applies the must-fixes to the topic JSONs (correct quotes, reconcile state mismatches) before Stage 2.2.

**Stage 2.2 — Chip-vendor scope (`monitor_scope`)**
1. Spawn one `monitor_scope` sub-agent (prompt from `agents/monitor_scope.md`) with `out_dir/topics/`, `out_dir/scope.json`, and `out_dir/verification_existence.md` as inputs.
2. Wait for `out_dir/verification_scope.md` and the verdict (`GREEN` / `YELLOW` / `RED` + must-fix list).
3. If `RED` (a single topic loses majority of entries to scope filtering): re-spawn that researcher with a tightened scope reminder and re-run Stages 2.1 + 2.2, subject to the phase-level re-spawn budget (see end of Phase 2). Do NOT advance to Stage 2.3. **The re-spawn prompt MUST embed the offending refs / out-of-scope hardware items from the punch-list verbatim, with an explicit instruction `do not re-introduce the following items: …`.**
4. If `YELLOW` (out-of-scope drops, scope-mixing, or scope-ambiguity nits): the main agent applies the must-fixes to the topic JSONs (drop entries, narrow hardware lists, annotate ambiguous families) before Stage 2.3. Audit-trail entries are written to the appropriate per-topic `_meta.*` arrays:
   - **drops** → `_meta.dropped_out_of_scope` with `{ref, reason}`
   - **scope-mixing narrows** → `_meta.scope_mixing_narrowed` with `{ref, kept_as, dropped_mention}`
   - **scope-ambiguity annotations** → `_meta.scope_ambiguity_annotated` with `{ref, family, in_scope_members}`

**Stage 2.3 — Feature strictness (`monitor_feature`)**
1. Spawn one `monitor_feature` sub-agent (prompt from `agents/monitor_feature.md`) with `out_dir/topics/`, `out_dir/scope.json`, `out_dir/verification_existence.md`, and `out_dir/verification_scope.md`. **Source of `{feature_strictness_criteria}`**: if the user passed the optional `feature_strictness_criteria` input (see Inputs section), the main agent substitutes it verbatim into the placeholder. Otherwise, the main agent leaves the placeholder empty and the monitor falls back to its built-in default 6-criterion test (defined in `agents/monitor_feature.md` under "Default strictness test"). There is no separate per-feature criteria file — feature-specific strictness rules live entirely in the user-supplied input or in the monitor's default test.
2. Wait for `out_dir/verification_feature.md` and the verdict (`GREEN` / `AMBER` / `RED`).
3. If `RED` (a topic loses majority of entries or a headline subfeature itself fails strictness): re-spawn the relevant researcher(s) with a tightened `topic_prompt` and re-run all three stages, subject to the phase-level re-spawn budget (see end of Phase 2). **The re-spawn prompt MUST embed the offending refs / failing-strictness items from the punch-list verbatim, with an explicit instruction `do not re-introduce the following items: …`.**
4. If `AMBER` (recategorize / drop recommendations): the main agent applies the punch-list to the topic JSONs (move entries to canonical buckets, delete entries) while preserving every change in the appropriate per-topic `_meta.*` audit array:
   - **DROP** → `_meta.removed_by_strictness_audit` with `{ref, original_bucket, reason}`
   - **RECATEGORIZE** → `_meta.recategorized_as_other` with `{ref, original_bucket, target_bucket, reason}`
   - **DEDUP (cross-listed)** → `_meta.dedup_canonical` with `{ref, canonical_bucket, also_listed_under_dropped}`
   Apply BEFORE Phase 3.

**Re-spawn budget across the whole phase: at most 2 rounds total.** **Definition of one round**: one re-spawn of any single researcher, regardless of which stage triggered it. The budget is a single counter spanning all three stages combined — re-spawning researcher A from Stage 2.1 and then re-spawning researcher B from Stage 2.3 counts as **2 rounds** (not 1 per stage). **Re-spawning N researchers in a single stage counts as N rounds against the cap of 2.** (E.g. Stage-3 RED requiring re-spawn of `completed_subfeatures` researcher AND `perf_numbers` researcher = 2 rounds, exhausting the budget; the next RED escalates to the user.) If the second round still produces a RED verdict at any stage, escalate to the user rather than looping further.

### Phase 3 — Synthesis (main agent)

1. By the time Phase 3 starts, the must-fix lists from all three stages (`monitor_existence`, `monitor_scope`, `monitor_feature`) have already been applied to the topic JSONs in Phase 2. Re-confirm the JSONs match the punch-lists; spot-fix anything missed.
2. Read `templates/REPORT_template.md` and populate it with the per-topic JSON contents:
   - Title: `# {framework} {feature} on {chip} — Highlighted Report`
   - Header: date + scope statement (verbatim from `scope.json`) + **all three** verification verdicts (existence, scope, feature-strictness).
   - **At-a-Glance Dashboard** table — one row per topic with count + headline insight.
   - One `##` section per topic with a primary table (one row per entity).
   - **Verification Footer** — verbatim-quote / internal-conflict fixes from Stage 1, scope drops from Stage 2, recategorize/drop punch-list from Stage 3, and links to all three `verification_*.md` files.
3. Write `out_dir/REPORT.md`.

### Phase 4 — Hand-off

Print a single short paragraph naming `out_dir/REPORT.md`, all three of `out_dir/verification_existence.md`, `out_dir/verification_scope.md`, `out_dir/verification_feature.md`, and the per-topic JSON files. Note that the JSONs are the dashboard-ready inputs (stable schema across runs) and that every drop/recategorize is recorded in `_meta` for full reversibility.

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
| `topics/topic_json_schema.md` | Required JSON shape every topic file must conform to |
| `scope/chip_scope_map.md` | Vendor → in/out scope SM/CDNA/XPU codes and scope statements |
| `sources/source_playbook.md` | gh / WebFetch / WebSearch / MLPerf / InferenceX recipes |
| `agents/researcher.md` | Per-topic researcher sub-agent prompt template |
| `agents/analyzer_external_repos.md` | Phase-1b external-repo analyzer sub-agent prompt template — runs after `completed_subfeatures` + `kernels_or_components` + `open_issues` are on disk; produces `topics/external_repo_dependencies.json` |
| `agents/monitor_existence.md` | Stage-1 verification sub-agent prompt — every cited PR/issue/URL must really exist on `{framework_repo}`; verbatim quotes must match their source |
| `agents/monitor_scope.md` | Stage-2 verification sub-agent prompt — chip-vendor scope strictness (every entry must target in-scope hardware) |
| `agents/monitor_feature.md` | Stage-3 verification sub-agent prompt — feature-strictness audit (every entry must directly influence `{feature}`'s functionality or performance) |
| `templates/REPORT_template.md` | Synthesized report skeleton |
