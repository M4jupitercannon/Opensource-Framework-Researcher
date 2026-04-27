# Default research topics

Six topics, generalized from `~/vllm_research/v2/`. Each topic has a stable name (used as the JSON filename and as the report `##` heading), a prompt template the main agent injects into the researcher sub-agent, and an entry schema.

The main agent passes one topic per researcher sub-agent. To override, the user supplies a `topics:` argument that is either a subset of these names or a list of custom topic objects of the same shape.

Section heading rule: when the report is synthesized, the `report_heading` field is what becomes the `##` heading — never `Q1`/`Q2`/etc.

---

## 1. `completed_subfeatures`

- **report_heading**: `Completed Subfeatures`
- **prompt** (template, `{chip}` / `{framework}` / `{feature}` / `{framework_repo}` / `{scope_statement}` substituted):
  > Identify the subfeatures of `{feature}` that have already been **merged** into `{framework}` and are usable on `{chip}` ({scope_statement}). For each subfeature, list every merged PR you can find in `{framework_repo}` whose changes contributed to that subfeature. Verify each PR's merged state and merge date with `gh pr view {N} --repo {framework_repo} --json number,title,state,mergedAt`. Include only items in scope. Group PRs under a single subfeature even if there were many follow-on fixes; pick a short canonical subfeature name and a 1–2 sentence description. Output the list as JSON conforming to the entry schema below.
- **entry schema**:
  ```jsonc
  {
    "name": "string — short canonical subfeature name",
    "description": "string — 1–2 sentences explaining what this subfeature does",
    "prs": [
      {"number": 12345, "title": "string", "merged_at": "ISO-8601", "verified_state": "MERGED"}
    ],
    "status": "string — e.g. 'production-ready', 'experimental', 'CI-tested but off by default'",
    "hardware_supported": ["SM90", "SM100", "..."]   // entries from scope.in_scope
  }
  ```

---

## 2. `open_issues`

- **report_heading**: `Open Issues`
- **prompt**:
  > For each subfeature of `{feature}` in `{framework}`, find currently OPEN issues in `{framework_repo}` that are relevant on `{chip}` ({scope_statement}). Use `gh issue list --repo {framework_repo} --state open --search '{search-terms}' --json number,title,labels,createdAt,state`. Verify each one is actually open. Drop issues whose hardware is out of scope (record drops in `_meta.dropped_out_of_scope`). Classify each issue as `ep-direct` / `ep-tangential` (or framework analog), and assign a severity (`critical` / `major` / `minor`). Group issues per subfeature; the same issue may appear under multiple subfeatures.
- **subfeature-name rule (cross-file consistency)**: `entries[*].subfeature` MUST match a canonical name from `completed_subfeatures.json` `entries[*].name` **verbatim** (same case, same spelling). The Phase-1b analyzer and the report's external-repo derivation rule both rely on this exact-match contract. If a Phase-1a researcher cannot map an issue to an existing canonical subfeature, it should either (a) defer the entry until `completed_subfeatures.json` lists the appropriate name, or (b) bucket it under a single `"(cross-cutting)"` literal — never invent a new subfeature name here.
- **entry schema** (one entry per subfeature):
  ```jsonc
  {
    "subfeature": "string — must match a name from completed_subfeatures.json when possible",
    "open_count": 12,
    "direct_count": 10,
    "tangential_count": 2,
    "issues": [
      {
        "number": 12345,
        "title": "string",
        "createdAt": "YYYY-MM-DD",
        "labels": ["bug", "..."],
        "severity": "critical|major|minor",
        "category": "direct|tangential"
      }
    ]
  }
  ```

---

## 3. `roadmap`

- **report_heading**: `Roadmap`
- **prompt**:
  > Find the canonical "roadmap" issue/page for `{framework}` (typically a tracking issue labelled `roadmap` or `tracking`). Verify it with `gh issue view`. Extract every roadmap item that touches `{feature}` on `{chip}` ({scope_statement}). For each item, classify as `in-flight` (open PRs already exist) / `planned` (no PR yet but on the roadmap) / `stretch` (explicitly experimental or marked tentative). Link open PRs and RFCs (verify each with `gh`). Also list recent (≤180 days) RFCs whose body discusses `{feature}` even if not on the official roadmap.
- **entry schema** has two top-level lists, `roadmap_items` and `recent_rfcs`. Roadmap item shape:
  ```jsonc
  {
    "name": "string",
    "category": "in-flight|planned|stretch",
    "description_verbatim": "string — copied from the roadmap source",
    "linked_prs": [{"number": 1, "title": "string", "state": "OPEN|MERGED"}],
    "linked_rfcs": [{"number": 1, "title": "string", "state": "OPEN"}],
    "target_arch": "string",
    "priority": "high|medium-high|medium|low|stretch"
  }
  ```
  RFC entry shape:
  ```jsonc
  {
    "number": 1,
    "title": "string",
    "state": "OPEN|CLOSED",
    "created_at": "ISO-8601",
    "label": "RFC|...",
    "feature_relevance": "string",
    "chip_relevance": "string"
  }
  ```

---

## 4. `perf_numbers`

- **report_heading**: `Performance Numbers`
- **prompt**:
  > For each subfeature of `{feature}` in `{framework}` on `{chip}`, find published performance numbers — typically from the body of merged perf PRs, or from vendor blogs / MLPerf submissions / SemiAnalysis InferenceX. EVERY number must be supported by a verbatim source quote from the cited URL/PR body. Cross-check by fetching the cited source (`gh pr view --json body` or `WebFetch`) and pasting the relevant passage into `source_quote`. Drop entries whose hardware is out of scope.
- **entry schema**:
  ```jsonc
  {
    "subfeature": "string",
    "metric": "string — what is being measured (e.g. 'decode tok/s')",
    "baseline": "string — what is the baseline (model + hw + config)",
    "improved": "string — what is the improved variant (and config)",
    "delta": "string — concrete improvement (% or absolute)",
    "source": {
      "type": "pr|blog|mlperf|inferencex|docs",
      "ref": "PR #12345 | URL",
      "repo_or_host": "vllm-project/vllm | docs.nvidia.com | ..."
    },
    "source_quote": "string — VERBATIM passage from the source"
  }
  ```

---

## 5. `kernels_or_components`

- **report_heading**: `Kernels & Components`
- **prompt**:
  > List the GPU kernels (or vendor-analog low-level components — e.g. AMD wmma, Intel XMX, TPU MXU) that lie on the critical path of `{feature}` in `{framework}` on `{chip}`. Group them into categories that fit the feature (for MoE: grouped-GEMM / MoE-compute / communication / quantization; for attention: attention-prefill / attention-decode / KV-page / quant). For each kernel, cite the kernel-library version (DeepGEMM, CUTLASS, FlashInfer, hipBLASLt, …) and the integrating PRs. Verify PRs with `gh`.
- **entry schema** (top-level is `{categories: [{name, kernels: [...]}, ...]}`); per-kernel:
  ```jsonc
  {
    "name": "string — kernel/component name",
    "category": "string — e.g. 'grouped-GEMM' / 'communication' / 'quantization'",
    "library": "string — DeepGEMM v2 / CUTLASS 4.x / FlashInfer >=0.4 / NCCL / NVSHMEM / ...",
    "prs": [{"number": 1, "title": "string", "verified_state": "MERGED|OPEN"}],
    "hardware": ["SM90", "SM100", "..."],
    "notes": "string — performance characteristic, alternatives, known issues"
  }
  ```

---

## 6. `external_repo_dependencies`

- **report_heading**: `External Repo Dependencies`
- **prerequisites**: `completed_subfeatures.json`, `kernels_or_components.json`, `open_issues.json` must already exist on disk. This topic is produced by the analyzer role (`agents/analyzer_external_repos.md`), not a generic researcher — see SKILL.md Phase 1b.
- **note**: This topic is produced by the Phase-1b analyzer; the prompt template below is informational. The authoritative procedure lives in `agents/analyzer_external_repos.md` and is what the orchestrator actually injects.
- **prompt** (template, `{chip}` / `{framework}` / `{feature}` / `{framework_repo}` / `{scope_statement}` substituted):
  > For each completed subfeature of `{feature}` in `{framework}` on `{chip}` ({scope_statement}), identify the **external open-source repositories** that subfeature depends on or contributes back to (e.g. kernel libraries like `deepseek-ai/DeepGEMM`, `deepseek-ai/DeepEP`, `flashinfer-ai/flashinfer`, `ROCm/mori`, `NVIDIA/cutlass`, `NVIDIA/nccl`, `NVIDIA/nvshmem`). You will be given the already-produced `completed_subfeatures.json`, `kernels_or_components.json`, and `open_issues.json` as inputs — read those files first. Discover external-repo names by (a) re-fetching each framework PR body via `gh pr view {N} --repo {framework_repo} --json body,files` and scanning for repo slugs, submodule changes, and `requirements*` bumps; (b) reading the `library` field of each kernel under `kernels_or_components.json`; (c) scanning open-issue bodies in `open_issues.json` for outbound references. For every external-repo PR/issue ref you find, run `gh pr view {N} --repo {ext_org/ext_repo}` or `gh issue view {N} --repo {ext_org/ext_repo}` to verify it exists, get its title, and confirm its state. Drop any ref that fails verification. Group results by subfeature (entry per subfeature), with sub-grouping by external repo.
- **entry schema** (one entry per subfeature; subfeature names inherited verbatim from `completed_subfeatures.json`):
  ```jsonc
  {
    "subfeature": "string — must match a name from completed_subfeatures.json",
    "external_repos": [
      {
        "repo": "string — org/repo slug, e.g. 'deepseek-ai/DeepEP'",
        "library_name": "string — short name as cited in framework PR bodies, e.g. 'DeepEP'",
        "pr_count": 6,
        "issue_count": 5,
        "prs": [
          {"number": 42, "title": "string", "verified_state": "MERGED|OPEN|CLOSED"}
        ],
        "issues": [
          {"number": 17, "title": "string", "verified_state": "OPEN|CLOSED"}
        ],
        "discovered_via": ["framework-pr-body:#12345", "kernels_or_components:DeepEP", "open_issues:#67890"]
      }
    ],
    "totals": { "external_repo_count": 2, "pr_count": 9, "issue_count": 10 }
  }
  ```

---

## Custom topic format

If the user passes a custom topic, it must follow:

```jsonc
{
  "name": "snake_case_id",                // becomes JSON filename
  "report_heading": "Title Case Heading", // becomes report ## heading
  "prompt": "string with {chip}/{framework}/{feature}/{framework_repo}/{scope_statement} placeholders",
  "entry_schema": { /* JSON-schema-ish shape; researcher will follow it */ }
}
```
