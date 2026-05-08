# Collection Runbook

Use this runbook after Phase 0 scope resolution and before analysis. The goal is to collect traceable AMD/ROCm and NVIDIA/CUDA evidence for one framework feature, with enough source detail and stable IDs for the monitors to verify every claim.

Delegated workers follow the role templates under `/home/ziwei/.cursor/skills/rocm-agent/agents/collector_*.md`, `/home/ziwei/.cursor/skills/rocm-agent/agents/subfeature_discovery.md`, and `/home/ziwei/.cursor/skills/rocm-agent/agents/analyzer_*.md`; this file is the shared source playbook of `gh` recipes, `WebFetch` host policy, `WebSearch` guidance, quoting rules, and source policy that all of those roles reuse. Do not re-describe role-specific procedures here; edit the matching role file instead.

Phase 0 chip scope must come from the fenced `rocm_agent_scope.v1` JSON block in `scope.md`. Parse the AMD and NVIDIA objects there and write `aliases`, `product_aliases`, `search_terms`, `in_scope`, `out_of_scope_drops`, and `default_scope_statement` verbatim into `scope.json.chip_scope.{amd,nvidia}`. Hardware query terms come only from explicit `search_terms`; product identifiers that appear only in `in_scope`, `default_scope_statement`, or `product_aliases` are not searchable. If the user passes `amd_hw_focus` or `nv_hw_focus`, match it against `product_aliases` or `search_terms` and write a separate `effective_scope_statement` that records the narrowed scope, but append the focus value to search queries only when that exact value is present in `search_terms`. Do not modify `default_scope_statement` or invent new chip generations or hardware codes here.

## 1. Subfeature Anchoring Rule

`subfeatures.json` must exist before any collector runs, and every retained subfeature must have at least one verified framework-side anchor: a doc URL, config/API symbol, file path, code symbol, or verified PR/issue. Collectors and analyzers must reuse the canonical subfeature names from `subfeatures.json` verbatim. The discovery procedure (input order, doc and repo passes, anchor types, output schema) lives in `/home/ziwei/.cursor/skills/rocm-agent/agents/subfeature_discovery.md`; the schema lives in `/home/ziwei/.cursor/skills/rocm-agent/schemas.md`.

## 2. Discover Docs, APIs, Config, And Code Paths

Use framework docs first, then repository search.

Framework docs and repo paths to check:

- vLLM: `docs.vllm.ai`, repo `docs/`, `vllm/config.py`, `vllm/engine/`, `vllm/core/`, `vllm/worker/`, `vllm/attention/`, `vllm/model_executor/`.
- SGLang: `docs.sglang.ai`, repo `docs/`, `python/sglang/srt/`, scheduler/runtime/server args, kernels, memory/cache managers.
- TGI: `huggingface.co/docs/text-generation-inference`, repo docs, launcher/router/server config, backend selection, CUDA/ROCm build paths.
- TensorRT-LLM: repo docs, examples, plugin/kernel paths, executor/runtime config.
- llama.cpp: repo docs, examples, `ggml-*` backends, CUDA/HIP build flags, server flags.

Useful code searches (chip terms come from `scope.json.chip_scope.{amd,nvidia}.search_terms`, never hardcoded):

```bash
gh search code --repo {framework_repo} '"{feature}" OR {feature_keyword}'
gh search code --repo {framework_repo} "$(join_or scope.json:.chip_scope.amd.search_terms)"
gh search code --repo {framework_repo} "$(join_or scope.json:.chip_scope.nvidia.search_terms)"
gh search code --repo {framework_repo} '{flag_or_symbol}'
```

When a code result is relevant, record the stable file path and symbol. Prefer code paths that implement dispatch, enablement, fallback, kernel selection, cache behavior, communication, memory management, graph capture, quantization, or benchmark configuration.

Code-path evidence must be pinned. A retained `kind=code` collector row needs `evidence_id`, `repo`, `commit_sha`, `path`, `symbol` or `line_start`/`line_end`, and a GitHub blob `source_url` pinned to that commit. Verify the blob through `gh api repos/{repo}/contents/{path}?ref={commit_sha}` or a live fetch of the pinned blob URL. Do not cite a moving branch path as evidence.

## 3. GitHub Search Recipes

Run framework AMD and NVIDIA passes first. Apply `time_window_days` when useful, but do not drop older merged PRs that are foundational for the feature.

Build the AMD and NVIDIA query keyword lists from `scope.json.chip_scope.{amd,nvidia}.search_terms`, copied from the explicit `search_terms` fields in `scope.md`. Do not derive query terms from `in_scope` prose, `default_scope_statement`, `product_aliases`, or hardcoded chip generations. If the user passes `amd_hw_focus` or `nv_hw_focus`, use `product_aliases` only to validate and group the focus in scope metadata. Append the focus value to the corresponding query only when that exact value is present in the matching side's explicit `search_terms`.

vLLM project-board discovery hint: when `framework` is vLLM or `framework_repo` is `vllm-project/vllm`, treat these vLLM GitHub project boards as high-value indexes for quick candidate discovery:

- AMD board: `https://github.com/orgs/vllm-project/projects/38`
- NVIDIA board: `https://github.com/orgs/vllm-project/projects/31`

Use the board matching the collector side to quickly identify candidate PRs, issues, labels, and recent activity that may not rank well in keyword search. Project-board membership, columns, or status are discovery signals only and are not evidence. Every retained PR or issue still needs `gh pr view` or `gh issue view` verification against `vllm-project/vllm`; do not cite board membership as support for a claim, state, priority, or side classification.

AMD/ROCm framework pass:

```bash
AMD_QUERY="$(join_or scope.json:.chip_scope.amd.search_terms) in:title,body"
gh pr list --repo {framework_repo} --state all \
  --search "$AMD_QUERY" \
  --limit {max_per_collector} \
  --json number,title,state,mergedAt,createdAt,updatedAt,labels,author,url

gh issue list --repo {framework_repo} --state all \
  --search "$AMD_QUERY" \
  --limit {max_per_collector} \
  --json number,title,state,createdAt,updatedAt,labels,author,url
```

NVIDIA/CUDA framework pass:

```bash
NV_QUERY="$(join_or scope.json:.chip_scope.nvidia.search_terms) in:title,body"
gh pr list --repo {framework_repo} --state all \
  --search "$NV_QUERY" \
  --limit {max_per_collector} \
  --json number,title,state,mergedAt,createdAt,updatedAt,labels,author,url

gh issue list --repo {framework_repo} --state all \
  --search "$NV_QUERY" \
  --limit {max_per_collector} \
  --json number,title,state,createdAt,updatedAt,labels,author,url
```

`join_or` produces an OR-joined search expression from a JSON array. The tokens come from explicit `search_terms` in `scope.json.chip_scope`; do not hardcode product or generation names here, and do not scrape product names from prose.

Feature-specific passes:

```bash
gh pr list --repo {framework_repo} --state all \
  --search '"{feature}" OR {subfeature_keyword} in:title,body' \
  --limit {max_per_collector} \
  --json number,title,state,mergedAt,createdAt,updatedAt,labels,author,url

gh issue list --repo {framework_repo} --state all \
  --search '"{feature}" OR {subfeature_keyword} in:title,body' \
  --limit {max_per_collector} \
  --json number,title,state,createdAt,updatedAt,labels,url
```

Backend repo passes use the same pattern, scoped to the verified backend repo and narrowed by feature/subfeature keywords plus vendor keywords.

## 4. Verify Each PR Or Issue

Never rely only on list output. For every PR or issue kept in a collector artifact, run exactly the matching view command and verify state, title, body relevance, files or labels, and dates. Do not blindly run both commands for the same candidate.

```bash
gh pr view {number} --repo {repo} \
  --json number,title,state,mergedAt,closedAt,body,labels,files,author,url

gh issue view {number} --repo {repo} \
  --json number,title,state,closedAt,body,labels,author,url
```

Rules:

- Branch by candidate type: PR candidates use `gh pr view`; issue candidates use `gh issue view`. If the candidate type is unknown, first try `gh pr view`; on a not-found response, try `gh issue view`, then record the resolved type in `kind`.
- `verified_state` must come from the view command, not search snippets.
- Merged PRs should record `MERGED`; open issues should record `OPEN`; unreachable or irrelevant refs are `DROPPED`.
- Use `files` to identify changed framework paths, backend dependencies, kernels, build flags, docs, tests, and benchmark harnesses.
- Keep a short `notes` field explaining why the item affects the requested feature or subfeature.
- Assign a stable `evidence_id` before writing the collector row. Use the format in `schemas.md` `## Stable IDs And Source Pointers`.

## 5. Expand Backend Repos Conservatively

Start with framework evidence, then expand.

Default first-hop candidates:

- AMD/ROCm: `ROCm/ROCm`, `ROCm/hipBLASLt`, `ROCm/composable_kernel`, `ROCm/flash-attention`, `ROCm/Triton`, `ROCm/rccl`, `ROCm/aotriton`, `ROCm/MIOpen`.
- NVIDIA/CUDA: `NVIDIA/cutlass`, `NVIDIA/cudnn-frontend`, `NVIDIA/TensorRT-LLM`, `NVIDIA/nccl`, `NVIDIA/nvshmem`, `flashinfer-ai/flashinfer`, `Dao-AILab/flash-attention`, `triton-lang/triton`.

Expansion is allowed only when one of these points there:

- Framework PR body, issue body, labels, dependency bumps, or changed files.
- Framework docs or release notes naming the backend library.
- Official vendor docs/blogs naming the library in relation to the feature.
- Reproducible third-party benchmark naming the backend path.

Scan framework PR bodies and files for names such as `flash-attn`, `flashinfer`, `cutlass`, `cudnn`, `nccl`, `nvshmem`, `hipblaslt`, `composable_kernel`, `aotriton`, `mori`, `rccl`, `MIOpen`, and `triton`. For each expansion, record `discovered_via` and verify the external repo with `gh pr view`, `gh issue view`, or a specific URL.

Do not expand because a repo is generally important to ROCm or CUDA. It must influence at least one scoped subfeature.

## 6. Use WebFetch Carefully

Use bounded `WebSearch` to discover specific source pages, then `WebFetch` for exact URLs. Fetch a source only after `WebSearch`, docs navigation, GitHub refs, or known hosts identify a concrete URL.

Preferred hosts:

- AMD: `rocm.docs.amd.com`, `rocm.blogs.amd.com`, `community.amd.com/t5/instinct-accelerators`, `developer.amd.com`.
- NVIDIA: `docs.nvidia.com`, `developer.nvidia.com/blog`, `nvidia.com/en-us/data-center`.
- Framework: `docs.vllm.ai`, `docs.sglang.ai`, `huggingface.co/docs/text-generation-inference`, official framework GitHub docs.
- Third-party performance: `mlcommons.org`, `github.com/SemiAnalysisAI/InferenceX`, benchmark repos, framework discussion threads, independent benchmark posts with methodology.

Guidance:

- For official web and third-party performance collectors, run at most 5 query strings per side and keep at most the top 10 candidate URLs per query before URL verification. Prefer host filters using the preferred hosts below.
- Example bounded queries: `site:rocm.docs.amd.com "{feature}" "{framework}"`, `site:developer.nvidia.com/blog "{feature}" "{framework}"`, `site:mlcommons.org "{feature}" "MI300X"`, and `site:github.com/SemiAnalysisAI/InferenceX "{feature}"`.
- Fetch the exact release note, doc section, benchmark page, blog post, discussion, or raw GitHub document.
- Ask for the claim, date/version, hardware, model/config, metric, and limitations.
- Avoid marketing pages unless they include concrete software, hardware, feature, or benchmark claims.
- If `WebFetch` cannot access a source, use another primary source or mark the item unverified and drop it from final claims.

## 7. Third-Party Performance Source Policy

Third-party performance evidence is useful only when it is tied to the requested feature or a subfeature. Set `evidence_tier` to:

- `primary`: reproducible benchmark harnesses, MLPerf or InferenceX results that name framework, model, hardware, dtype, and metric, or framework PRs with attached benchmark output.
- `secondary`: vendor or framework blogs, docs, or release notes with stated methodology but limited reproduction detail.
- `anecdotal`: issue or PR comments, forum posts, or third-party posts without enough detail for reproduction. Do not use alone for high-confidence scored gaps.

The retrieval procedure, comparability checklist, and `entries[]` shape for these sources are owned by `/home/ziwei/.cursor/skills/rocm-agent/agents/collector_third_party_perf.md` and `/home/ziwei/.cursor/skills/rocm-agent/agents/monitor_comparison.md`.

## 8. Quote Requirements

Every non-`gh` source used as evidence needs a short verbatim quote in `entries[*].quote`.

Rules:

- Quote the smallest passage that supports the claim.
- Do not paraphrase inside `quote`.
- Keep quotes short, usually one sentence or one table cell value.
- Preserve enough surrounding context in `notes` to explain relevance.
- If a quote cannot be verified on refetch, drop the claim or lower confidence before analysis.

GitHub PRs and issues do not require `quote`, but the collector must still include `ref`, `source_url`, `verified_state`, and `notes`.

## 9. Collector Output Locations

Collectors write JSON under `{out_dir}/collectors/` (one artifact per role):

- `collectors/framework_amd.json`
- `collectors/framework_nvidia.json`
- `collectors/rocm_stack.json`
- `collectors/nvidia_stack.json`
- `collectors/official_web.json`
- `collectors/third_party_perf.json`

The required `_meta` and `entries[]` field contracts (including `vendor_side` rules, timestamps, `evidence_tier`, and `dropped_unverified`) are defined in `/home/ziwei/.cursor/skills/rocm-agent/schemas.md` (`## Common Collector Artifact`). Per-collector retrieval procedures, query budgets, and side mappings live in the matching role file at `/home/ziwei/.cursor/skills/rocm-agent/agents/collector_{role}.md`.

Cross-collector normalization rules:

- One entry per source claim; use canonical subfeature names from `subfeatures.json` verbatim.
- Every entry carries stable `evidence_id`. Any downstream analysis row cites it through a structured source pointer with `artifact`, `json_pointer`, `evidence_id`, `ref`, `source_url`, and `verified_state`.
- Use `neutral` only in `official_web.json` or `third_party_perf.json` when a source is genuinely vendor-neutral.
- Deduplicate same-source claims unless they support different subfeatures.
- Prefer specific source URLs over search result URLs.
- Place unreachable or quote-drift refs in `_meta.dropped_unverified`, chip/framework/feature scope drops in `_meta.dropped_out_of_scope`, and low-severity or low-signal analysis candidates in `_meta.dropped_below_threshold`.

## 10. Caps And Escalation

Default cap is `max_per_collector=200`. Apply tighter working caps when a query is noisy:

- Keep the top 50 to 100 search hits per query for triage.
- Keep only verified, feature-relevant entries in final artifacts.
- Stop expanding backend repos after 1 to 2 verified repos per side unless evidence clearly points to more.
- Limit WebFetch work to sources that can support a concrete collector entry.

Escalate to the user when:

- The framework repo cannot be resolved.
- The requested feature is too broad to produce anchored subfeatures.
- No AMD or no NVIDIA evidence can be found after framework, backend, and official web passes.
- Required sources are blocked, private, or unavailable.
- Comparable performance evidence is absent and the report would need to rely mainly on anecdotal claims.
- Two monitor remediation rounds still leave high-impact claims unverifiable.
- The host's `gh` CLI is unauthenticated or otherwise unable to run `gh pr view` / `gh issue view`. Collectors and analyzers must not invent or skip verification when `gh` fails; escalate so the user can authenticate.

If escalation is not required but evidence is weak, proceed with lower confidence, record the gap, and surface missing evidence in the monitor audit.
