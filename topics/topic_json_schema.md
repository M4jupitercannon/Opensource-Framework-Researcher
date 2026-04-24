# Topic JSON schema (required)

Every `topics/{topic_name}.json` file MUST conform to this top-level shape.

```jsonc
{
  "_meta": {
    "topic_name": "completed_subfeatures",          // matches filename (no .json)
    "report_heading": "Completed Subfeatures",      // becomes ## heading in REPORT.md
    "chip": "NVIDIA",
    "framework": "vLLM",
    "framework_repo": "vllm-project/vllm",
    "feature": "EP",
    "scope": "NVIDIA Hopper and Blackwell GPUs (datacenter and consumer) — SM90 (Hopper), SM100/SM103 (Blackwell datacenter), SM120 (Blackwell consumer/workstation), SM121 (Blackwell DGX-Spark). Out: SM80/SM86 (Ampere), SM89 (Ada), SM110 (Jetson/DRIVE Thor).",
    "in_scope": ["SM90", "SM100", "SM103", "SM120", "SM121"],
    "sources_used": ["gh", "WebFetch:docs.vllm.ai"],   // see sources/source_playbook.md
    "verified_at": "2026-04-23T00:00:00Z",
    "dropped_out_of_scope": [                          // items considered but discarded (Stage-2 audit trail)
      {"ref": "PR #38421", "reason": "L40S/SM89 — Ada Lovelace, prior generation, out of scope"}
    ],
    "scope_mixing_narrowed": [                         // Stage-2: kept entries whose hardware list was narrowed
      // {"ref": "PR #11111", "kept_as": ["SM90","SM100"], "dropped_mention": ["SM89"]}
    ],
    "scope_ambiguity_annotated": [                     // Stage-2: kept entries whose family was annotated
      // {"ref": "PR #22222", "family": "Hopper", "in_scope_members": ["SM90"]}
    ],
    "removed_by_strictness_audit": [                   // Stage-3: dropped for failing feature-strictness
      // {"ref": "PR #33333", "original_bucket": "completed_subfeatures", "reason": "..."}
    ],
    "recategorized_as_other": [                        // Stage-3: moved to a different topic bucket
      // {"ref": "PR #44444", "original_bucket": "open_issues", "target_bucket": "kernels_or_components", "reason": "..."}
    ],
    "dedup_canonical": [                               // Stage-3: cross-listed entries deduped to canonical bucket
      // {"ref": "PR #55555", "canonical_bucket": "completed_subfeatures", "also_listed_under_dropped": ["open_issues"]}
    ],
    "verifications_run": 36                            // number of gh/WebFetch calls made
  },
  "entries": [ /* entries follow the per-topic schema in topics/default_topics.md */ ]
}
```

## Rules

1. The following `_meta` fields are REQUIRED on every topic file (initialize empty arrays / `0` as appropriate when produced). Files missing any will be rejected by `monitor_existence` (Stage 1) as RED:
   - `_meta.scope`, `_meta.sources_used`, `_meta.in_scope`, `_meta.framework_repo`, `_meta.verified_at`, `_meta.verifications_run`
   - **Stage-2 audit fields** (start as `[]`; populated when Stage-2 must-fixes are applied): `_meta.dropped_out_of_scope`, `_meta.scope_mixing_narrowed`, `_meta.scope_ambiguity_annotated`
   - **Stage-3 audit fields** (start as `[]`; populated when Stage-3 must-fixes are applied): `_meta.removed_by_strictness_audit`, `_meta.recategorized_as_other`, `_meta.dedup_canonical`
   - **Additionally required on `external_repo_dependencies.json`**: `_meta.dropped_unverifiable` (start as `[]`).
2. `_meta.verified_at` is the timestamp at which the producing researcher finished verification — use UTC ISO-8601.
3. `_meta.dropped_out_of_scope` is required (may be empty `[]`); it powers the report's Verification Footer. Same applies to the other Stage-2 / Stage-3 audit arrays — they MUST exist on every file even when empty.
4. Per-entry shape is defined in `topics/default_topics.md` under each topic's `entry schema:` block. The researcher must follow it exactly.
5. PR / issue references inside entries MUST include the `verified_state` field set by `gh`-checking immediately before write.
6. Source quotes (in `perf_numbers.json`) must be VERBATIM — no comma stripping, no paraphrase. The monitor will diff against the live PR body.
