# Opensource-Framework-Researcher

A Claude Code [skill](https://docs.claude.com/en/docs/claude-code/skills) that runs a multi-agent investigation of one **(chip vendor, framework, feature)** triple in the open-source AI inference / training ecosystem and emits dashboard-ready outputs.

Examples of triples this skill handles:

- `NVIDIA + vLLM + EP` (Expert Parallelism)
- `AMD + SGLang + PD-disaggregation`
- `NVIDIA + TensorRT-LLM + speculative-decoding`
- `Google + JAX + paged-KV` *(if your framework→repo map is extended)*

It generalizes the methodology of a hand-run vLLM-EP investigation: **5 parallel Phase-1a researcher sub-agents** fan out across the default topics, then **1 serial Phase-1b analyzer sub-agent** derives external-repo dependencies from three of those topic outputs, three serial verification monitors (existence, chip-vendor scope, feature strictness) independently re-check every PR / issue / URL via the GitHub CLI and `WebFetch`, and the main agent synthesizes a single highlighted Markdown report from per-topic JSON files.

## What you get per run

Under `~/research/{framework}_{feature}/{YYYY-MM-DD}/`:

| File | Purpose |
|---|---|
| `topics/*.json` | One file per research topic, **stable schema** — feed straight into a dashboard. |
| `scope.json` | Auto-derived chip-vendor scope (in/out SKUs) used for filtering. |
| `verification_existence.md` | Stage 1 audit (PR/issue/URL existence + verbatim quotes), with verdict `GREEN` / `YELLOW` / `RED` and must-fix punch list. |
| `verification_scope.md` | Stage 2 audit (chip-vendor scope strictness), with verdict and must-fix punch list. |
| `verification_feature.md` | Stage 3 audit (feature strictness), with verdict and must-fix punch list. |
| `REPORT.md` | Synthesized human-readable report — At-a-Glance dashboard table + one section per topic with a primary table optimized for dashboard ingestion. |

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

| Source | Use |
|---|---|
| `gh` (GitHub CLI) | Primary source for PRs / issues / RFCs in the framework repo. |
| `WebFetch` | Vendor docs, framework release notes, RFC pages. |
| `WebSearch` | Discovery of blogs / announcements. |
| MLPerf | Public chip-vs-chip benchmark cross-check. |
| [SemiAnalysis InferenceX](https://github.com/SemiAnalysisAI/InferenceX) | Third-party perf reference. |

## Install

Clone into your Claude Code skills directory:

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/M4jupitercannon/Opensource-Framework-Researcher.git \
    ~/.claude/skills/feature-research
```

Verify Claude Code picks it up — it should appear in your available-skills list as `feature-research` on next session start.

### Prerequisites

- Claude Code (the CLI)
- `gh` (GitHub CLI), authenticated — `gh auth status` should show a valid login.

## Use

In any Claude Code session, just name the triple naturally:

> "Use the feature-research skill for NVIDIA + vLLM + EP"
>
> "Run feature-research on AMD + SGLang + PD-disaggregation"

The skill walks through:

1. **Phase 0** — resolve scope from chip vendor (in-scope SM/CDNA/XPU codes + out-of-scope drops).
2. **Phase 1a** — spawn one researcher sub-agent per default topic, in parallel (excluding `external_repo_dependencies`). Each verifies every PR / issue with `gh` before writing its JSON.
3. **Phase 1b** — once `completed_subfeatures.json`, `kernels_or_components.json`, and `open_issues.json` are on disk, spawn one serial `analyzer_external_repos` sub-agent that derives `external_repo_dependencies.json` from them (verifying every external-repo ref against its OWN repo).
4. **Phase 2** — three serial verification monitor sub-agents in series: Stage 1 (`monitor_existence`) re-samples PR/issue/URL existence and verbatim quotes, Stage 2 (`monitor_scope`) audits chip-vendor scope, Stage 3 (`monitor_feature`) audits feature strictness. Each writes its own `verification_*.md`; later stages run only after the prior stage reaches GREEN/YELLOW.
5. **Phase 3** — apply YELLOW / AMBER / RED must-fixes from all three stages, synthesize `REPORT.md`.
6. **Phase 4** — print paths to all artifacts (`REPORT.md`, the three `verification_*.md` files, `scope.json`, and the per-topic JSONs under `topics/`).

## Repo layout

```
SKILL.md                     # entry + 4-phase orchestration contract
topics/
  default_topics.md          # 6 default topic definitions (prompt + entry schema each) — 5 Phase-1a researchers + 1 Phase-1b analyzer
  topic_json_schema.md       # required JSON shape every topic file must conform to
scope/
  chip_scope_map.md          # NVIDIA / AMD / Intel / Google TPU scope rules
sources/
  source_playbook.md         # gh / WebFetch / WebSearch / MLPerf / InferenceX recipes
agents/
  researcher.md              # per-topic researcher sub-agent prompt template
  analyzer_external_repos.md # Phase-1b external-repo analyzer sub-agent prompt template
  monitor_existence.md       # Stage-1 verification sub-agent prompt — PR/issue/URL existence + verbatim quotes
  monitor_scope.md           # Stage-2 verification sub-agent prompt — chip-vendor scope strictness
  monitor_feature.md         # Stage-3 verification sub-agent prompt — feature-strictness audit
templates/
  REPORT_template.md         # synthesized report skeleton
```

## Extending

- **Add a framework** — edit the framework→repo map in `sources/source_playbook.md` (table near the top of the file).
- **Add a chip vendor** — add a vendor block to `scope/chip_scope_map.md` (in-scope, out-of-scope drops, `default_scope_statement`).
- **Add a default topic** — append a topic block to `topics/default_topics.md` matching the existing format (name, `report_heading`, `prompt`, `entry_schema`).

## Design constraints baked in

- **Sub-agents do not spawn further sub-agents** — orchestration stays flat in the main agent.
- **Verify before write** — every PR / issue / URL is `gh`-checked or `WebFetch`-checked by the producing researcher before the JSON file is written. The monitor re-samples but does not substitute.
- **Verbatim source quotes** — perf-number entries store an exact quote from the cited source; the monitor diffs against the live page.
- **Scope audit trail** — items dropped for being out-of-scope are logged in `verification_scope.md` (Stage 2) and surfaced in the report's Verification Footer.

## License

MIT — see [`LICENSE`](./LICENSE).
