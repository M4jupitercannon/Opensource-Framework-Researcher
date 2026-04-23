# Default research topics

Five topics, generalized from `~/vllm_research/v2/`. Each topic has a stable name (used as the JSON filename and as the report `##` heading), a prompt template the main agent injects into the researcher sub-agent, and an entry schema.

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
    "hardware_supported": ["SM89", "SM90", "..."]   // entries from scope.in_scope
  }
  ```

---

## 2. `open_issues`

- **report_heading**: `Open Issues`
- **prompt**:
  > For each subfeature of `{feature}` in `{framework}`, find currently OPEN issues in `{framework_repo}` that are relevant on `{chip}` ({scope_statement}). Use `gh issue list --repo {framework_repo} --state open --search '{search-terms}' --json number,title,labels,createdAt,state`. Verify each one is actually open. Drop issues whose hardware is out of scope (record drops in `_meta.dropped_out_of_scope`). Classify each issue as `ep-direct` / `ep-tangential` (or framework analog), and assign a severity (`critical` / `major` / `minor`). Group issues per subfeature; the same issue may appear under multiple subfeatures.
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
