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
    "scope": "NVIDIA datacenter GPUs only — Hopper (SM89/SM90), Blackwell (SM100/SM120). Out: SM80, SM86, SM103, SM121.",
    "in_scope": ["SM89", "SM90", "SM100", "SM120"],
    "sources_used": ["gh", "WebFetch:docs.vllm.ai"],   // see sources/source_playbook.md
    "verified_at": "2026-04-23T00:00:00Z",
    "dropped_out_of_scope": [                          // items considered but discarded
      {"ref": "issue #40419", "reason": "B300/SM103 — out of scope"}
    ],
    "verifications_run": 36                            // number of gh/WebFetch calls made
  },
  "entries": [ /* entries follow the per-topic schema in topics/default_topics.md */ ]
}
```

## Rules

1. `_meta.scope` and `_meta.sources_used` are REQUIRED. Files missing either will be rejected by the monitor.
2. `_meta.verified_at` is the timestamp at which the producing researcher finished verification — use UTC ISO-8601.
3. `_meta.dropped_out_of_scope` is required (may be empty `[]`); it powers the report's Verification Footer.
4. Per-entry shape is defined in `topics/default_topics.md` under each topic's `entry schema:` block. The researcher must follow it exactly.
5. PR / issue references inside entries MUST include the `verified_state` field set by `gh`-checking immediately before write.
6. Source quotes (in `perf_numbers.json`) must be VERBATIM — no comma stripping, no paraphrase. The monitor will diff against the live PR body.
