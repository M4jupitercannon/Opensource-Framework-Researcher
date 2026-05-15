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
    "sources_used": ["mcp:signals", "gh", "WebFetch:docs.vllm.ai"],   // see sources/source_playbook.md
    "verified_at": "2026-04-23T00:00:00Z",
    "search_window": {                                 // C5: 4-field subset of the canonical search_window object (full object lives at out_dir/search_window.json)
      "raw_input":  "1y",
      "display":    "trailing 1 year (2025-05-14..2026-05-14)",
      "start_date": "2025-05-14",
      "end_date":   "2026-05-14"
    },
    "fallback_used": [                                 // C5: one entry per ref that fell back from mcp:signals to gh (or any other documented fallback)
      {
        "ref":             "vllm-project/vllm#1234",
        "tool_attempted":  "mcp:get_signal_detail",
        "tool_succeeded":  "gh:pr_view",
        "reason":          "mcp returned 404"
      }
    ],
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
    "verifications_run": 36                            // number of mcp:signals / gh / WebFetch calls made
  },
  "entries": [ /* entries follow the per-topic schema in topics/default_topics.md */ ]
}
```

## Rules

1. The following `_meta` fields are REQUIRED on every topic file (initialize empty arrays / `0` as appropriate when produced). Files missing any will be rejected by `monitor_existence` (Stage 1) as RED:
   - `_meta.scope`, `_meta.sources_used`, `_meta.in_scope`, `_meta.framework_repo`, `_meta.verified_at`, `_meta.verifications_run`
   - **C5 session-context fields**: `_meta.search_window` (object with the 4 fields below), `_meta.fallback_used` (array, may be empty `[]`).
   - **Stage-2 audit fields** (start as `[]`; populated when Stage-2 must-fixes are applied): `_meta.dropped_out_of_scope`, `_meta.scope_mixing_narrowed`, `_meta.scope_ambiguity_annotated`
   - **Stage-3 audit fields** (start as `[]`; populated when Stage-3 must-fixes are applied): `_meta.removed_by_strictness_audit`, `_meta.recategorized_as_other`, `_meta.dedup_canonical`
   - **Additionally required on `external_repo_dependencies.json`**: `_meta.dropped_unverifiable` (start as `[]`).
2. `_meta.verified_at` is the timestamp at which the producing researcher finished verification — use UTC ISO-8601.
3. `_meta.dropped_out_of_scope` is required (may be empty `[]`); it powers the report's Verification Footer. Same applies to the other Stage-2 / Stage-3 audit arrays — they MUST exist on every file even when empty.
4. **`_meta.search_window` schema (C5).** A 4-field subset of the canonical session-wide `search_window` object (full object lives at `out_dir/search_window.json` per the C2 schema in `SKILL.md`). Required keys: `raw_input` (the user's original input string, e.g. `"1y"`), `display` (human-readable, e.g. `"trailing 1 year (2025-05-14..2026-05-14)"`), `start_date` (`YYYY-MM-DD`), `end_date` (`YYYY-MM-DD`). Phase 0 stamps every topic JSON with this 4-field subset; researchers / analyzers / monitors MUST NOT re-parse `raw_input` and MUST consume the canonical fields from the session-wide object for any qualifier / SQL predicate strings.
5. **`_meta.fallback_used` schema (C5).** Array of fallback rows; initialize as `[]`. One entry per ref that fell back from the PRIMARY source (`mcp:signals`) to a documented fallback (typically `gh`). Each entry has the shape `{ref, tool_attempted, tool_succeeded, reason}`:
   - `ref` — the canonical PR / issue / URL identifier (e.g. `"vllm-project/vllm#1234"`).
   - `tool_attempted` — the failed tool invocation in `<source>:<recipe>` form (e.g. `"mcp:get_signal_detail"`, `"mcp:search_signals"`).
   - `tool_succeeded` — the fallback tool that actually produced the data (e.g. `"gh:pr_view"`, `"gh:issue_view"`).
   - `reason` — short human-readable cause (e.g. `"mcp returned 404"`, `"db_health failed at session start"`, `"signal_id format mismatch"`).
   The Verification Footer rolls these up into a one-line summary (e.g. `Fallback usage: 3 of 47 refs fell back from mcp:signals to gh.`). `monitor_existence` (Stage 1) RED-fails any file missing this field even when empty.
6. Per-entry shape is defined in `topics/default_topics.md` under each topic's `entry schema:` block. The researcher must follow it exactly.
7. PR / issue references inside entries MUST include the `verified_state` field set immediately before write — by `mcp:get_signal_detail` (PRIMARY per `sources/source_playbook.md` Section 0) or by `gh pr/issue view` when MCP fell back per the fallback contract.
8. Source quotes (in `perf_numbers.json`) must be VERBATIM — no comma stripping, no paraphrase. The monitor will diff against the live PR body.
