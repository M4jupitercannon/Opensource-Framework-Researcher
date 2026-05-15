# signals-service MCP — redacted discovery guide (Stage 1.5)

This appendix records portable schema strings and query shapes for a
`signals-service` MCP server registered under the name `signals-service`.
It intentionally does **not** record actual MCP URLs, build-machine row counts,
sync IDs, or current capability verdicts.

At runtime, the main agent still runs the MCP pre-flight (`db_health()` and
`get_stats()`), resolves the per-host `MCP_DETAIL_USABLE` and `MCP_SQL_USABLE`
flags, and writes those actual values to `out_dir/_signals_schema.json`. Treat
the placeholders below as examples to refresh during Stage 1.5, not as a claim
that any new host has MCP detail or SQL support enabled.

```yaml
# Runtime capability flags — write actual values to out_dir/_signals_schema.json.
MCP_DETAIL_USABLE: <true|false>  # per-PR `search_signals` + `get_signal_detail` path
MCP_SQL_USABLE:    <true|false>  # Phase 4 raw-rows `execute_sql` path
# `gh` remains the documented fallback when MCP errors, returns no hit,
# or db_health() fails at session start.
```

## Probe target (redacted)

- **Registered name**: `signals-service` (the only name the rest of the skill uses)
- **Configured URL**: `<host MCP config value; do not commit actual URLs>`
- **Protocol version**: `<reported by server>`
- **Server name / version**: `<reported by server>`

## Probe checklist

| Step | Probe | Record |
|---|---|---|
| 1 | `db_health()` | Health summary in `out_dir/_signals_schema.json`; do not commit host row counts or transient sync state. |
| 2 | `get_stats()` | Repo/state/type coverage summary in `out_dir/_signals_schema.json`; do not commit host-specific counts. |
| 3 | `search_signals(query, repos, ...)` over a small known-repo list | Confirm accepted argument names and whether full repo slugs are required. |
| 4 | `get_signal_detail(signal_id, ...)` | Confirm `signal_id` format and detail field availability. |
| 5 | `execute_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")` | Confirm SQL access and table names when SQL is available. |
| 6 | `execute_sql("SELECT * FROM signals LIMIT 1")` | Refresh the portable canonical-string table below if columns drift. |
| 7 | One Phase 4–shaped raw-rows query | Confirm whether `MCP_SQL_USABLE` should be true for this runtime host. |

## Resolved canonical strings

| Placeholder | Resolved value |
|---|---|
| `signal_id_format` | `github:<org>/<repo>:<pr\|issue>:<source_number>` (e.g. `github:vllm-project/vllm:pr:42434`, `github:pytorch/pytorch:pr:182808`) |
| `signals_table` | `signals` |
| `repo_column` | `source_repo` (TEXT, e.g. `vllm-project/vllm`) |
| `repo_predicate` | `source_repo = '<org/repo>'` |
| `number_column` | `source_number` (INTEGER, PR/issue number) |
| `title_column` | `title` |
| `labels_column_json` | `github_labels` (TEXT, JSON array) |
| `labels_column_relational` | `signal_labels.label` (joined via `signal_labels.signal_id = signals.signal_id`) |
| `is_pr_predicate` | `source_type = 'github_pr'` (preferred over `github_is_pr = 1`; same result) |
| `is_issue_predicate` | `source_type = 'github_issue'` |
| `created_at_column` | `created_at` (top-level TEXT, ISO 8601 UTC) |
| `updated_at_column` | `updated_at` (top-level TEXT, ISO 8601 UTC) |
| `merged_at_expr` | `json_extract(github_json, '$.pr_merged_at')` (nested; null when not merged) |
| `merged_filter_expr` | `json_extract(github_json, '$.pr_merged') = 1` |
| `closed_at_expr` | `json_extract(github_json, '$.closed_at')` (nested; null when open) |
| `date_filter_supported_in_search_signals` | yes — `since` / `until` ISO 8601 UTC, **bounded on `updated_at`** (not `created_at` / `merged_at` / `closed_at`) |

## `signals` table schema (28 columns)

```
rowid                INTEGER
signal_id            TEXT        -- "github:<org>/<repo>:<pr|issue>:<N>"
source_type          TEXT        -- "github_pr" | "github_issue"
source_url           TEXT        -- "https://github.com/<org>/<repo>/{pull|issues}/<N>"
source_repo          TEXT        -- "<org>/<repo>"
source_number        INTEGER     -- PR/issue number
title                TEXT
body                 TEXT
body_token_estimate  INTEGER
author               TEXT
created_at           TEXT        -- ISO 8601 UTC (e.g. "2026-05-12T15:32:13Z")
updated_at           TEXT        -- ISO 8601 UTC
first_seen_at        TEXT
last_synced_at       TEXT
content_hash         TEXT
version              INTEGER
sync_run_id          TEXT
references_json      TEXT        -- JSON: {github_issues, github_prs, external_urls, mentions}
tags                 TEXT        -- JSON array
github_json          TEXT        -- JSON blob: state, labels, assignees, comment_count, closed_at,
                                 --            closed_by, is_pr, pr_merged, pr_merged_at,
                                 --            pr_changed_files{total,additions,deletions,files,
                                 --                             rocm_specific,cuda_specific,shared},
                                 --            pr_review_comments
github_state         TEXT        -- "open" | "closed" (no "merged"; merged-ness lives in github_json.pr_merged)
github_labels        TEXT        -- JSON array (also pivoted to signal_labels table)
github_is_pr         INTEGER     -- 0/1
github_comment_count INTEGER
twitter_json         TEXT
arxiv_json           TEXT
classification_json  TEXT
gap_ids              TEXT        -- JSON array
```

Other relevant tables: `signal_labels(signal_id, label)` (relational pivot of `signals.github_labels`,
use for label-AND-of-many queries), `signal_comments`, `signal_refs`, `signal_changes`,
`signal_gap_ids`, `signal_stats`, `etag_cache`, `sync_runs`, and the FTS5 virtual table
`signals_fts` (queried only via `search_signals(query=...)`).

## Phase 4 SQL templates (schema example)

The three templates below are parameterised on `<org/repo>`, `<search_window.start_date>`,
and `<search_window.end_date_plus_one_day>`. **The caller computes `<end_date_plus_one_day>`
as `<search_window.end_date> + 1 day`** so the upper bound is a half-open interval that
still includes every event on `end_date` itself. Each template returns RAW rows; the plot
agent then classifies client-side against `scope/chip_scope_map.md` and buckets into
`(month, repo, vendor_group)` to preserve the existing CSV schema
`month,repo,vendor_group,count`. When the runtime host confirms
`MCP_SQL_USABLE=true`, this changes O(months × repos × metrics) `gh search`
round-trips into O(repos × metrics) `execute_sql` round-trips.

### `merged_prs` for one (`repo`, window)

```sql
SELECT
  source_number,
  title,
  github_labels,
  json_extract(github_json, '$.pr_merged_at') AS merged_at,
  source_repo
FROM signals
WHERE source_repo = '<org/repo>'
  AND source_type = 'github_pr'
  AND json_extract(github_json, '$.pr_merged') = 1
  AND json_extract(github_json, '$.pr_merged_at') >= '<search_window.start_date>'
  AND json_extract(github_json, '$.pr_merged_at') <  '<search_window.end_date_plus_one_day>'
ORDER BY merged_at;
```

### `opened_issues` for one (`repo`, window)

```sql
SELECT
  source_number,
  title,
  github_labels,
  created_at,
  source_repo
FROM signals
WHERE source_repo = '<org/repo>'
  AND source_type = 'github_issue'
  AND created_at >= '<search_window.start_date>'
  AND created_at <  '<search_window.end_date_plus_one_day>'
ORDER BY created_at;
```

### `closed_issues` for one (`repo`, window)

```sql
SELECT
  source_number,
  title,
  github_labels,
  json_extract(github_json, '$.closed_at') AS closed_at,
  source_repo
FROM signals
WHERE source_repo = '<org/repo>'
  AND source_type = 'github_issue'
  AND json_extract(github_json, '$.closed_at') >= '<search_window.start_date>'
  AND json_extract(github_json, '$.closed_at') <  '<search_window.end_date_plus_one_day>'
ORDER BY closed_at;
```

## `search_signals` date-filter note

`search_signals` exposes `since` and `until` (ISO 8601 UTC, e.g. `2026-04-20T00:00:00Z`),
but **both bounds filter on `updated_at`** — NOT on `created_at`, `pr_merged_at`, or
`closed_at`. Consequences:

- Per-metric windowing for Phase 4 (`merged_prs` over `pr_merged_at`, `opened_issues` over
  `created_at`, `closed_issues` over `closed_at`) MUST use the `execute_sql` path above for
  date accuracy. The `search_signals(since, until)` shape would catch any signal *touched*
  in the window, including merged/closed/created outside it.
- Reserve `search_signals(since, until)` for catch-up / change-feed lookups (e.g. "what
  has changed in the last day across repos X / Y") where activity-window semantics are
  acceptable.
- Phase-1 researchers / Phase-2 monitor re-samples doing per-PR / per-issue lookups
  should pass `since` / `until` only as a coarse pre-filter and then confirm
  per-metric timestamps from the returned `github_json` blob (`pr_merged_at`,
  `closed_at`, etc.) before claiming inclusion in the window.

## Re-probe instructions

To refresh this file on a host where `signals-service` is registered:

- Confirm `signals-service` is registered in the host MCP config (for example
  `~/.cursor/mcp.json`, or that host agent's equivalent). The skill always
  references the server by its registered name; do not write actual MCP URLs into
  committed docs.
- Pre-flight: `db_health()` (expect `signal_count > 0`, `fts_integrity = "ok"` when no
  sync is in flight) and `get_stats()` (expect per-repo / per-state / per-type totals).
- `search_signals` iteration over the probe-repo list
  `[vllm-project/vllm, sgl-project/sglang, pytorch/pytorch]` with a known-title query
  (e.g. `query="aiter MLA"`); accept the first repo returning ≥1 result; capture the
  exact `signal_id` shape from the returned `signal_id` field.
- `get_signal_detail(signal_id=<from previous step>, include_body=false, include_comments=false)`
  to confirm `MCP_DETAIL_USABLE`.
- `execute_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")` and
  `execute_sql("SELECT * FROM signals LIMIT 1")` to confirm the canonical-string table
  above; if columns drifted, refresh the table accordingly.
- One Phase 4–shaped `execute_sql(<merged_prs template>)` call against one of the
  probe repos to confirm `MCP_SQL_USABLE`.
- Persist both flags + any host-specific probe results to
  `out_dir/_signals_schema.json`. Update this committed file only for portable
  schema strings, redacted examples, or query-template changes. Delegated roles
  (`agents/researcher.md`, `agents/analyzer_external_repos.md`,
  `agents/monitor_*.md`, `agents/plot_ecosystem_activity.md`) do NOT need to be
  re-run just because runtime flags changed — they gate their MCP recipes on
  `MCP_DETAIL_USABLE` / `MCP_SQL_USABLE` at runtime.
