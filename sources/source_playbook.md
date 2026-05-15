# Source playbook

Each researcher worker receives this file and chooses sources per topic. Every fact in a topic JSON must be traceable to one of the source IDs below; the researcher records which sources it used in `_meta.sources_used` (e.g. `["mcp:signals", "gh", "web_fetch:docs.vllm.ai", "inferencex"]`).

---

## 0. `mcp:signals` — signals-service MCP server (PRIMARY for GitHub PR/issue lookups)

**`mcp:signals` is the PRIMARY source for any GitHub PR / issue / RFC lookup; `gh` (Section 1) is the DOCUMENTED FALLBACK.** Every researcher / analyzer / monitor that needs PR or issue data MUST try MCP first per the **Fallback contract** below.

The MCP server is referenced by its **registered name** `signals-service` only. The URL lives in the **host's** MCP config (per-host paths below) and is environment-specific — committed docs MUST NOT contain actual MCP URLs. The Stage-1.5 discovery appendix `sources/signals_service_discovered.md` uses redacted placeholders and portable schema examples (per C7).

### Per-host MCP setup

Configure `signals-service` in your host's MCP config before running the skill. Paths and registration syntax differ per host:

| Host | Config path | Registration command / snippet |
|---|---|---|
| Claude Code | `~/.claude.json` | `claude mcp add signals-service <command-or-url>` (CLI writes the entry into the file) |
| Cursor | `~/.cursor/mcp.json` | JSON `mcpServers` entry: `{"mcpServers": {"signals-service": {"command": "...", "args": ["..."]}}}` |
| Codex | `~/.codex/config.toml` | TOML block: `[mcp_servers.signals-service]` with `command`, `args`, optional `env` (verify on your Codex version) |
| opencode | `~/.config/opencode/opencode.json` (or `opencode.jsonc`) | JSON `mcp` entry: `{"mcp": {"signals-service": {"type": "local", "command": ["..."], "enabled": true}}}` for a local server, or `{"type": "remote", "url": "..."}` for a remote server (verify on your opencode version) |

If any path differs on your installed host version, update the host's MCP config according to that host's documentation; the skill only requires that the server be reachable under the registered name `signals-service`.

**When**: any claim about a PR, issue, or release in the framework's repo (Phase 1 fetches, Phase 2 monitor re-samples, and optional Phase 4 `fresh_search`). For external-repo refs (Phase 1b analyzer), still try `mcp:signals` first since signals-service indexes many ecosystem repos; on miss, fall back to `gh` per the contract.

### Resolved recipes (from Stage 1.5 discovery)

The Stage-1.5 discovery appendix records the portable `signal_id` format, SQL column
names, and Phase 4 templates in `sources/signals_service_discovered.md`.
Researchers / analyzers / monitors / plot agents MUST consume that appendix for
canonical strings and MUST NOT invent a different `signal_id` or SQL schema.

```text
# Pre-flight (run once per session, before Phase 0)
db_health()                                                   # → returns {ok: bool, ...}
get_stats()                                                   # → returns {row_count, tables[], latest_update_ts, ...}

# Per-PR / per-issue search (Phase 1 fetch, Phase 2 monitor re-sample)
search_signals(
    query="<keywords>",
    repos="<org/repo>",                                       # full slug required; "sglang" is not enough
    source_types="github_issue|github_pr",
    state="open|closed|all",
    since="<search_window.start_date>T00:00:00Z",             # filters updated_at
    until="<search_window.end_date_plus_1>T00:00:00Z",
    sort="updated|created|relevance",
    limit=20
)

# Per-PR / per-issue body fetch (Phase 2 monitor re-sample)
get_signal_detail(
    signal_id="<as-discovered — see sources/signals_service_discovered.md; current shape: github:<org>/<repo>:<pr|issue>:<source_number>>",
    include_body=true|false,
    include_comments=true|false
)

# Optional Phase 4 fresh_search raw-rows pattern (one query per (repo, metric) over the full window)
execute_sql("<probed-schema-aware-SQL>")                       # resolved template in Stage 1.5 probe appendix;
                                                               # see `sources/signals_service_discovered.md`
                                                               # for the resolved Phase 4 SQL template.
```

**Date-filter and SQL details are resolved from the discovery appendix** in
`sources/signals_service_discovered.md`. `search_signals` supports `since` /
`until` over `updated_at`; optional Phase 4 fresh_search metric bucketing uses SQL because created,
merged, and closed timestamps are separate fields / JSON paths. If a future
probe changes the schema, update the appendix and keep this playbook pointing to
the appendix rather than duplicating environment-specific details.

### Discovery protocol (per C6)

Two capability flags govern which MCP paths are usable in the current run:

- `MCP_DETAIL_USABLE` — controls the per-PR MCP path (used by Phase-1 researchers and Phase-2 monitors), i.e. per-ref `search_signals` + `get_signal_detail`. True iff `db_health()` passes AND a known-PR `search_signals` round-trip returns a usable `signal_id`. Defaults to **False** if `db_health()` errors.
- `MCP_SQL_USABLE` — controls the optional Phase 4 `fresh_search` SQL raw-rows path (used by the plot role), i.e. the Phase 4 raw-rows pattern per C8. True iff `MCP_DETAIL_USABLE` is True AND a probed `execute_sql("SELECT ... LIMIT 5")` against the discovered schema succeeds. Defaults to **False** if `db_health()` errors.

Both flags fold into a single `data_source` variable: `mcp_first` when either flag is True, `gh_only` when both are False.

**Discovery sequence** (executed once per session by the main agent, formalized as Stage 1.5 in the build plan):

1. **Session-start pre-flight.** Call `db_health()` and `get_stats()`. If `db_health` errors, set both flags to False and `data_source=gh_only`; skip the rest of the discovery sequence.
2. **`signal_id` format probe.** Iterate the small fixed probe-repo list `["vllm-project/vllm", "sgl-project/sglang", "pytorch/pytorch"]` and call `search_signals(query="<known title>", repos="<org/repo>")` against each in turn. Accept the **first** repo that returns ≥1 result (per C6.E — a single repo's absence from the signals DB does not falsely conclude the service is broken). Record the exact `signal_id` field shape (e.g. `<org/repo>#<N>` vs `<repo>:<N>` vs numeric vs URL), the available result fields, and whether `since` / `until` or any other date filter is accepted by `search_signals`.
3. **`get_signal_detail` round-trip.** Using a `signal_id` from step 2, call `get_signal_detail(..., include_body=false)` and record the field set. On success, set `MCP_DETAIL_USABLE=True`. If all three probe repos returned empty AND no error, treat the service as alive but unindexed: `MCP_DETAIL_USABLE=False` and continue to step 4.
4. **Schema probe.** Call `execute_sql("SHOW TABLES")` (or `SELECT name FROM sqlite_master`, `\dt` — try variants). Cache the table list. For each interesting table, call `execute_sql("SELECT * FROM <table> LIMIT 1")` to record column names + types. If all variants error, set `MCP_SQL_USABLE=False` and skip step 5.
5. **Phase 4 fresh-search shape probe.** Try one Phase 4–shaped raw-rows query against the discovered schema (per C8 — RAW rows over the full window, NOT pre-aggregated). On success set `MCP_SQL_USABLE=True`; on failure set False and record the error string.
6. **Persist.** Persist the discovered values + both flags to `out_dir/_signals_schema.json`. Update the committed `sources/signals_service_discovered.md` only when portable schema strings or redacted examples change; do not commit host-specific verdict flags or actual MCP URLs. Stage 2 delegated roles reference these strings at runtime.

### Fallback contract (verbatim across all role prompts)

> Try MCP via <recipe> FIRST. If MCP errors, returns no hit, or db_health() failed at session start, fall back to <gh recipe> and append a row to _meta.fallback_used.

Each fallback row records `{ref, tool_attempted, tool_succeeded, reason}` per the C5 schema in `topics/topic_json_schema.md`.

### Open-issue semantics (per C3)

For the Phase-1a `open_issues` topic and "currently open" monitor lookups, **"in window" means `state:open AND updated:in_window`** (activity-based windowing, not creation-based). Long-lived important tickets that pre-date the window but were updated within it MUST be included; conversely, long-stale `state:open` tickets that were not touched in the window are excluded. Researchers use `{search_window.gh_qualifier_issue_updated}` from the C2 `search_window` object verbatim.

For Phase 4 metrics the per-metric bucket field is unchanged and per-metric:
- `merged_prs` → bucket by `merged_at` / `mergedAt`
- `opened_issues` → bucket by `created_at` / `createdAt`
- `closed_issues` → bucket by `closed_at` / `closedAt`

(Stage 1.5 resolves which underscore-or-camelCase variant the live signals-service exposes; until then, treat both forms as candidates.)

### Phase 4 source modes (per C8)

Default `ecosystem_plot_source=topic_jsons` performs no live source lookup. The plot role runs `scripts/build_ecosystem_activity_from_topics.py` over `out_dir/{vendor}/topics/*.json` after Phase 1-3 monitor fixes, skips `external_repo_dependencies.json` because those refs belong to external repos, de-duplicates refs by `(vendor, repo, kind, number)`, buckets by the metric timestamp, and emits the same CSV shape: `month,repo,vendor_group,count`. This is a simple statistic over audited run evidence, not an exhaustive ecosystem search.

Optional `ecosystem_plot_source=fresh_search` uses the raw-rows pattern below.

The single `execute_sql` per `(repo, metric)` returns **RAW rows** `(number, title, labels, mergedAt|createdAt|closedAt, repo)` over the full `search_window` — NOT pre-aggregated. The plot agent then runs client-side classification (title + labels keyword match against `scope/chip_scope_map.md`): cross-vendor rows are counted once under each matched vendor, and hardware-agnostic rows are dropped from the CSV. The CSV shape remains `month,repo,vendor_group,count`; `BOTH` / `NEITHER` literals are no longer emitted.

Fresh-search net change versus the old per-month loop: O(months × repos × metrics) round-trips → O(repos × metrics) round-trips, identical classification logic, identical CSV schema. Gated by `MCP_SQL_USABLE`; when False, the optional Phase 4 SQL raw-rows path uses the Section-6 `gh search` per-month loop as the only path. The resolved Phase 4 SQL template (with real column names interpolated) lives in `sources/signals_service_discovered.md`.

---

## 1. `gh` — GitHub CLI (DOCUMENTED FALLBACK)

`gh` is the DOCUMENTED FALLBACK for any per-PR / per-issue / per-RFC lookup and per-PR re-sample. It runs whenever the `mcp:signals` Section-0 path errors, returns no hit, or `db_health()` failed at session start (per the **Fallback contract** above). It also remains the verified path for Phase 4's optional `fresh_search` per-month loop when `MCP_SQL_USABLE=False`.

**When**: any claim about a PR, issue, RFC, or release in the framework's repo where the Section-0 MCP path is unavailable per the fallback contract.

**Recipes**:
```bash
# verify a single PR
gh pr view <N> --repo <org/repo> --json number,title,state,mergedAt,body,labels,author

# verify a single issue / RFC
gh issue view <N> --repo <org/repo> --json number,title,state,createdAt,labels,body,author

# search merged PRs touching a feature
gh pr list --repo <org/repo> --state merged --search '<keywords> in:title,body' --limit 100 \
  --json number,title,mergedAt,labels

# search open issues
gh issue list --repo <org/repo> --state open --search '<keywords>' --limit 100 \
  --json number,title,createdAt,labels,state

# bulk via API (for >100 items or label-only queries)
gh api 'search/issues?q=repo:<org/repo>+<keywords>+is:open&per_page=100'
```

**Framework → repo map** (extend by editing this file):

| Framework | Repo |
|---|---|
| vLLM | `vllm-project/vllm` |
| SGLang | `sgl-project/sglang` |
| TGI (Text Generation Inference) | `huggingface/text-generation-inference` |
| TensorRT-LLM | `NVIDIA/TensorRT-LLM` |
| llama.cpp | `ggerganov/llama.cpp` |
| MLC-LLM | `mlc-ai/mlc-llm` |
| LMDeploy | `InternLM/lmdeploy` |
| FasterTransformer | `NVIDIA/FasterTransformer` |
| DeepSpeed-FastGen | `deepspeedai/DeepSpeed-MII` |
| vAttention | `microsoft/vattention` |

If the framework arg is not in this map, the main agent must ask the user for the `org/repo` (or accept `gh_repo_override`) before Phase 0 completes.

---

## 2. Host web-fetch capability — vendor docs, RFC pages, release notes

**When**: official documentation, blog posts (when the URL is known), framework release notes, RFC discussion pages.

**Useful hosts**:
- NVIDIA: `docs.nvidia.com`, `developer.nvidia.com/blog`
- AMD: `rocm.docs.amd.com`, `community.amd.com/t5/instinct-accelerators`
- Intel: `intel.com/content/www/us/en/developer/tools/...`, `habana.ai/blog`
- Google: `cloud.google.com/tpu/docs`, `cloud.google.com/blog`
- Framework docs: `docs.vllm.ai`, `docs.sglang.ai`, `huggingface.co/docs/text-generation-inference`
- PyTorch blog: `pytorch.org/blog`

Always pass a SPECIFIC extraction prompt to the host's web-fetch capability or equivalent (e.g. "Extract the section about FP8 grouped GEMM kernel for MI355X").

---

## 3. Host web-search capability — discovery (when the URL is unknown)

**When**: looking for blog posts / talks / vendor announcements about `{feature}` on `{chip}` for `{framework}` whose URL is not known. Always cross-reference with a host web fetch of the result before quoting.

Use specific queries like:
```
{framework} {feature} {chip-vendor} {chip-codename} performance benchmark
{framework} {feature} {chip-vendor} announcement 2026
```

Restrict with `allowed_domains` to vendor / framework hosts when possible.

---

## 4. MLPerf — public benchmark cross-check

**When**: corroborating perf claims for a chip+model combination.

**Source**:
- Inference Datacenter: `https://mlcommons.org/benchmarks/inference-datacenter/`
- Results CSVs: `https://github.com/mlcommons/inference_results_v5.0/` (replace version per current round)

Use host web fetch against the results page or `gh` against the `mlcommons/inference_results_v*` repo for a specific submission.

---

## 5. SemiAnalysis InferenceX — third-party perf reference

**When**: cross-checking framework-claimed perf numbers, finding alternative configurations, or sanity-checking absolute throughput.

**Source**: `https://github.com/SemiAnalysisAI/InferenceX`. Configs live under `.github/configs/{vendor}-master.yaml` (e.g. `nvidia-master.yaml`, `amd-master.yaml`).

Recipes:
```bash
gh api repos/SemiAnalysisAI/InferenceX/contents/.github/configs/<vendor>-master.yaml -H "Accept: application/vnd.github.raw"
gh search code 'in:file repo:SemiAnalysisAI/InferenceX <feature>' --limit 50
```

---

## 6. `gh-search-bulk` — feature-activity time-series queries (optional Phase 4 fresh_search)

**When**: only when `ecosystem_plot_source=fresh_search` and MCP SQL is unavailable or unusable. The Phase 4 `plot_ecosystem_activity` role bulk-fetches merged PRs / opened issues / closed issues per `(repo, month)` to build a time-series CSV. Default `topic_jsons` mode does not use this section. **Do NOT** use these recipes for per-feature research in Phase 1 — those topics use the per-PR `gh pr view` / `gh issue view` flow above.

**Vendor classification keywords** for these queries are derived at runtime from `scope/chip_scope_map.md` (the same canonical map Phase 0 uses). Do NOT introduce a parallel keyword file. See `agents/plot_ecosystem_activity.md` for the parsing rules (aliases + in_scope codenames, with a few generic-prefix tokens dropped).

**Recipes (one bucket = one calendar month per repo per metric)**:
```bash
# merged PRs in a month
gh search prs --repo <org/repo> \
  --merged-at YYYY-MM-01..YYYY-MM-LAST \
  --json number,title,labels,url \
  --limit 1000

# opened issues in a month
gh search issues --repo <org/repo> --include-prs=false \
  --created YYYY-MM-01..YYYY-MM-LAST \
  --json number,title,labels,url \
  --limit 1000

# closed issues in a month
gh search issues --repo <org/repo> --include-prs=false \
  --closed YYYY-MM-01..YYYY-MM-LAST \
  --json number,title,labels,url \
  --limit 1000

# fallback when `gh search` rejects an option in the installed gh version
gh api 'search/issues?q=repo:<org/repo>+is:pr+is:merged+merged:YYYY-MM-DD..YYYY-MM-DD&per_page=100'
```

**Bucket field per metric** (must not be mixed within one CSV):

| Metric | Search qualifier | Bucket field |
|---|---|---|
| `merged_prs` | `is:pr is:merged merged:<range>` | `mergedAt` |
| `opened_issues` | `is:issue created:<range>` | `createdAt` |
| `closed_issues` | `is:issue is:closed closed:<range>` | `closedAt` |

**Pagination + 1000-hit ceiling.** GitHub's Search API caps at ~1000 results per query. If a single (repo, month) bucket would exceed that, split the month into halves on the same qualifier (`merged:YYYY-MM-01..YYYY-MM-15` then `merged:YYYY-MM-16..YYYY-MM-LAST`) and union the result sets, deduping by `number`.

**Classification.** Use entry `title` and each `labels[*].name` only — do NOT bulk-fetch bodies (would multiply API cost ~100×). Entries matching multiple vendor groups emit one CSV row per matched vendor; entries matching no vendor group are dropped from the CSV. Record both the cross-vendor count and the dropped hardware-agnostic count in `<metric>_methods.md`.

---

## Source-tag conventions

In `_meta.sources_used` use these tags exactly:
- `mcp:signals` — any `signals-service` MCP server call (`db_health`, `get_stats`, `search_signals`, `get_signal_detail`, `execute_sql`). Per Section 0, this is the PRIMARY tag for per-PR / per-issue lookups and the optional Phase 4 fresh-search raw-rows pattern.
- `gh` — any GitHub CLI / API call (per-PR / per-issue / scoped `--search`). Per Section 1, this is the DOCUMENTED FALLBACK for `mcp:signals`. Whenever a fallback occurs, the researcher / monitor MUST also append a row to `_meta.fallback_used` per the C5 schema.
- `gh-search-bulk` — optional Phase 4 fresh-search bulk monthly Search queries (Section 6); paired with the methods note for reproducibility. Used as the Phase 4 fallback path when `MCP_SQL_USABLE=False` and `ecosystem_plot_source=fresh_search`.
- `web_fetch:<host>` — e.g. `web_fetch:docs.vllm.ai`
- `web_search` — discovery search (the follow-up host web fetch is logged separately)
- `mlperf` — MLPerf data
- `inferencex` — SemiAnalysis InferenceX data
