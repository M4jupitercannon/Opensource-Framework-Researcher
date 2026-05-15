<!--
ENVIRONMENT-SPECIFIC FILE. The URL recorded below is the probe target seen
at probe time on the build host and is ignored if `signals-service` is
registered under a different URL on the runtime host. The skill always
references the server by its registered name `signals-service` (per
contract clarification C7); only this discovery appendix may name the URL,
and only as a recorded probe target. Re-run Stage 1.5 to refresh.
-->

# signals-service MCP — discovered values (Stage 1.5)

```yaml
# Capability flags — Stage 2 branches on these.
MCP_DETAIL_USABLE: true    # per-PR `search_signals` + `get_signal_detail` path
MCP_SQL_USABLE:    true    # Phase 4 raw-rows `execute_sql` path
# `gh` remains the documented fallback only when MCP errors or returns no hit.
```

## Probe target (environment-specific)

- **Registered name**: `signals-service` (the only name the rest of the skill uses)
- **Probe-time URL**: `http://10.161.176.9:8082/mcp` (recorded only here; the runtime
  host may register a different URL under the same name — the skill never bakes
  the URL into committed prose per C7).
- **Protocol version**: `2024-11-05`
- **Server name / version**: `Signals Service` `1.27.0`

## Probe verdict (2026-05-14T07:04:16Z)

**signals-service is alive and both MCP paths are usable.** The live probe (run via
direct HTTP/JSON-RPC against the probe-time URL because the Cursor host hadn't
picked up the registered MCP server yet at probe time — same protocol, same data)
returned a healthy DB with **111,476 signals** (525,488 comments) over a
**1488.7 MB** database, latest sync state `running`
(`sync_vllm-project_vllm_20260514_061914_222017`, started `2026-05-14T06:19:14Z`).
`db_health()`'s `fts_integrity` field reported `database is locked` while the
sync was in flight — a transient effect of the running sync, not a service
failure — but `search_signals`, `get_signal_detail`, and `execute_sql` all
completed successfully, so **both capability flags resolve to `true`**.

## Probe results table

| Step | Probe | Status | Sample value | Notes |
|---|---|---|---|---|
| 1 | `db_health()` | OK | `signal_count=111476`, `comment_count=525488`, `db_size_mb=1488.7`, `wal_size_mb=0.5` | `fts_integrity` returned `database is locked` because sync `sync_vllm-project_vllm_20260514_061914_222017` was running; the locked state is transient and the query APIs remained usable. Re-running after sync completion returns `ok`. |
| 2 | `get_stats()` | OK | repos: `pytorch/pytorch=44946`, `vllm-project/vllm=41774`, `sgl-project/sglang=24756`; states: `closed=95158`, `open=16318`; types: `github_pr=75476`, `github_issue=36000` | All three default probe repos are indexed. |
| 3 | `search_signals(query, repos, ...)` over probe list `[vllm-project/vllm, sgl-project/sglang, pytorch/pytorch]` | OK | `search_signals(query="aiter MLA", limit=5)` returned `github:vllm-project/vllm:issue:29290` plus related PRs/issues; `search_signals(repos="sgl-project/sglang", state="open", limit=5)` returned 3,451 open results. | `repos` requires full slugs (`sglang` alone returns 0). Confirmed argument names: `query, repos, source_types, labels, state, since, until, sort, limit, offset`. |
| 4 | `get_signal_detail(signal_id, ...)` | OK | `get_signal_detail("github:vllm-project/vllm:issue:29290", include_body=false, include_comments=false)` returned title, body_preview, labels, state, references, GitHub metadata, comments preview, and the rich `github_json` blob. | Resolved `signal_id` format `github:<org>/<repo>:<pr\|issue>:<source_number>` (e.g. `github:vllm-project/vllm:pr:42434`). |
| 5 | `execute_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")` | OK | tables: `etag_cache`, `signal_changes`, `signal_comments`, `signal_gap_ids`, `signal_labels`, `signal_refs`, `signal_stats`, `signals`, `signals_fts`, `sync_runs`, plus SQLite FTS / stat tables. | The SQLite-flavoured probe replaces `SHOW TABLES`. Read-only path; returns JSON with `columns`, `rows`, `row_count`. |
| 6 | `execute_sql("SELECT * FROM signals LIMIT 1")` | OK | full 28-column schema captured below. | Confirms the canonical-string table below (e.g. `source_repo`, `source_type`, `github_labels`, `github_json` etc.). |
| 7 | Phase 4–shaped raw-rows query | OK | `execute_sql(<merged_prs template>)` returned merged PR rows for `vllm-project/vllm` and `sgl-project/sglang`; `<opened_issues template>` and `<closed_issues template>` returned issue rows for `sgl-project/sglang`. | `MCP_SQL_USABLE = true`; Phase 4 uses SQL first and falls back to `gh` only on MCP failure or miss. |

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

## Phase 4 SQL templates (verified — `execute_sql` returned rows)

The three templates below are parameterised on `<org/repo>`, `<search_window.start_date>`,
and `<search_window.end_date_plus_one_day>`. **The caller computes `<end_date_plus_one_day>`
as `<search_window.end_date> + 1 day`** so the upper bound is a half-open interval that
still includes every event on `end_date` itself. Each template returns RAW rows; the plot
agent then classifies client-side against `scope/chip_scope_map.md` and buckets into
`(month, repo, vendor_group)` to preserve the existing CSV schema
`month,repo,vendor_group,count`. Net change: O(months × repos × metrics) `gh search`
round-trips → O(repos × metrics) `execute_sql` round-trips.

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

- Confirm `signals-service` is registered in the host MCP config at `~/.cursor/mcp.json`
  (or the host agent's equivalent). The skill always references the server by its
  registered name — the URL recorded above is environment-specific and ignored if
  the runtime host registers a different URL under the same name.
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
- Persist both flags + the canonical strings back into this file. Stage 2 sub-agents
  (`agents/researcher.md`, `agents/analyzer_external_repos.md`,
  `agents/monitor_*.md`, `agents/plot_ecosystem_activity.md`) do NOT need to be
  re-spawned — they already gate their MCP recipes on `MCP_DETAIL_USABLE` /
  `MCP_SQL_USABLE` so flipping the flags activates / deactivates the MCP path at
  runtime.
