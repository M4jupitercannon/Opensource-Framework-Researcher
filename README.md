# Opensource-Framework-Researcher

A cross-agent research workflow for Claude Code, Cursor, Codex, and opencode. It investigates one **(chip vendor, framework, feature)** triple in the open-source AI inference / training ecosystem and emits dashboard-ready outputs.

Examples of triples this skill handles:

- `NVIDIA + vLLM + EP` (Expert Parallelism)
- `AMD + SGLang + PD-disaggregation`
- `NVIDIA + TensorRT-LLM + speculative-decoding`
- `Google + JAX + paged-KV` *(if your framework→repo map is extended)*

It generalizes the methodology of a hand-run vLLM-EP investigation. The main agent synthesizes a single highlighted Markdown report from per-topic JSON files produced by the pipeline below:

- **Phase 1a (research)** — 5 default researcher roles cover the default topics in parallel.
- **Phase 1b (analyzer)** — 1 external-repo analyzer derives `external_repo_dependencies.json` from three of the Phase-1a outputs.
- **Phase 2 (verification)** — three serial monitors (existence, chip-vendor scope, feature strictness) independently re-check every PR / issue / URL.
- **Data sources** — `signals-service` MCP server first, falling back to the GitHub CLI and web fetch when needed.
- **Phase 4 / Phase 5 (optional context)** — best-effort ecosystem activity plot, and a side-by-side comparison report when `len(chip_list) == 2`.

When the host agent supports delegated workers (Claude Code, Cursor, or similar), Phase 1a can run in parallel. In Codex or any environment without worker delegation, use the serial fallback mode described in `SKILL.md` and `AGENTS.md`.

## What you get per run

Under `~/research/{framework}_{feature}/{YYYY-MM-DD}/` (per-vendor outputs live under `out_dir/{vendor}/` for multi-vendor runs):

| File | Purpose |
|---|---|
| `search_window.json` | Canonical session-wide time-window object (C2 schema) that bounds every Phase 1 PR/issue search and the Phase 4 plot window. Written once at Phase 0. |
| `_signals_schema.json` | MCP pre-flight result for this run: the `MCP_DETAIL_USABLE` / `MCP_SQL_USABLE` capability flags plus any discovered canonical strings from `sources/signals_service_discovered.md`. |
| `{vendor}/topics/*.json` | One file per research topic, **stable schema** — feed straight into a dashboard. Each `_meta` carries the 4-field `search_window` subset and a `fallback_used` array (one row per `mcp:signals → gh` fallback). |
| `{vendor}/scope.json` | Auto-derived chip-vendor scope (in/out SKUs) used for filtering. |
| `{vendor}/verification_existence.md` | Stage 1 audit (PR/issue/URL existence + verbatim quotes + `_meta.search_window` / `_meta.fallback_used` present), with verdict `GREEN` / `YELLOW` / `RED` and must-fix punch list. |
| `{vendor}/verification_scope.md` | Stage 2 audit (chip-vendor scope strictness), with verdict and must-fix punch list. |
| `{vendor}/verification_feature.md` | Stage 3 audit (feature strictness), with verdict and must-fix punch list. |
| `ecosystem_plots/<metric>_by_vendor.{png,csv}` + `<metric>_methods.md` | Optional Phase 4 ecosystem activity charts (one set per chosen metric: `merged_prs`, `opened_issues`, `closed_issues`). Top-level path (per C8.1) — Phase 4 runs once per session, not per vendor; `vendor_group` values mirror the run's `chip_list` (per C8.2). Best-effort context outside the three-stage audit; vendor classification is derived from `scope/chip_scope_map.md` at runtime. If the user picks `ecosystem_plot_metric=skip`, the directory is not created; the run still continues to Phase 5 when `len(chip_list) == 2` (and to Phase 6 otherwise). |
| `{vendor}/REPORT.md` | Synthesized human-readable per-vendor report — At-a-Glance dashboard table + one section per topic with a primary table optimized for dashboard ingestion (and an optional `## Ecosystem Activity Context` section when Phase 4 ran). |
| `COMPARISON_REPORT.md` | Side-by-side comparison report rendered by Phase 5, **only when exactly two vendors were researched** (per C4). Embeds the Phase 4 ecosystem plots from top-level `ecosystem_plots/` via `[render_if_present ecosystem_plots]`. |

Section headings use **named topics** (e.g. `## Completed Subfeatures`, `## Open Issues`, `## Roadmap`, `## Performance Numbers`, `## Kernels & Components`) — never `Q1`/`Q2`/etc. — so dashboards can bookmark stable anchors.

## Default research topics

| Topic name (filename stem) | Heading | What it answers |
|---|---|---|
| `completed_subfeatures` | Completed Subfeatures | What has merged for this feature, by subfeature, with landmark PRs. |
| `open_issues` | Open Issues | Currently open issues per subfeature, with severity. |
| `roadmap` | Roadmap | Official roadmap items + recent RFCs. |
| `perf_numbers` | Performance Numbers | Verified perf gains, each backed by a verbatim source quote. |
| `kernels_or_components` | Kernels & Components | Low-level kernels / libraries on the critical path (DeepGEMM, CUTLASS, FlashInfer, hipBLASLt, …). |
| `external_repo_dependencies` | External Repo Dependencies | External open-source repos each completed subfeature depends on or contributes back to (kernel libs, comm libs, etc.). Produced by a Phase-1b analyzer, not a generic researcher. |

Note: `external_repo_dependencies` is produced by an analyzer sub-agent in Phase 1b, not a generic Phase-1a researcher. It requires `completed_subfeatures`, `kernels_or_components`, and `open_issues` to exist on disk first.

Topics are user-configurable: pass a subset to limit scope, or supply custom topic specs (name + prompt + entry schema).

## Sources

| Source | Role | Notes |
|---|---|---|
| `signals-service` MCP server (source tag `mcp:signals`) | **Primary** for PR / issue / RFC lookups in the framework repo. | Referenced by its registered name only — the URL is configured at install/host time in your host's MCP config (per-host paths listed in the **Per-host MCP setup** table in `sources/source_playbook.md`) and is **not** baked into committed docs (per C7). See **Data sources / MCP-first** below for the pre-flight + capability-flag contract. |
| `gh` (GitHub CLI, source tag `gh`) | **Documented fallback** when MCP errors, returns no hit, or `db_health()` failed at session start. | Falls produce one row in each affected topic JSON's `_meta.fallback_used` array (per C5). |
| `WebFetch` | Vendor docs, framework release notes, RFC pages. | |
| `WebSearch` | Discovery of blogs / announcements. | |
| MLPerf | Public chip-vs-chip benchmark cross-check. | |
| [SemiAnalysis InferenceX](https://github.com/SemiAnalysisAI/InferenceX) | Third-party perf reference. | |

## Compatibility

| Environment | Entry point | Notes |
|---|---|---|
| Claude Code | `SKILL.md` | `install.sh` installs under `~/.claude/skills/feature-research`; invoke naturally (e.g. "Use feature-research for NVIDIA + vLLM + EP"). |
| Cursor | `SKILL.md` | `install.sh` installs under `~/.cursor/skills/feature-research`; invoke naturally (e.g. "Use feature-research for NVIDIA + vLLM + EP") or attach as context. |
| Codex | `AGENTS.md` | `install.sh` installs a repo link under `~/.codex/skills/feature-research` and a managed block in `~/.codex/AGENTS.md`. |
| opencode | `AGENTS.md` (+ `SKILL.md` as runbook) | `install.sh` installs under `~/.config/opencode/skills/feature-research`; opencode picks up `AGENTS.md` natively when invoked from this repo, or via the managed block written to `~/.config/opencode/AGENTS.md`. (Verify on your opencode version.) |

## Install

Clone the repository anywhere you want to keep the working copy, then run the installer:

```bash
git clone https://github.com/M4jupitercannon/Opensource-Framework-Researcher.git \
    ~/Opensource-Framework-Researcher
cd ~/Opensource-Framework-Researcher
./install.sh
```

By default, `install.sh` installs symlinks for Claude Code, Cursor, Codex, and opencode. Use targeted installs when needed:

```bash
./install.sh --target claude
./install.sh --target cursor
./install.sh --target codex
./install.sh --target opencode
```

Use `--copy` if you want independent copies instead of symlinks. Use `--force` only when replacing an existing install path; it moves the old path to a timestamped backup before installing.

```bash
./install.sh --copy --target cursor
./install.sh --force --target claude
```

Verify Claude Code / Cursor pick it up on the next session start. Codex reads the managed `feature-research` block from `~/.codex/AGENTS.md`, which points back to this repo's `AGENTS.md` and `SKILL.md`.

### Prerequisites

- Claude Code, Cursor, Codex, or another agentic coding environment
- `gh` (GitHub CLI), authenticated — `gh auth status` should show a valid login for documented fallback paths.
- For the optional Phase 4 ecosystem activity plot only: `python` ≥ 3.9 with `matplotlib` (`pip install matplotlib`). The Phase 1 → Phase 3 workflow has no Python dependency; only the chart renderer needs it.

## Use

In any supported agent session, name the triple naturally:

> "Use the feature-research skill for NVIDIA + vLLM + EP"
>
> "Run feature-research on AMD + SGLang + PD-disaggregation"

Claude Code and Cursor use `SKILL.md` directly. Codex starts from `AGENTS.md`, which points back to `SKILL.md` as the canonical runbook.

### Session intake

At session start (before Phase 0), the main agent runs a short four-question intake so every downstream phase operates on the same captured inputs (researchers / analyzers / monitors reference these by name and never re-parse the raw strings).

1. **Time window** → `search_window`. Accepts one of three forms:
   - **Preset** — e.g. `1y` (trailing 1 year), `6mo`, `2y`.
   - **Inclusive month range** — e.g. `2025-05..2026-04`.
   - **Inclusive day range** — e.g. `2025-05-14..2026-05-14`.
   Phase 0 normalizes the raw input into the canonical C2 `search_window` object (`raw_input`, `display`, `start_date`, `end_date`, `start_month`, `end_month`, plus pre-baked `gh_qualifier_*` / `mcp_args` / `sql_predicate_*` strings) and writes it to `out_dir/search_window.json`. Each topic JSON's `_meta.search_window` carries the 4-field subset.
2. **Chip vendor(s)** → `chip_list`. Accepts zero, one, or two vendor names: `chip=NVIDIA`, `chip=[AMD, NVIDIA]`, `chip=[Intel, AMD]`, etc. **Defaults to `[AMD, NVIDIA]` when omitted.** Per **contract clarification C4 (v1 limitation), the comparison report supports exactly two vendors**:
   - `len(chip_list) == 0` → defaults to `[AMD, NVIDIA]`, comparison report rendered (Phase 5 runs).
   - `len(chip_list) == 1` → single-vendor flow, no comparison report.
   - `len(chip_list) == 2` → comparison report rendered (Phase 5 runs).
   - `len(chip_list) > 2` → **errors out at session intake** with the canonical message: `comparison report supports exactly 2 vendors; you supplied N. Re-run with chip=[A,B] or accept default [AMD, NVIDIA].` (N>2 is tracked as a known v2 work item in `templates/COMPARISON_REPORT_template.md`.)
3. **Framework + feature** → `framework`, `feature` (unchanged from prior versions).
4. **Scope confirmation** — after Phase 0 derives each vendor's `in_scope` SM/CDNA/XPU code list, the main agent presents the derived lists back to the user and accepts one of: **accept** the derived scope, **narrow** to a subset of the derived codes, or **override** with an explicit `scope_override`. The per-vendor pipelines (Phase 1 → Phase 2 → Phase 3) only fan out after this confirmation.

### Multi-vendor / comparison report

When `len(chip_list) == 2`, the main agent additionally runs Phase 5 after Phase 4 finishes. Phase 5 is best-effort synthesis only — it does NOT re-verify refs (those are covered by each per-vendor pipeline's three-stage audit) but it does roll each vendor's `_meta.fallback_used` count into a single Verification Footer line.

- Renders `templates/COMPARISON_REPORT_template.md` to `out_dir/COMPARISON_REPORT.md`.
- **Phase 4 runs first** so the comparison report can embed the ecosystem plots from the top-level `out_dir/ecosystem_plots/` directory (per C8.1) via the `[render_if_present ecosystem_plots]` block. Per-vendor `out_dir/{vendor}/REPORT.md` files reference the same plots via the relative path `../ecosystem_plots/{metric}_by_vendor.png`.
- Uses `{{vendor_a}}` / `{{vendor_b}}` placeholders throughout — the template caps comparison at exactly two vendors per C4. **N>2 is a known v2 work item**: for now, run separate vendor-pairs end-to-end.
- Skipped entirely when `len(chip_list) == 1`.

### Data sources / MCP-first

The skill prefers the `signals-service` MCP server (source tag `mcp:signals`) for every GitHub PR/issue/RFC lookup, with `gh` CLI documented as a fallback (per contract clarifications C6 + C7).

- **MCP pre-flight at session start.** Immediately after Session intake, the main agent calls `db_health()` and `get_stats()` against `signals-service` and folds the result into two independent capability flags:
  - `MCP_DETAIL_USABLE` — controls the per-PR `search_signals` + `get_signal_detail` path used by Phase-1 researchers and Phase-2 monitors.
  - `MCP_SQL_USABLE` — controls the Phase 4 raw-rows `execute_sql` path used by the plot agent.
  Both flags are persisted to `out_dir/_signals_schema.json` along with the discovered canonical strings.
- **Probe verdict lives in `sources/signals_service_discovered.md`.** That file (produced by the Stage-1.5 MCP probe) is the single source of truth for the live server's resolved column names, `signal_id` format, and date-filter support. **Current verdict on the build host:** `MCP_DETAIL_USABLE: true` and `MCP_SQL_USABLE: true` — `signals-service` is the verified first-choice data path for indexed GitHub PR / issue lookups and Phase 4 SQL raw-row fetches. `gh` remains the documented fallback when MCP errors or returns no hit.
- **Server reference uses the registered name only.** Every committed doc names `signals-service` and nothing else — the actual MCP URL is configured at install/host time in your host's MCP config (Claude Code, Cursor, Codex, and opencode each have their own path; see the **Per-host MCP setup** table in `sources/source_playbook.md`). **URLs are never baked into committed docs** (per C7). `install.sh` MAY emit a warning if `signals-service` is not registered, but it does not write the URL. The only file in the repo that may contain a URL is `sources/signals_service_discovered.md`, and only as a recorded probe target.
- **Every fallback is recorded.** Whenever an agent falls back from `mcp:signals` to `gh` for a given ref, it appends a row `{ref, tool_attempted, tool_succeeded, reason}` to the relevant topic JSON's `_meta.fallback_used` array (per C5). `monitor_existence` (Stage 1) RED-fails any topic file missing either `_meta.search_window` or `_meta.fallback_used`. The synthesized `REPORT.md` rolls these up into a one-line Verification Footer summary (e.g. `Fallback usage: 3 of 47 refs fell back from mcp:signals to gh.`).

### Workflow

The skill walks through:

1. **Phase 0** — resolve scope per chip vendor in `chip_list` (in-scope SM/CDNA/XPU codes + out-of-scope drops). Writes `out_dir/search_window.json` (full C2 object) and `out_dir/_signals_schema.json` (session-wide), plus `out_dir/{vendor}/scope.json` for each vendor.
2. **Phase 1a** — for each vendor, run one researcher role per default topic, in parallel when supported (excluding `external_repo_dependencies`). Each verifies every PR / issue via `mcp:signals` first and via `gh` on fallback before writing its JSON. Topic JSONs land at `out_dir/{vendor}/topics/{topic}.json` and are stamped with `_meta.search_window` (4-field subset) and `_meta.fallback_used` (per C5).
3. **Phase 1b** — once that vendor's `completed_subfeatures.json`, `kernels_or_components.json`, and `open_issues.json` are on disk, run one serial `analyzer_external_repos` role that derives `out_dir/{vendor}/topics/external_repo_dependencies.json` from them (verifying every external-repo ref against its OWN repo).
4. **Phase 2** — three serial verification monitor roles per vendor in series: Stage 1 (`monitor_existence`) re-samples PR/issue/URL existence + verbatim quotes AND RED-fails any topic JSON missing `_meta.search_window` / `_meta.fallback_used`; Stage 2 (`monitor_scope`) audits chip-vendor scope; Stage 3 (`monitor_feature`) audits feature strictness. Each writes its own `verification_*.md` under `out_dir/{vendor}/`; later stages run only after the prior stage reaches GREEN/YELLOW.
5. **Phase 3** — per vendor, apply YELLOW / AMBER / RED must-fixes from all three stages and synthesize `out_dir/{vendor}/REPORT.md`.
6. **Phase 4 — Ecosystem activity plot (optional)** — main agent asks the user which metric(s) to chart (`merged_prs`, `opened_issues`, `closed_issues`, `all`, `skip`). For each chosen metric, one `plot_ecosystem_activity` role bulk-fetches monthly counts on `vllm-project/vllm` + `sgl-project/sglang` (configurable), classifies entries against the vendor blocks in `scope/chip_scope_map.md` (single source of truth — no separate keyword file), and writes one CSV + PNG + methods note under the top-level `out_dir/ecosystem_plots/` (per C8.1, NOT under any vendor folder — Phase 4 runs once per session, not per vendor). The CSV's `vendor_group` column matches the run's `chip_list` (per C8.2). Best-effort context outside the three-stage audit trail. If the user picks `skip`, do NOT create `out_dir/ecosystem_plots/`; continue to Phase 5 when `len(chip_list) == 2`, otherwise advance directly to Phase 6 (the Phase 5 gate is purely `len(chip_list) == 2`).
7. **Phase 5 — Comparison synthesis** — only when `len(chip_list) == 2`. Always runs after Phase 4 (per C1) so the comparison report can embed ecosystem plots via `[render_if_present ecosystem_plots]`. Renders `templates/COMPARISON_REPORT_template.md` to `out_dir/COMPARISON_REPORT.md`. Skipped when `len(chip_list) == 1`.
8. **Phase 6 — Hand-off** — print paths to all artifacts: per-vendor `out_dir/{vendor}/REPORT.md` + the three `verification_*.md` files + `scope.json` + topic JSONs, plus session-wide artifacts (`search_window.json`, `_signals_schema.json`, Phase 4 artifacts under `ecosystem_plots/`, and `COMPARISON_REPORT.md` when Phase 5 ran).

## Repo layout

```
install.sh                          # installs symlinks/copies for Claude Code, Cursor, and Codex
SKILL.md                            # entry + 6-phase orchestration contract (incl. C1 phase order, C4 2-vendor cap, C7 URL handling)
AGENTS.md                           # Codex/project-instruction shim that points to SKILL.md
topics/
  default_topics.md                 # 6 default topic definitions (prompt + entry schema each) — 5 Phase-1a researchers + 1 Phase-1b analyzer
  topic_json_schema.md              # required JSON shape every topic file must conform to — includes the C5 _meta.search_window and _meta.fallback_used fields
scope/
  chip_scope_map.md                 # NVIDIA / AMD / Intel / Google TPU scope rules
sources/
  source_playbook.md                # mcp:signals (PRIMARY) + gh (DOCUMENTED FALLBACK) + WebFetch / WebSearch / MLPerf / InferenceX recipes
  signals_service_discovered.md     # Stage-1.5 MCP probe output: capability flags, discovered canonical strings, Phase 4 SQL template (only file allowed to record the probe URL, per C7)
agents/
  researcher.md                     # per-topic researcher sub-agent prompt template
  analyzer_external_repos.md        # Phase-1b external-repo analyzer sub-agent prompt template
  monitor_existence.md              # Stage-1 verification sub-agent prompt — PR/issue/URL existence + verbatim quotes + _meta.search_window / _meta.fallback_used presence
  monitor_scope.md                  # Stage-2 verification sub-agent prompt — chip-vendor scope strictness
  monitor_feature.md                # Stage-3 verification sub-agent prompt — feature-strictness audit
  plot_ecosystem_activity.md        # Phase 4 ecosystem activity plot sub-agent prompt (optional)
templates/
  REPORT_template.md                # synthesized per-vendor report skeleton
  COMPARISON_REPORT_template.md     # side-by-side comparison report skeleton rendered by Phase 5 when len(chip_list) == 2 (per C4)
scripts/
  check_compat.py                   # lightweight packaging/wording validation (host coverage, MCP-first, phase-ordering, URL-handling, per-host MCP setup, slash-command/artifact agreement, plot flag)
  plot_ecosystem_activity.py        # Phase 4 CSV → PNG renderer (matplotlib) — unchanged CSV consumer contract per C8
```

## Extending

- **Add a framework** — edit the framework→repo map in `sources/source_playbook.md` (table near the top of the file).
- **Add a chip vendor** — add a vendor block to `scope/chip_scope_map.md` (in-scope, out-of-scope drops, `default_scope_statement`). The Phase 4 plot role automatically picks up the new vendor's `aliases` + `in_scope` codenames as classification keywords; no separate keyword file to edit.
- **Add a default topic** — append a topic block to `topics/default_topics.md` matching the existing format (name, `report_heading`, `prompt`, `entry_schema`).
- **Add a repo to the ecosystem activity plot** — pass `ecosystem_plot_repos=["org/repoA", "org/repoB", ...]`. The plot script's per-`(repo, vendor)` color/marker map covers the v1 default repos; new repos fall back through the matplotlib default cycle. Override the legend prefix with `--repo-label org/repo=Label` if needed.

## Design constraints baked in

- **Roles do not spawn nested workers** — orchestration stays flat in the main agent.
- **Verify before write** — every PR / issue / URL is `gh`-checked or web-fetched by the producing researcher before the JSON file is written. The monitor re-samples but does not substitute.
- **Verbatim source quotes** — perf-number entries store an exact quote from the cited source; the monitor diffs against the live page.
- **Scope audit trail** — items dropped for being out-of-scope are logged in `verification_scope.md` (Stage 2) and surfaced in the report's Verification Footer.

## Compatibility check

Run this before publishing changes:

```bash
python scripts/check_compat.py
```

Also run after `./install.sh` to verify symlinks and host detection.

## License

MIT — see [`LICENSE`](./LICENSE).
