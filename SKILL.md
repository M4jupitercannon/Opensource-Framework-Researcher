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

## Hard rules

1. **Orchestration-only.** The main agent never executes a researcher or monitor runbook itself. It resolves scope, fans out sub-agents, then synthesizes their outputs.
2. **Flat sub-agents.** Researchers and the monitor must NOT call the Agent tool. (Nested sub-agents are not supported.)
3. **Verify before write.** Every PR / issue / URL claim in any topic JSON MUST be live-verified by the producing researcher (via `gh` / `WebFetch`) before the JSON is written. The monitor re-samples but does not substitute.
4. **No q1/q2/q3 labels.** Section headings in the synthesized report use the topic names directly (e.g. `## Completed Subfeatures`, `## Open Issues`, `## Roadmap`).
5. **Required JSON metadata.** Every topic JSON file has a top-level `_meta` block with at least: `scope`, `sources_used`, `verified_at`, `framework_repo`. See `templates/` notes (schema lives in `topics/topic_json_schema.md`).
6. **Scope audit trail.** Items dropped for being out-of-scope are logged in `verification.md` and surfaced in the report's Verification Footer — not silently discarded.

## Workflow

### Phase 0 — Scope resolution (main agent)

1. Read `scope/chip_scope_map.md`. Look up the `chip` argument and derive a scope spec (in-scope SM/CDNA/XPU codes + out-of-scope SKUs to drop + a one-line "scope statement" string for the report header).
2. If `scope_override` is supplied, replace the derived spec.
3. Read `sources/source_playbook.md` and resolve `framework` → `org/repo` for the GitHub queries (use `gh_repo_override` if given).
4. Create `out_dir/` and write `out_dir/scope.json` with: `{chip, framework, framework_repo, feature, in_scope, out_of_scope_drops, scope_statement, generated_at}`.

### Phase 1 — Parallel research (main agent fans out)

1. Read `topics/default_topics.md` (or use the user's `topics` override).
2. **In a single message, spawn one `researcher` sub-agent per topic** (parallel tool calls). Each researcher's prompt is built from `agents/researcher.md` + the per-topic spec from `default_topics.md` + the resolved scope + the source playbook + the target output path `out_dir/topics/{topic_name}.json`.
3. Wait for all researchers to return. Each returns: file path written, entry count, count of `gh`/`WebFetch` verifications performed.
4. If any researcher reports an error, surface it and stop before Phase 2.

### Phase 2 — Verification (serial)

1. Spawn one `monitor` sub-agent (prompt from `agents/monitor.md`) with `out_dir/topics/` and `out_dir/scope.json` as inputs.
2. Wait for `out_dir/verification.md` to be written and the monitor's verdict (`GREEN` / `YELLOW` / `RED` + must-fix list).
3. If verdict is `RED`: re-spawn the relevant researcher(s) to redo their topics, then re-run the monitor. Loop at most twice.

### Phase 3 — Synthesis (main agent)

1. Apply YELLOW/RED must-fixes (drop out-of-scope items, reconcile internal conflicts) by editing the topic JSONs directly.
2. Read `templates/REPORT_template.md` and populate it with the per-topic JSON contents:
   - Title: `# {framework} {feature} on {chip} — Highlighted Report`
   - Header: date + scope statement (verbatim from `scope.json`) + verification verdict.
   - **At-a-Glance Dashboard** table — one row per topic with count + headline insight.
   - One `##` section per topic with a primary table (one row per entity).
   - **Verification Footer** — dropped items, internal conflict reconciliations, link to `verification.md`.
3. Write `out_dir/REPORT.md`.

### Phase 4 — Hand-off

Print a single short paragraph naming `out_dir/REPORT.md`, `out_dir/verification.md`, and the per-topic JSON files. Note that the JSONs are the dashboard-ready inputs (stable schema across runs).

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
| `topics/default_topics.md` | The 5 default research topics + their prompts and entry schemas |
| `topics/topic_json_schema.md` | Required JSON shape every topic file must conform to |
| `scope/chip_scope_map.md` | Vendor → in/out scope SM/CDNA/XPU codes and scope statements |
| `sources/source_playbook.md` | gh / WebFetch / WebSearch / MLPerf / InferenceX recipes |
| `agents/researcher.md` | Per-topic researcher sub-agent prompt template |
| `agents/monitor.md` | Verification sub-agent prompt template |
| `templates/REPORT_template.md` | Synthesized report skeleton |
