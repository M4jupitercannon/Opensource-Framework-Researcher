# ROCm-agent Schemas

This file defines the stable artifact contracts for ROCm-agent runs. Artifacts should be strict JSON unless explicitly marked as Markdown monitor output. Use ISO-8601 timestamps, repository refs as `org/repo#number`, and URLs for web sources. Machine-checkable JSON Schema definitions live in `/home/ziwei/.cursor/skills/rocm-agent/json-schemas/artifacts.schema.json`; after writing any JSON artifact, validate the artifact against that file when a JSON Schema validator is available, and otherwise perform the same required-field checks manually before handing off.

## Common Rules

- Required metadata appears in `_meta` for every JSON artifact.
- `vendor_side` values: `AMD`, `NVIDIA`, `neutral`. Use `neutral` only in `official_web.json` or `third_party_perf.json` when a source is genuinely vendor-neutral; side-specific collector files must use `AMD` or `NVIDIA`.
- `side` values: `AMD`, `NVIDIA`.
- `support_state` values: `supported`, `experimental`, `missing`, `broken`.
- `enablement_state` values: `default_on`, `flag_gated`, `unavailable`, `unknown`.
- `confidence` values: `high`, `medium`, `low`.
- `verified_state` values: `MERGED`, `OPEN`, `CLOSED`, `PUBLISHED`, `N/A`, `DROPPED`.
- Score dimensions are only `feature_relevance` and `performance_relevance`.
- Drop unreachable or unverifiable claims into `_meta.dropped_unverified`; do not keep them as report evidence.
- Drop valid but out-of-chip/framework/feature-scope claims into `_meta.dropped_out_of_scope`; drop valid but below-threshold analysis rows into `_meta.dropped_below_threshold`. Use empty arrays when nothing was dropped. Do not overload `_meta.dropped_unverified` for scope or severity-threshold decisions.
- Every analysis artifact, `dashboard/dashboard_data.json`, and `dashboard/report_citations.json` must include `_meta.framework`, `_meta.framework_repo`, `_meta.feature`, `_meta.dropped_unverified`, `_meta.dropped_out_of_scope`, and `_meta.dropped_below_threshold`.
- Use `evidence_tier` only for source strength (`primary`, `secondary`, `anecdotal`). Use `comparability_note` or a structured `comparability` block for methodology completeness; do not overload comparability with evidence tier values.

## Stable IDs And Source Pointers

Every artifact that can be cited must expose stable IDs. These IDs are part of the public contract and must not depend on array position.

- Collector entries require `evidence_id`. Format: `<collector_name>:<normalized-ref-or-url-hash>:<subfeature-slug>`. It must remain stable across reruns while the same source claim is retained.
- Analysis entries and dashboard rows require `row_id`. Format: `<artifact-kind>:<subfeature-slug>:<short-hash-of-key-fields>`.
- Analysis `evidence_refs[]` MUST contain source pointers, not bare strings. Each item has `{ "artifact": "collectors/framework_amd.json", "json_pointer": "/entries/0", "evidence_id": "framework_amd_collector:vllm-project-vllm-12345:automatic-prefix-caching", "ref": "vllm-project/vllm#12345", "source_url": "https://github.com/vllm-project/vllm/pull/12345", "verified_state": "MERGED" }`.
- Dashboard rows carry `source_row_ids[]` and `evidence_refs[]` source pointers inherited from analysis rows. Dashboard rows also carry `source_json_pointers[]` when they copy full prose from upstream artifacts.
- `dashboard/report_citations.json` refs must include exact `artifact`, `json_pointer`, `evidence_id` or `row_id`, `ref`, `source_url`, `verified_state`, `evidence_tier`, and `quote_sha256` when a quote is non-empty. Array-index strings such as `dashboard_data.tables.score_rows[0]` are not sufficient without the row's `row_id`.
- When a row cites code evidence, the source pointer must target a collector entry with `kind="code"` and the code-evidence fields below; raw repository paths are not citeable.
- Monitors verify JSON Pointers and stable IDs. A report or manifest that can only be reconciled by array position is not publishable.

## Agent role mapping

Each artifact below is produced by exactly one role. When editing a schema, also check the matching role file and keep the field set in sync. The orchestration order is defined in `/home/ziwei/.cursor/skills/rocm-agent/SKILL.md`.

- `scope.json` -> main agent (Phase 0; not a delegated role).
- `subfeatures.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/subfeature_discovery.md`.
- `collectors/framework_amd.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/collector_framework_amd.md`.
- `collectors/framework_nvidia.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/collector_framework_nvidia.md`.
- `collectors/rocm_stack.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/collector_rocm_stack.md`.
- `collectors/nvidia_stack.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/collector_nvidia_stack.md`.
- `collectors/official_web.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/collector_official_web.md`.
- `collectors/third_party_perf.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/collector_third_party_perf.md`.
- `analysis/subfeature_influence_matrix.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/analyzer_subfeature_influence.md`.
- `analysis/backend_repo_map.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/analyzer_backend_repo_map.md`.
- `analysis/stability_gaps.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/analyzer_stability_gaps.md`.
- `analysis/performance_kernel_gaps.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/analyzer_performance_kernel_gaps.md`.
- `analysis/criteria_scores.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/analyzer_criteria_scores.md`.
- `dashboard/dashboard_data.json` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/analyzer_dashboard_data.md`.
- `monitors/monitor_evidence.md` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/monitor_evidence.md` (initial pass and post-synthesis rerun).
- `monitors/monitor_scope.md` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/monitor_scope.md`.
- `monitors/monitor_comparison.md` -> `/home/ziwei/.cursor/skills/rocm-agent/agents/monitor_comparison.md`.
- `dashboard/report_citations.json` -> main agent (drafted in Phase 4 alongside `REPORT.md`); the post-synthesis rerun that re-verifies it is `/home/ziwei/.cursor/skills/rocm-agent/agents/monitor_evidence.md`.
- `remediation_state.json` -> main agent (created in Phase 0, updated before every monitor run and after every remediation round).

## scope.json

Records resolved user inputs, framework repository, limits, and run location.

```jsonc
{
  "_meta": {
    "schema": "scope.v1",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601"
  },
  "inputs": {
    "framework": "vLLM",
    "feature": "prefix caching",
    "framework_repo_override": null,
    "amd_hw_focus": "MI300X",
    "nv_hw_focus": "H100",
    "out_dir": "/home/user/research/rocm-agent/vllm_prefix-caching/2026-05-06",
    "time_window_days": 365,
    "max_per_collector": 200
  },
  "resolved": {
    "framework_repo": "vllm-project/vllm",
    "framework_repo_source": "built_in_map",
    "feature_slug": "prefix-caching",
    "run_id": "vllm_prefix-caching_2026-05-06",
    "chip_scope_source": "scope.md#rocm_agent_scope.v1"
  },
  "chip_scope": {
    "amd": {
      "default_scope_statement": "VERBATIM AMD default_scope_statement parsed from scope.md rocm_agent_scope.v1 JSON block",
      "effective_scope_statement": "Optional narrowed statement when amd_hw_focus narrows the default scope",
      "in_scope": ["VERBATIM in_scope entries parsed from scope.md rocm_agent_scope.v1 vendors.amd"],
      "out_of_scope_drops": ["VERBATIM out_of_scope_drops parsed from scope.md rocm_agent_scope.v1 vendors.amd"],
      "aliases": ["VERBATIM aliases parsed from scope.md rocm_agent_scope.v1 vendors.amd"],
      "product_aliases": {
        "CDNA3": ["MI300X", "MI300A", "MI325X"]
      },
      "search_terms": ["VERBATIM search_terms parsed from scope.md rocm_agent_scope.v1 vendors.amd"]
    },
    "nvidia": {
      "default_scope_statement": "VERBATIM NVIDIA default_scope_statement parsed from scope.md rocm_agent_scope.v1 JSON block",
      "effective_scope_statement": "Optional narrowed statement when nv_hw_focus narrows the default scope",
      "in_scope": ["VERBATIM in_scope entries parsed from scope.md rocm_agent_scope.v1 vendors.nvidia"],
      "out_of_scope_drops": ["VERBATIM out_of_scope_drops parsed from scope.md rocm_agent_scope.v1 vendors.nvidia"],
      "aliases": ["VERBATIM aliases parsed from scope.md rocm_agent_scope.v1 vendors.nvidia"],
      "product_aliases": {
        "SM90": ["H100", "H200", "H20", "GH200"]
      },
      "search_terms": ["VERBATIM search_terms parsed from scope.md rocm_agent_scope.v1 vendors.nvidia"]
    }
  },
  "built_in_framework_repo_map": {
    "vLLM": "vllm-project/vllm",
    "SGLang": "sgl-project/sglang",
    "TGI": "huggingface/text-generation-inference",
    "TensorRT-LLM": "NVIDIA/TensorRT-LLM",
    "llama.cpp": "ggerganov/llama.cpp"
  },
  "source_policy": {
    "require_verified_refs": true,
    "max_recollection_rounds": 2,
    "allowed_score_dimensions": ["feature_relevance", "performance_relevance"]
  }
}
```

Phase 0 must derive `chip_scope` by parsing the fenced `rocm_agent_scope.v1` JSON block in `scope.md`. Copy `aliases`, `product_aliases`, `search_terms`, `in_scope`, `out_of_scope_drops`, and `default_scope_statement` verbatim from that block for AMD and NVIDIA. Search queries must use only the explicit `search_terms` field; product identifiers in `in_scope`, `default_scope_statement`, or `product_aliases` are descriptive context, not implicit search terms. Hardware focus inputs may produce an `effective_scope_statement` after matching `product_aliases` or `search_terms`, but a focus value may be appended to queries only when that exact value is present in `search_terms`. Product aliases are validation and grouping data unless they also appear in `search_terms`. This skill must not maintain a separate chip-generation map.

## remediation_state.json

Main-agent-owned state for bounded remediation. Monitor workers read this file and record its values in audit output; they do not infer run phase or round count from prose.

```jsonc
{
  "_meta": {
    "schema": "remediation_state.v1",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "prefix caching",
    "created_at": "ISO-8601",
    "updated_at": "ISO-8601"
  },
  "max_recollection_rounds": 2,
  "recollection_rounds_used": 0,
  "rounds_remaining": 2,
  "current_monitor": "monitor_evidence",
  "current_monitor_run_phase": "initial",
  "history": [
    {
      "round": 0,
      "monitor": "monitor_evidence",
      "run_phase": "initial",
      "verdict": "GREEN",
      "checked_at": "ISO-8601",
      "blocking_findings": 0,
      "non_blocking_caveats": 0,
      "notes": "Initial pass."
    }
  ],
  "blocking_findings_open": [],
  "allowed_yellow_caveats": []
}
```

Rules:
- The main agent increments `recollection_rounds_used` only when it recollects, respawns, or rewrites an upstream artifact in response to a monitor punch list.
- Before every monitor run, set `current_monitor` and `current_monitor_run_phase` explicitly. Allowed phases are `initial` and `post_synthesis`.
- Monitors must copy `recollection_rounds_used` and `rounds_remaining` from this file into their audit headers. A missing or stale file is a RED finding.
- Publish requires `history` to reconcile with all monitor sections and `rounds_remaining = max_recollection_rounds - recollection_rounds_used`.

## subfeatures.json

Taxonomy discovered before collectors run. Each subfeature must have at least one framework-side anchor.

```jsonc
{
  "_meta": {
    "schema": "subfeatures.v1",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "prefix caching",
    "verified_at": "ISO-8601",
    "dropped_unverified": [],
    "dropped_out_of_scope": [],
    "dropped_below_threshold": []
  },
  "subfeatures": [
    {
      "name": "automatic prefix caching",
      "description": "Reuses KV cache across requests sharing a prompt prefix.",
      "framework_anchors": [
        {
          "type": "doc",
          "ref": "https://docs.vllm.ai/...",
          "verified_state": "PUBLISHED"
        },
        {
          "type": "code",
          "ref": "vllm/core/block_manager.py",
          "verified_state": "N/A"
        },
        {
          "type": "pr",
          "ref": "vllm-project/vllm#1234",
          "verified_state": "MERGED"
        }
      ],
      "applicable_sides": ["AMD", "NVIDIA"],
      "topic_tags": ["memory", "cache-management", "perf"]
    }
  ]
}
```

## Common Collector Artifact

Used by `collectors/framework_amd.json`, `framework_nvidia.json`, `rocm_stack.json`, `nvidia_stack.json`, `official_web.json`, and `third_party_perf.json`.

```jsonc
{
  "_meta": {
    "schema": "collector.v1",
    "collector_name": "framework_amd_collector",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "prefix caching",
    "vendor_side": "AMD",
    "sources_used": ["gh", "WebFetch"],
    "verified_at": "ISO-8601",
    "claim_count": 1,
    "dropped_unverified": [
      {
        "ref": "vllm-project/vllm#99999",
        "reason": "unreachable or state mismatch"
      }
    ],
    "dropped_out_of_scope": [],
    "dropped_below_threshold": []
  },
  "entries": [
    {
      "evidence_id": "framework_amd_collector:vllm-project-vllm-12345:automatic-prefix-caching",
      "subfeature": "automatic prefix caching",
      "vendor_side": "AMD",
      "kind": "pr",
      "ref": "vllm-project/vllm#12345",
      "title": "Enable prefix caching on ROCm",
      "state": "MERGED",
      "verified_state": "MERGED",
      "created_at": "ISO-8601 or null",
      "updated_at": "ISO-8601 or null",
      "merged_at": "ISO-8601 or null",
      "closed_at": "ISO-8601 or null",
      "published_at": "ISO-8601 or null",
      "activity_at": "ISO-8601 - newest relevant activity timestamp used for recent activity counts",
      "hardware": ["MI300X"],
      "evidence_tier": "primary",
      "topic_tags": ["kernel", "memory", "perf"],
      "quote": "",
      "source_url": "https://github.com/vllm-project/vllm/pull/12345",
      "discovered_via": ["query:rocm prefix caching"],
      "notes": "Short analyst note."
    }
  ]
}
```

For `kind="code"` entries, these fields are also required:

```jsonc
{
  "kind": "code",
  "repo": "vllm-project/vllm",
  "commit_sha": "full 40-character commit SHA or release tag SHA",
  "path": "vllm/attention/backends/rocm.py",
  "symbol": "RocmAttentionBackend",
  "line_start": 10,
  "line_end": 80,
  "source_url": "https://github.com/vllm-project/vllm/blob/<commit_sha>/vllm/attention/backends/rocm.py#L10-L80",
  "verified_state": "N/A"
}
```

Code evidence is citeable only when `repo`, `commit_sha`, `path`, `source_url`, and either `symbol` or `line_start`/`line_end` are populated and the collector verified the blob URL or `gh api repos/{repo}/contents/{path}?ref={commit_sha}`. A moving branch URL or raw file path is not stable evidence.

### Third-party Performance Collector Extension

`collectors/third_party_perf.json` uses the common `collector.v1` shape above and may add these methodology fields to each `entries[]` item. They are declared extensions for this collector only; other collectors should not emit them unless their role template explicitly says so.

```jsonc
{
  "model": "Llama3-70B or unspecified",
  "dtype": "bf16",
  "batch_size": "decode batch 8",
  "sequence_lengths": "prompt 2048, generation 256",
  "feature_flags": "prefix caching on, paged attention enabled",
  "warmup": "5 warmup iterations or unspecified",
  "metric": "decode tok/s",
  "hardware_generation": "MI300X CDNA3 vs H100 SM90",
  "power_clock_policy": "clock locked, default power, or unspecified",
  "evidence_type": "microbenchmark | end_to_end",
  "comparability_note": "Short methodology caveat or pass note."
}
```

Third-party benchmark rows with missing methodology may still be retained as `evidence_tier="anecdotal"` only when they are useful context and are clearly caveated. They must not be the sole support for high-confidence scored gaps or headline quantitative deltas.

## subfeature_influence_matrix.json

Maps every subfeature to framework evidence and backend repos on both sides.

```jsonc
{
  "_meta": {
    "schema": "subfeature_influence_matrix.v1",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "prefix caching",
    "verified_at": "ISO-8601",
    "dropped_unverified": [],
    "dropped_out_of_scope": [],
    "dropped_below_threshold": []
  },
  "matrix": [
    {
      "row_id": "subfeature_influence:automatic-prefix-caching",
      "subfeature": "automatic prefix caching",
      "amd": {
        "framework_prs": [
          {
            "ref": "vllm-project/vllm#12345",
            "verified_state": "MERGED"
          }
        ],
        "framework_issues": [
          {
            "ref": "vllm-project/vllm#23456",
            "verified_state": "OPEN"
          }
        ],
        "backend_repos": ["ROCm/composable_kernel", "ROCm/aotriton"],
        "evidence_refs": [
          {
            "artifact": "collectors/framework_amd.json",
            "json_pointer": "/entries/0",
            "evidence_id": "framework_amd_collector:vllm-project-vllm-12345:automatic-prefix-caching",
            "ref": "vllm-project/vllm#12345",
            "source_url": "https://github.com/vllm-project/vllm/pull/12345",
            "verified_state": "MERGED"
          }
        ],
        "support_rationale": "AMD support is experimental because the verified framework PR is merged but docs still require an opt-in flag.",
        "enablement_rationale": "AMD enablement is flag_gated because the verified entry names the required server flag."
      },
      "nvidia": {
        "framework_prs": [
          {
            "ref": "vllm-project/vllm#22222",
            "verified_state": "MERGED"
          }
        ],
        "framework_issues": [],
        "backend_repos": ["flashinfer-ai/flashinfer", "Dao-AILab/flash-attention"],
        "evidence_refs": [
          {
            "artifact": "collectors/framework_nvidia.json",
            "json_pointer": "/entries/0",
            "evidence_id": "framework_nvidia_collector:vllm-project-vllm-22222:automatic-prefix-caching",
            "ref": "vllm-project/vllm#22222",
            "source_url": "https://github.com/vllm-project/vllm/pull/22222",
            "verified_state": "MERGED"
          }
        ],
        "support_rationale": "NVIDIA support is supported because a verified framework PR and docs identify the default kernel path.",
        "enablement_rationale": "NVIDIA enablement is default_on because verified docs state the backend is selected without an extra flag."
      },
      "neutral_context_refs": [],
      "support_state": {
        "amd": "experimental",
        "nvidia": "supported"
      },
      "enablement_state": {
        "amd": "flag_gated",
        "nvidia": "default_on"
      },
      "evidence_refs": [
        {
          "artifact": "collectors/framework_amd.json",
          "json_pointer": "/entries/0",
          "evidence_id": "framework_amd_collector:vllm-project-vllm-12345:automatic-prefix-caching",
          "ref": "vllm-project/vllm#12345",
          "source_url": "https://github.com/vllm-project/vllm/pull/12345",
          "verified_state": "MERGED"
        },
        {
          "artifact": "collectors/framework_nvidia.json",
          "json_pointer": "/entries/0",
          "evidence_id": "framework_nvidia_collector:vllm-project-vllm-22222:automatic-prefix-caching",
          "ref": "vllm-project/vllm#22222",
          "source_url": "https://github.com/vllm-project/vllm/pull/22222",
          "verified_state": "MERGED"
        }
      ]
    }
  ]
}
```

`backend_repos[]` contains repo slugs only. Do not attach `verified_state` to those strings; the verification backing each repo slug belongs in side-specific `evidence_refs[]`. Neutral evidence may appear only in `neutral_context_refs[]` unless the retained source explicitly names AMD or NVIDIA behavior for the subfeature; neutral rows must not be used to infer parity on both sides without side-specific rationale.

## backend_repo_map.json

Maps subfeatures to likely owning backend repositories.

```jsonc
{
  "_meta": {
    "schema": "backend_repo_map.v1",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "prefix caching",
    "verified_at": "ISO-8601",
    "dropped_unverified": [],
    "dropped_out_of_scope": [],
    "dropped_below_threshold": []
  },
  "entries": [
    {
      "row_id": "backend_repo_map:automatic-prefix-caching:AMD",
      "subfeature": "automatic prefix caching",
      "side": "AMD",
      "primary_owner": "ROCm/composable_kernel",
      "co_owners": ["ROCm/aotriton", "vllm-project/vllm"],
      "integration_surface": "vLLM custom op via Triton lowering on AMD",
      "confidence": "high",
      "rationale": "Verified framework and backend refs both name the AMD attention lowering path.",
      "notes": "Optional caveat about inferred ownership.",
      "evidence_refs": [
        {
          "artifact": "analysis/subfeature_influence_matrix.json",
          "json_pointer": "/matrix/0",
          "row_id": "subfeature_influence:automatic-prefix-caching",
          "ref": "vllm-project/vllm#12345",
          "source_url": "https://github.com/vllm-project/vllm/pull/12345",
          "verified_state": "MERGED"
        }
      ]
    }
  ],
  "counts": {
    "amd_subfeatures_with_rocm_backend": 1,
    "nvidia_subfeatures_with_cuda_backend": 1,
    "subfeatures_by_repo": {
      "ROCm/composable_kernel": 1,
      "flashinfer-ai/flashinfer": 1
    }
  }
}
```

## stability_gaps.json

AMD stability issues compared with NVIDIA. Stability is not a third score; each entry must feed one of the two score dimensions only when it affects the scoped feature.

```jsonc
{
  "_meta": {
    "schema": "stability_gaps.v1",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "prefix caching",
    "verified_at": "ISO-8601",
    "dropped_unverified": [],
    "dropped_out_of_scope": [],
    "dropped_below_threshold": []
  },
  "entries": [
    {
      "row_id": "stability_gap:automatic-prefix-caching:mi300x-long-prompts",
      "subfeature": "automatic prefix caching",
      "symptom": "hang on long prompts on MI300X (full prose, no ellipsis)",
      "side_affected": "AMD",
      "comparison_baseline": "NVIDIA path has no matching verified issue (full prose, no ellipsis)",
      "feeds_score": "feature_relevance",
      "rationale": "Disables prefix caching on MI300X for sequences over 8k. (full prose, no ellipsis)",
      "amd_severity": "high",
      "nvidia_severity": "none",
      "amd_owner_candidate": "ROCm/aotriton",
      "nvidia_owner_candidate": null,
      "confidence": "medium",
      "evidence_refs": [
        {
          "artifact": "collectors/framework_amd.json",
          "json_pointer": "/entries/3",
          "evidence_id": "framework_amd_collector:vllm-project-vllm-34567:automatic-prefix-caching",
          "ref": "vllm-project/vllm#34567",
          "source_url": "https://github.com/vllm-project/vllm/issues/34567",
          "verified_state": "OPEN"
        }
      ]
    }
  ]
}
```

`amd_severity` and `nvidia_severity` are required on every retained entry. Allowed values are `none`, `low`, `medium`, `high`, and `critical` per `criteria.md` `## Severity Rating` (Stability severity scale). At least one side's severity must be `>= medium` for the row to be retained; rows whose highest severity is `low` or `none` belong in `_meta.dropped_below_threshold` with reason `severity_too_low_to_feed_scored_dimension`. `side_affected` remains required for backwards compatibility and must equal the side with the higher severity (or AMD when severities are tied and AMD is the affected side per `feeds_score` rationale).

`amd_owner_candidate` and `nvidia_owner_candidate` are required on every retained entry. Use `null` only when no verified owner exists for that side. Do not collapse side-specific ownership into one generic owner because the affected side and remediation owner can differ from the comparison baseline.

`symptom`, `comparison_baseline`, and `rationale` MUST be full prose. Do not truncate with three-or-more-dot ellipses, `…`, or any elision marker; downstream dashboard renderers will compress for table cells while preserving the full prose verbatim in per-row detail subsections.

## performance_kernel_gaps.json

Kernel and performance deltas, including missing kernels, immature kernels, fallback paths, missing fusion, poor lowering, and excessive host sync.

```jsonc
{
  "_meta": {
    "schema": "performance_kernel_gaps.v1",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "MoE expert parallelism",
    "verified_at": "ISO-8601",
    "dropped_unverified": [],
    "dropped_out_of_scope": [],
    "dropped_below_threshold": []
  },
  "entries": [
    {
      "row_id": "performance_gap:moe-grouped-gemm:missing-fused-kernel",
      "subfeature": "MoE grouped GEMM",
      "claim_type": "quantitative_benchmark",
      "kind": "missing_kernel",
      "nv_state": "FlashInfer fused grouped GEMM available on H100/B200 (full prose, no ellipsis).",
      "amd_state": "No fused grouped GEMM on MI300X; falls back to per-expert GEMM (full prose, no ellipsis).",
      "delta_estimate": "Approx 2.1x slower decode tok/s on MI300X vs H100 for Llama3-70B, batch size 8 (full prose, no ellipsis).",
      "amd_severity": 4,
      "nvidia_severity": 0,
      "comparability": {
        "model": "Llama3-70B",
        "dtype": "fp16",
        "batch_size": "8",
        "sequence_lengths": "documented",
        "feature_flags": "documented",
        "warmup": "documented",
        "metric": "decode tok/s",
        "hardware_generation": "MI300X vs H100",
        "power_clock_policy": "unspecified",
        "evidence_type": "end_to_end",
        "code_path_note": "AMD fallback path vs NVIDIA fused grouped GEMM path."
      },
      "amd_owner_candidate": "ROCm/composable_kernel",
      "nvidia_owner_candidate": "flashinfer-ai/flashinfer",
      "confidence": "medium",
      "evidence_tier": "primary",
      "evidence_refs": [
        {
          "artifact": "collectors/framework_amd.json",
          "json_pointer": "/entries/2",
          "evidence_id": "framework_amd_collector:vllm-project-vllm-22222:moe-grouped-gemm",
          "ref": "vllm-project/vllm#22222",
          "source_url": "https://github.com/vllm-project/vllm/pull/22222",
          "verified_state": "MERGED"
        }
      ]
    }
  ]
}
```

`claim_type` is required on each performance-kernel gap entry:

- `quantitative_benchmark`: the row relies on a numeric benchmark, kernel timing, throughput, latency, memory, or scaling delta. Its `comparability` block must include model, dtype, batch size, sequence lengths, feature flags, warmup, metric, hardware generation, power/clock policy when available, and `evidence_type`.
- `performance_path`: the row is a qualitative path comparison such as `missing_kernel`, `fallback_path`, `missing_fusion`, `poor_lowering`, or `excessive_host_sync` without a numeric delta. Its `comparability` block must include same framework/feature/subfeature, side-specific code paths, feature flags or dispatch conditions, hardware generation, dependency or backend versions when known, and a `code_path_note` explaining whether the paths are equivalent or intentionally different.

`amd_severity` and `nvidia_severity` are required on every retained entry as integers in `[0, 5]` per `criteria.md` `## Severity Rating` (Performance severity scale). Both sides MUST be assigned even when one is `0`. Severity values must be defensible from the same `evidence_refs` that justify the row; lower severity rather than dropping when comparability is incomplete or evidence is anecdotal.

`amd_owner_candidate` and `nvidia_owner_candidate` are required on every retained entry. Use `null` only when no verified owner exists for that side. For one-sided AMD gaps, still identify the NVIDIA owner or backend that provides the comparison path when verified, so follow-up ownership is auditable on both sides.

`nv_state`, `amd_state`, `delta_estimate`, and every field of the `comparability` block MUST be full prose. Do not truncate with three-or-more-dot ellipses, `…`, or any elision marker; downstream dashboard renderers will compress for table cells while preserving the full prose verbatim in per-row detail subsections.

## criteria_scores.json

Scores only feature relevance and performance relevance. Use 0 to 5 per side. Reported gap is `nvidia_score - amd_score`.

```jsonc
{
  "_meta": {
    "schema": "criteria_scores.v1",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "prefix caching",
    "verified_at": "ISO-8601",
    "scale": "0-5",
    "dropped_unverified": [],
    "dropped_out_of_scope": [],
    "dropped_below_threshold": []
  },
  "entries": [
    {
      "row_id": "criteria_score:kernel-availability-attention:automatic-prefix-caching",
      "criterion": "Kernel availability - attention",
      "dimension": "performance_relevance",
      "subfeatures": ["automatic prefix caching"],
      "amd_score": 3,
      "nvidia_score": 5,
      "nvidia_minus_amd_gap": 2,
      "scale": "0-5",
      "rationale": "AMD lacks a paged-FlashAttention v3 equivalent; uses an aotriton path.",
      "evidence_refs": [
        {
          "artifact": "analysis/performance_kernel_gaps.json",
          "json_pointer": "/entries/0",
          "row_id": "performance_gap:moe-grouped-gemm:missing-fused-kernel",
          "ref": "ROCm/aotriton#321",
          "source_url": "https://github.com/ROCm/aotriton/pull/321",
          "verified_state": "MERGED"
        }
      ],
      "evidence_tier": "primary",
      "comparability_note": "Qualitative path comparison; no numeric benchmark delta is claimed.",
      "confidence": "medium",
      "primary_amd_owner": "ROCm/aotriton",
      "primary_nvidia_owner": "flashinfer-ai/flashinfer",
      "amd_co_owners": ["vllm-project/vllm"],
      "nvidia_co_owners": ["vllm-project/vllm"],
      "amd_integration_surface": "attention backend dispatch and kernel lowering",
      "nvidia_integration_surface": "attention backend dispatch and kernel selection"
    }
  ],
  "score_scale": {
    "0": "not present or actively broken",
    "1": "experimental, blocked by major bugs, or only on out-of-scope hardware",
    "2": "usable but limited model, dtype, or shape coverage, or large performance gap",
    "3": "usable on representative configs, with known but bounded gaps",
    "4": "parity on most representative configs",
    "5": "state of the art on the requested feature"
  }
}
```

Criteria rows may include multiple `subfeatures` when the same criterion and score applies to each listed subfeature. Downstream dashboard construction must explode each source row into one `tables.score_rows` row per `(criterion, subfeature, dimension)` tuple; do not render an array-valued subfeature cell in dashboard data or the report.

Criteria rows must include `evidence_tier` for source strength and `comparability_note` for methodology completeness. Quantitative performance rows may additionally include a structured `comparability` block matching the `performance_kernel_gaps.json` rules. Criteria rows may include optional side-specific owner fields: `primary_amd_owner`, `primary_nvidia_owner`, `amd_co_owners`, `nvidia_co_owners`, `amd_integration_surface`, and `nvidia_integration_surface`. Prefer these fields whenever a row implies a side-specific fix or follow-up. Leave a side-specific owner field `null` or omit it only when no verified owner exists; do not collapse different AMD and NVIDIA owners into generic owner fields.

## dashboard/dashboard_data.json

Visualization-ready data used to render the final dashboard report. Keep this artifact normalized enough for charts, tables, or a later UI to consume without reparsing prose.

```jsonc
{
  "_meta": {
    "schema": "dashboard_data.v1",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "prefix caching",
    "generated_at": "ISO-8601",
    "dropped_unverified": [],
    "dropped_out_of_scope": [],
    "dropped_below_threshold": [],
    "source_artifacts": [
      "scope.json",
      "subfeatures.json",
      "collectors/framework_amd.json",
      "collectors/framework_nvidia.json",
      "collectors/rocm_stack.json",
      "collectors/nvidia_stack.json",
      "collectors/official_web.json",
      "collectors/third_party_perf.json",
      "analysis/subfeature_influence_matrix.json",
      "analysis/backend_repo_map.json",
      "analysis/stability_gaps.json",
      "analysis/performance_kernel_gaps.json",
      "analysis/criteria_scores.json",
      "monitors/monitor_evidence.md",
      "monitors/monitor_scope.md",
      "monitors/monitor_comparison.md",
      "dashboard/report_citations.json"
    ],
    "final_status": {
      "status": "draft",
      "post_synthesis_evidence_verdict": null,
      "citation_manifest_status": null,
      "finalized_at": null,
      "notes": []
    }
  },
  "counts": {
    "total_subfeatures": 8,
    "support_state": {
      "amd": {"supported": 2, "experimental": 3, "missing": 2, "broken": 1},
      "nvidia": {"supported": 6, "experimental": 1, "missing": 1, "broken": 0}
    },
    "framework_refs": {
      "amd": {"prs": 42, "issues": 17, "recent_activity": 9},
      "nvidia": {"prs": 88, "issues": 11, "recent_activity": 22}
    },
    "enablement_state": {
      "amd": {"default_on": 1, "flag_gated": 5, "unavailable": 2, "unknown": 0},
      "nvidia": {"default_on": 6, "flag_gated": 1, "unavailable": 1, "unknown": 0}
    },
    "backend_repo_influence": {
      "amd_subfeatures_with_rocm_backend": 6,
      "nvidia_subfeatures_with_cuda_backend": 7
    },
    "stability_gaps_by_dimension": {"feature_relevance": 3, "performance_relevance": 2},
    "stability_severity": {
      "amd": {"none": 0, "low": 0, "medium": 1, "high": 3, "critical": 1},
      "nvidia": {"none": 4, "low": 1, "medium": 0, "high": 0, "critical": 0}
    },
    "performance_gaps_by_kind": {
      "missing_kernel": 1,
      "immature_kernel": 0,
      "fallback_path": 2,
      "missing_fusion": 1,
      "poor_lowering": 0,
      "excessive_host_sync": 1
    },
    "performance_severity": {
      "amd": {"0": 0, "1": 0, "2": 1, "3": 1, "4": 2, "5": 1},
      "nvidia": {"0": 4, "1": 1, "2": 0, "3": 0, "4": 0, "5": 0}
    },
    "criteria_by_dimension": {"feature_relevance": 6, "performance_relevance": 9},
    "dropped_unverified_total": 4,
    "dropped_out_of_scope_total": 2,
    "dropped_below_threshold_total": 1
  },
  "cards": [
    {"id": "total_subfeatures", "label": "Total subfeatures", "value_ref": "counts.total_subfeatures", "unit": "count"},
    {"id": "largest_gap", "label": "Largest score gap", "value": 3, "unit": "score"},
    {"id": "amd_blockers", "label": "AMD high-confidence blockers", "value": 4, "unit": "count"},
    {"id": "dropped_claims", "label": "Dropped or unverified claims", "value_ref": "counts.dropped_unverified_total", "unit": "count"}
  ],
  "tables": {
    "gap_dashboard": [
      {
        "row_id": "dashboard_gap:automatic-prefix-caching",
        "subfeature": "automatic prefix caching",
        "amd_state": "experimental",
        "nvidia_state": "supported",
        "feature_score_amd": 3,
        "feature_score_nvidia": 5,
        "perf_score_amd": 2,
        "perf_score_nvidia": 5,
        "feature_gap": 2,
        "perf_gap": 3,
        "max_abs_gap": 3,
        "primary_amd_owner": "ROCm/aotriton",
        "primary_nvidia_owner": "flashinfer-ai/flashinfer",
        "top_blocker": "AMD fallback path for long context decode",
        "aggregation_rule": "max_abs_gap",
        "source_criteria_row_ids": ["criteria_score:kernel-availability-attention:automatic-prefix-caching"],
        "evidence_tier": "primary",
        "confidence": "medium",
        "evidence_refs": [
          {
            "artifact": "analysis/criteria_scores.json",
            "json_pointer": "/entries/0",
            "row_id": "criteria_score:kernel-availability-attention:automatic-prefix-caching",
            "ref": "ROCm/aotriton#321",
            "source_url": "https://github.com/ROCm/aotriton/pull/321",
            "verified_state": "MERGED"
          }
        ]
      }
    ],
    "score_rows": [
      {
        "row_id": "dashboard_score:kernel-availability-attention:automatic-prefix-caching:performance_relevance",
        "source_row_ids": ["criteria_score:kernel-availability-attention:automatic-prefix-caching"],
        "criterion": "Kernel availability - attention",
        "subfeature": "automatic prefix caching",
        "dimension": "performance_relevance",
        "amd_score": 3,
        "nvidia_score": 5,
        "gap": 2,
        "rationale": "AMD lacks a paged-FlashAttention v3 equivalent; uses an aotriton path.",
        "primary_amd_owner": "ROCm/aotriton",
        "primary_nvidia_owner": "flashinfer-ai/flashinfer",
        "amd_co_owners": ["vllm-project/vllm"],
        "nvidia_co_owners": ["vllm-project/vllm"],
        "amd_integration_surface": "attention backend dispatch and kernel lowering",
        "nvidia_integration_surface": "attention backend dispatch and kernel lowering",
        "confidence": "medium",
        "evidence_tier": "primary",
        "comparability_note": "Qualitative path comparison; no numeric benchmark delta is claimed.",
        "evidence_refs": [
          {
            "artifact": "analysis/criteria_scores.json",
            "json_pointer": "/entries/0",
            "row_id": "criteria_score:kernel-availability-attention:automatic-prefix-caching",
            "ref": "ROCm/aotriton#321",
            "source_url": "https://github.com/ROCm/aotriton/pull/321",
            "verified_state": "MERGED"
          }
        ]
      }
    ],
    "repo_influence": [
      {"side": "AMD", "repo": "ROCm/aotriton", "influenced_subfeatures": 3},
      {"side": "NVIDIA", "repo": "flashinfer-ai/flashinfer", "influenced_subfeatures": 4}
    ],
    "performance_gaps": [
      {"kind": "missing_kernel", "count": 1},
      {"kind": "immature_kernel", "count": 0},
      {"kind": "fallback_path", "count": 2},
      {"kind": "missing_fusion", "count": 1},
      {"kind": "poor_lowering", "count": 0},
      {"kind": "excessive_host_sync", "count": 1}
    ],
    "support_state_distribution": [
      {"side": "AMD", "state": "supported", "count": 2},
      {"side": "AMD", "state": "experimental", "count": 3},
      {"side": "AMD", "state": "missing", "count": 2},
      {"side": "AMD", "state": "broken", "count": 1},
      {"side": "NVIDIA", "state": "supported", "count": 6},
      {"side": "NVIDIA", "state": "experimental", "count": 1},
      {"side": "NVIDIA", "state": "missing", "count": 1},
      {"side": "NVIDIA", "state": "broken", "count": 0}
    ],
    "enablement_state_distribution": [
      {"side": "AMD", "state": "default_on", "count": 1},
      {"side": "AMD", "state": "flag_gated", "count": 5},
      {"side": "AMD", "state": "unavailable", "count": 2},
      {"side": "AMD", "state": "unknown", "count": 0},
      {"side": "NVIDIA", "state": "default_on", "count": 6},
      {"side": "NVIDIA", "state": "flag_gated", "count": 1},
      {"side": "NVIDIA", "state": "unavailable", "count": 1},
      {"side": "NVIDIA", "state": "unknown", "count": 0}
    ],
    "framework_refs_by_side": [
      {"side": "AMD", "kind": "pr", "count": 42},
      {"side": "AMD", "kind": "issue", "count": 17},
      {"side": "AMD", "kind": "recent_activity", "count": 9},
      {"side": "NVIDIA", "kind": "pr", "count": 88},
      {"side": "NVIDIA", "kind": "issue", "count": 11},
      {"side": "NVIDIA", "kind": "recent_activity", "count": 22}
    ],
    "stability_gaps_detail": [
      {
        "row_id": "dashboard_stability_gap:automatic-prefix-caching:mi300x-long-prompts",
        "source_row_ids": ["stability_gap:automatic-prefix-caching:mi300x-long-prompts"],
        "subfeature": "automatic prefix caching",
        "symptom": "Full prose symptom text copied verbatim from analysis/stability_gaps.json - no truncation, no ellipsis.",
        "side_affected": "AMD",
        "comparison_baseline": "Full prose comparison baseline text copied verbatim - no truncation.",
        "feeds_score": "feature_relevance",
        "rationale": "Full prose rationale copied verbatim - no truncation.",
        "amd_severity": "high",
        "nvidia_severity": "none",
        "amd_owner_candidate": "ROCm/aotriton",
        "nvidia_owner_candidate": null,
        "confidence": "medium",
        "evidence_refs": [
          {
            "artifact": "analysis/stability_gaps.json",
            "json_pointer": "/entries/0",
            "row_id": "stability_gap:automatic-prefix-caching:mi300x-long-prompts",
            "ref": "vllm-project/vllm#34567",
            "source_url": "https://github.com/vllm-project/vllm/issues/34567",
            "verified_state": "OPEN"
          }
        ]
      }
    ],
    "performance_gaps_detail": [
      {
        "row_id": "dashboard_performance_gap:moe-grouped-gemm:missing-fused-kernel",
        "source_row_ids": ["performance_gap:moe-grouped-gemm:missing-fused-kernel"],
        "subfeature": "MoE grouped GEMM",
        "kind": "missing_kernel",
        "claim_type": "quantitative_benchmark",
        "nv_state": "Full prose NVIDIA state copied verbatim from analysis/performance_kernel_gaps.json - no truncation.",
        "amd_state": "Full prose AMD state copied verbatim - no truncation.",
        "delta_estimate": "Full prose delta estimate copied verbatim - no truncation.",
        "amd_severity": 4,
        "nvidia_severity": 0,
        "comparability": {
          "model": "Llama3-70B",
          "dtype": "fp16",
          "batch_size": "8",
          "sequence_lengths": "documented",
          "feature_flags": "documented",
          "warmup": "documented",
          "metric": "decode tok/s",
          "hardware_generation": "MI300X vs H100",
          "power_clock_policy": "unspecified",
          "evidence_type": "end_to_end",
          "code_path_note": "AMD fallback path vs NVIDIA fused grouped GEMM path."
        },
        "amd_owner_candidate": "ROCm/composable_kernel",
        "nvidia_owner_candidate": "flashinfer-ai/flashinfer",
        "confidence": "medium",
        "evidence_tier": "primary",
        "evidence_refs": [
          {
            "artifact": "analysis/performance_kernel_gaps.json",
            "json_pointer": "/entries/0",
            "row_id": "performance_gap:moe-grouped-gemm:missing-fused-kernel",
            "ref": "vllm-project/vllm#22222",
            "source_url": "https://github.com/vllm-project/vllm/pull/22222",
            "verified_state": "MERGED"
          }
        ]
      }
    ],
    "stability_severity_by_side": [
      {"side": "AMD", "severity": "none", "count": 0},
      {"side": "AMD", "severity": "low", "count": 0},
      {"side": "AMD", "severity": "medium", "count": 1},
      {"side": "AMD", "severity": "high", "count": 3},
      {"side": "AMD", "severity": "critical", "count": 1},
      {"side": "NVIDIA", "severity": "none", "count": 4},
      {"side": "NVIDIA", "severity": "low", "count": 1},
      {"side": "NVIDIA", "severity": "medium", "count": 0},
      {"side": "NVIDIA", "severity": "high", "count": 0},
      {"side": "NVIDIA", "severity": "critical", "count": 0}
    ],
    "performance_severity_by_side": [
      {"side": "AMD", "severity": 0, "count": 0},
      {"side": "AMD", "severity": 1, "count": 0},
      {"side": "AMD", "severity": 2, "count": 1},
      {"side": "AMD", "severity": 3, "count": 1},
      {"side": "AMD", "severity": 4, "count": 2},
      {"side": "AMD", "severity": 5, "count": 1},
      {"side": "NVIDIA", "severity": 0, "count": 4},
      {"side": "NVIDIA", "severity": 1, "count": 1},
      {"side": "NVIDIA", "severity": 2, "count": 0},
      {"side": "NVIDIA", "severity": 3, "count": 0},
      {"side": "NVIDIA", "severity": 4, "count": 0},
      {"side": "NVIDIA", "severity": 5, "count": 0}
    ]
  },
  "charts": [
    {
      "id": "score_gap_by_subfeature_dimension",
      "title": "Score gap by subfeature and dimension",
      "type": "bar",
      "data_table": "score_rows",
      "x": "subfeature",
      "y": "gap",
      "series": "dimension"
    },
    {
      "id": "repo_influence_by_side",
      "title": "Backend repo influence by side",
      "type": "stacked_bar",
      "data_table": "repo_influence",
      "x": "repo",
      "y": "influenced_subfeatures",
      "series": "side"
    },
    {
      "id": "performance_gap_kinds",
      "title": "Performance gap kinds",
      "type": "bar",
      "data_table": "performance_gaps",
      "x": "kind",
      "y": "count"
    },
    {
      "id": "support_state_distribution",
      "title": "Subfeature support state by side",
      "type": "stacked_bar",
      "data_table": "support_state_distribution",
      "x": "state",
      "y": "count",
      "series": "side"
    },
    {
      "id": "enablement_state_distribution",
      "title": "Subfeature enablement state by side",
      "type": "stacked_bar",
      "data_table": "enablement_state_distribution",
      "x": "state",
      "y": "count",
      "series": "side"
    },
    {
      "id": "framework_refs_by_side",
      "title": "Framework PR/issue/activity counts by side",
      "type": "stacked_bar",
      "data_table": "framework_refs_by_side",
      "x": "kind",
      "y": "count",
      "series": "side"
    },
    {
      "id": "stability_severity_by_side",
      "title": "Stability gap severity by side",
      "type": "stacked_bar",
      "data_table": "stability_severity_by_side",
      "x": "severity",
      "y": "count",
      "series": "side"
    },
    {
      "id": "performance_severity_by_side",
      "title": "Performance gap severity by side",
      "type": "stacked_bar",
      "data_table": "performance_severity_by_side",
      "x": "severity",
      "y": "count",
      "series": "side"
    }
  ]
}
```

Allowed chart `type` values: `bar`, `stacked_bar`, `heatmap`, `scatter`, `line`, `table`. Every chart must name a `data_table` present in `tables` (or use `value_ref` paths into `counts`).

Required content for `dashboard_data.v1`:
- `counts` must be present and complete enough that every required count in `report-template.md` resolves without reparsing other artifacts.
- `_meta.source_artifacts` must list every collector JSON, every analysis JSON used for dashboard construction, all three monitor markdown files, and `dashboard/report_citations.json` once it exists. The finalization refresh after the post-synthesis evidence rerun must include `dashboard/report_citations.json`.
- `_meta.final_status` must be `draft` before the post-synthesis evidence rerun, then refreshed during finalization to one of `publishable`, `publishable-with-caveats`, or `blocked` using the post-synthesis evidence verdict, monitor verdicts, and citation manifest status.
- `tables.gap_dashboard` must contain one row per important subfeature with both `feature_gap` and `perf_gap` populated. Aggregation is deterministic: for each `(subfeature, dimension)` use the criterion row with largest absolute `nvidia_minus_amd_gap`, breaking ties by `evidence_tier` (`primary` > `secondary` > `anecdotal`) and then `confidence` (`high` > `medium` > `low`). Set `aggregation_rule="max_abs_gap"` and `source_criteria_row_ids[]` to the selected criteria row IDs. Do not average scores unless the schema is revised.
- `tables.score_rows` must contain one row per `(criterion, subfeature, dimension)` tuple from `criteria_scores.json`, including `rationale`, `evidence_tier`, and `comparability_note`. If a criteria row has `subfeatures: [...]`, explode it into one singular-subfeature dashboard row for each listed subfeature. Populate `primary_amd_owner`, `primary_nvidia_owner`, `amd_co_owners`, `nvidia_co_owners`, `amd_integration_surface`, and `nvidia_integration_surface` from side-specific fields in `criteria_scores.json` when present. If a criteria row lacks side-specific owner fields, enrich the missing fields from `analysis/backend_repo_map.json` by matching `(subfeature, side)`; leave the corresponding owner field `null` only when no verified owner exists.
- `tables.repo_influence` must contain one row per `(side, repo)` from `backend_repo_map.json`.
- `tables.performance_gaps` must contain one row per allowed `kind` value, even when the count is 0.
- `tables.support_state_distribution` must cover every `(side, support_state)` combination for both sides and all allowed states, including zero-count rows.
- `tables.enablement_state_distribution` must cover every `(side, enablement_state)` combination for both sides and all allowed states (`default_on`, `flag_gated`, `unavailable`, `unknown`), including zero-count rows.
- `tables.framework_refs_by_side` must include `pr`, `issue`, and `recent_activity` rows for both sides.
- `tables.stability_gaps_detail` must contain one row per entry in `analysis/stability_gaps.json` `entries[]`. Each row carries `row_id`, `source_row_ids`, `subfeature`, `side_affected`, full prose `symptom`, full prose `comparison_baseline`, full prose `rationale`, `feeds_score`, `amd_severity`, `nvidia_severity`, `amd_owner_candidate`, `nvidia_owner_candidate`, `confidence`, and structured `evidence_refs`. Prose fields MUST be copied verbatim from the source artifact; never insert `...`, `....`, `…`, or any ellipsis. Sort rows by `max(amd_severity, nvidia_severity)` descending using the stability enum order `none < low < medium < high < critical`, breaking ties by `confidence` descending.
- `tables.performance_gaps_detail` must contain one row per entry in `analysis/performance_kernel_gaps.json` `entries[]`. Each row carries `row_id`, `source_row_ids`, `subfeature`, `kind`, `claim_type`, full prose `nv_state`, full prose `amd_state`, full prose `delta_estimate`, the entire `comparability` block verbatim, `amd_severity` (int 0..5), `nvidia_severity` (int 0..5), `amd_owner_candidate`, `nvidia_owner_candidate`, `confidence`, `evidence_tier`, and structured `evidence_refs`. Prose fields and the `comparability` block MUST be copied verbatim from the source artifact; never insert `...`, `....`, `…`, or any ellipsis. Sort rows by `max(amd_severity, nvidia_severity)` descending, breaking ties by `evidence_tier` (`primary` > `secondary` > `anecdotal`) and then `confidence` descending.
- `tables.stability_severity_by_side` must contain one row per `(side, severity)` for both sides and every value in the stability enum (`none`, `low`, `medium`, `high`, `critical`), including zero-count rows.
- `tables.performance_severity_by_side` must contain one row per `(side, severity)` for both sides and every integer severity in `[0, 5]`, including zero-count rows.
- `counts.stability_severity.{amd,nvidia}` must include all five enum keys with zero-count entries when applicable. `counts.performance_severity.{amd,nvidia}` must include all six integer keys (`"0"` through `"5"`) with zero-count entries when applicable.
- `counts.dropped_unverified_total`, `counts.dropped_out_of_scope_total`, and `counts.dropped_below_threshold_total` must be counted separately across all artifact `_meta` arrays.
- `charts[]` must include at least the chart specs in the schema example above plus `stability_severity_by_side` and `performance_severity_by_side`.

## dashboard/report_citations.json

Post-synthesis citation manifest for `REPORT.md`. Generate it after drafting the report and before the final evidence-monitor rerun. It is the contract that final report citations still map back to verified artifacts after synthesis. The later finalization refresh may update dashboard provenance and the report footer only; if finalization changes any cited claim, ref, URL, quote, or citation entry, regenerate this manifest and rerun post-synthesis `monitor_evidence`.

```jsonc
{
  "_meta": {
    "schema": "report_citations.v1",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "prefix caching",
    "generated_at": "ISO-8601",
    "dropped_unverified": [],
    "dropped_out_of_scope": [],
    "dropped_below_threshold": [],
    "report_path": "REPORT.md",
    "dashboard_data_path": "dashboard/dashboard_data.json",
    "source_artifacts": [
      "scope.json",
      "subfeatures.json",
      "collectors/framework_amd.json",
      "collectors/framework_nvidia.json",
      "collectors/rocm_stack.json",
      "collectors/nvidia_stack.json",
      "collectors/official_web.json",
      "collectors/third_party_perf.json",
      "analysis/subfeature_influence_matrix.json",
      "analysis/backend_repo_map.json",
      "analysis/stability_gaps.json",
      "analysis/performance_kernel_gaps.json",
      "analysis/criteria_scores.json",
      "dashboard/dashboard_data.json",
      "monitors/monitor_evidence.md",
      "monitors/monitor_scope.md",
      "monitors/monitor_comparison.md"
    ],
    "manifest_check": {
      "status": "pass",
      "report_refs_count": 12,
      "manifest_refs_count": 12,
      "missing_from_manifest": [],
      "missing_from_report": []
    }
  },
  "citations": [
    {
      "report_section": "Kernel and performance gap analysis",
      "claim": "AMD uses a fallback path for long-context decode while NVIDIA uses a fused attention backend.",
      "refs": [
        {
          "artifact": "analysis/performance_kernel_gaps.json",
          "json_pointer": "/entries/0",
          "row_id": "performance_gap:moe-grouped-gemm:missing-fused-kernel",
          "ref": "ROCm/aotriton#321",
          "source_url": "https://github.com/ROCm/aotriton/pull/321",
          "verified_state": "MERGED",
          "evidence_tier": "primary",
          "quote": "",
          "quote_sha256": null
        }
      ],
      "dashboard_sources": [
        {
          "artifact": "dashboard/dashboard_data.json",
          "json_pointer": "/tables/score_rows/0",
          "row_id": "dashboard_score:kernel-availability-attention:automatic-prefix-caching:performance_relevance"
        }
      ],
      "monitor_coverage": ["monitors/monitor_evidence.md"],
      "status": "verified"
    }
  ]
}
```

Manifest rules:
- Every non-obvious claim, PR/issue ref, URL, and quote in `REPORT.md` must appear in `citations[]`.
- Every `citations[].refs[]` item must point to one listed `source_artifacts` entry and, when it cites evidence, to a retained collector or analysis record with a non-`DROPPED` `verified_state`.
- Every `citations[].refs[]` item must include an exact RFC-6901 JSON Pointer (`json_pointer`) plus either `evidence_id` (collector evidence) or `row_id` (analysis/dashboard row). The monitor resolves the pointer and confirms the ID at that location matches. Array indexes without IDs are invalid.
- Every `dashboard_sources[]` item must include `artifact`, `json_pointer`, and `row_id`. Strings such as `dashboard_data.tables.score_rows[0]` are invalid because they become stale after sorting.
- `manifest_check.status` must be `pass` before publish. If report refs and manifest refs differ, update the report or manifest and recheck; do not publish with missing refs.
- `quote_sha256` is required when `quote` is non-empty and must be SHA-256 over the exact UTF-8 quote string in the source artifact.
- Dropped or unverifiable claims belong in artifact `_meta.dropped_unverified`, not in `citations[]`.

## Monitor Audit Output Expectations

Monitor artifacts are Markdown files: `monitors/monitor_evidence.md`, `monitors/monitor_scope.md`, and `monitors/monitor_comparison.md`. Each monitor returns one verdict: `GREEN`, `YELLOW`, or `RED`.

Required structure:

```markdown
# monitor_evidence Audit

Verdict: GREEN
Checked at: ISO-8601
Run phase: initial | post_synthesis
Artifacts checked: collectors/framework_amd.json, analysis/criteria_scores.json
Sample rate: 0.80
Remediation state: remediation_state.json
Recollection rounds used: 0
Rounds remaining: 2

## Required Checks
- PASS: PR and issue refs exist and states match.
- PASS: Web quotes match fetched sources.
- PASS: Post-synthesis report and citation-manifest refs are verified when run phase is post_synthesis.
- PASS: Dropped unreachable refs are listed in source artifact metadata.

## Findings
- severity: info
  artifact: collectors/framework_amd.json
  ref: vllm-project/vllm#12345
  action: kept
  note: State verified as MERGED.

## Punch List
- None.

## Dropped Evidence
- None.

## Footer
Summary: One sentence audit result.
```

Monitor-specific required checks:

- `monitor_evidence`: run once after analysis to re-verify 100 percent of refs and quotes that appear in `dashboard/dashboard_data.json`, then rerun after draft `REPORT.md` and `dashboard/report_citations.json` exist. The post-synthesis rerun must re-verify 100 percent of refs and quotes that appear in `dashboard/dashboard_data.json`, `dashboard/report_citations.json`, or any `tables.*`/`cards` value of `REPORT.md`. It must also resolve every manifest `json_pointer` and stable `evidence_id`/`row_id`. Re-sample at least 80 percent of remaining retained refs in `collectors/*.json`. Any unreachable retained ref is a must-fix: drop it into `_meta.dropped_unverified`, remove dependent claims, and rerun the monitor.
- `monitor_scope`: verify framework, feature, side classification, vendor-neutral placement, and that `scope.json.resolved.chip_scope_source` equals `scope.md#rocm_agent_scope.v1`. Confirm that `scope.json.chip_scope.{amd,nvidia}.aliases`, `product_aliases`, `search_terms`, `in_scope`, `out_of_scope_drops`, and `default_scope_statement` are present verbatim from the fenced `rocm_agent_scope.v1` JSON block in `scope.md` (no alternate chip map). Reject entries whose `hardware` falls under `out_of_scope_drops` and require any narrowing to appear only in `effective_scope_statement`.
- `monitor_comparison`: split checks by claim type. For `quantitative_benchmark` claims, verify model, dtype, batch size, sequence lengths, feature flags, warmup, metric definition, hardware generation, power or clock policy when available, and whether evidence is microbenchmark or end-to-end. For qualitative `performance_path` claims, verify same framework/feature/subfeature, comparable side-specific code paths or an explicit path-difference note, feature flags or dispatch conditions, hardware generation, and dependency/backend versions when known.

Verification policy:

- Collectors must verify 100 percent of entries kept in their final artifact via `gh ... view` or live `WebFetch`; do not retain unverified entries.
- Monitors must verify 100 percent of refs and quotes that appear in `dashboard/dashboard_data.json`, `dashboard/report_citations.json`, or the final report.
- The post-synthesis `monitor_evidence` rerun must occur after both `REPORT.md` and `dashboard/report_citations.json` exist, with `remediation_state.json.current_monitor_run_phase = "post_synthesis"`, and before publish. Record the rerun in `monitors/monitor_evidence.md` so the final report and citation manifest are monitor-verifiable.
- After the post-synthesis rerun, finalization may update only `dashboard/dashboard_data.json` `_meta.source_artifacts`, `_meta.final_status`, and the `REPORT.md` monitor verdict footer. If any cited claim, ref, URL, quote, or citation entry changes, regenerate `dashboard/report_citations.json` and rerun post-synthesis `monitor_evidence`.
- The 80 percent sampling rate applies only to non-cited retained evidence.

Verdict handling:

- `GREEN`: proceed.
- `YELLOW`: if recollection rounds remain, remediate the punch list before the next stage. After the maximum rounds, `YELLOW` may remain only for documented non-blocking caveats that do not affect citation validity, retained-evidence reachability, scope correctness, score correctness, or comparison fairness.
- `RED`: recollect affected artifacts or drop bad claims before final report synthesis. If a blocking finding remains after the maximum rounds, keep or convert the verdict to `RED` and do not publish.

## Evidence Tier Definitions

Use these values in `evidence_tier` and in monitor confidence decisions.

```jsonc
{
  "primary": {
    "definition": "Upstream PRs, issues, commits, release artifacts, or reproducible benchmark harnesses with enough detail to verify the claim.",
    "examples": ["framework PR with files and merged state", "backend repo issue with maintainer diagnosis", "benchmark harness with model, dtype, batch, sequence lengths, metric, and hardware"],
    "report_use": "May support scored gaps and quantitative deltas when comparability checks pass."
  },
  "secondary": {
    "definition": "Official vendor, framework, or project documentation, release notes, blogs, or talks with stated methodology but limited independent reproduction detail.",
    "examples": ["AMD ROCm blog with benchmark setup", "NVIDIA developer blog with hardware and model details", "framework docs describing support limits"],
    "report_use": "May support scored gaps; quantitative claims need explicit methodology notes."
  },
  "anecdotal": {
    "definition": "Issue comments, forum posts, third-party posts, or benchmark claims without enough detail for reproduction.",
    "examples": ["user issue comment reporting speedup", "unverified blog benchmark", "discussion thread without exact config"],
    "report_use": "May provide context only; do not use alone for high-confidence scored gaps."
  }
}
```
