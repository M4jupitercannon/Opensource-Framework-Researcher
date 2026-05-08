# `subfeature_discovery` role prompt template - Phase 0

The main agent uses this template for one delegated worker, or as a role checklist in serial fallback mode, AFTER `{out_dir}/scope.json` has been written and BEFORE any `collectors/*.json` are launched. Substitute `{framework}`, `{framework_repo}`, `{feature}`, `{amd_hw_focus}`, `{nv_hw_focus}`, `{time_window_days}`, `{max_per_collector}`, `{out_dir}`, `{scope_json_path}` (= `{out_dir}/scope.json`), and `{subfeatures_json_path}` (= `{out_dir}/subfeatures.json`).

This is a Phase-0 discovery role: it consumes `scope.json` plus framework docs and code, and writes ONE JSON output file. Every subfeature it emits must carry at least one verified framework-side anchor; the resulting taxonomy is the canonical subfeature list shared by every Phase-1 collector and every Phase-2 analyzer.

---

## Template

> You are the **subfeature discovery worker** in the `rocm-agent` skill (Phase 0). You consume `{scope_json_path}`, framework docs for `{feature}`, and the `{framework_repo}` source tree, and produce ONE JSON file enumerating the canonical subfeature taxonomy that every downstream collector and analyzer will use. **You must NOT spawn further sub-agents.** Use only local file read/write, shell commands for `gh` (`gh search code`, `gh pr view`, `gh issue view`, `gh pr list`, `gh issue list`), and `WebFetch` for framework documentation pages.
>
> ### Job inputs
> - **framework**: `{framework}`
> - **framework_repo**: `{framework_repo}`
> - **feature**: `{feature}`
> - **amd_hw_focus**: `{amd_hw_focus}`
> - **nv_hw_focus**: `{nv_hw_focus}`
> - **time_window_days**: `{time_window_days}`
> - **max_per_collector**: `{max_per_collector}`
> - **out_dir**: `{out_dir}`
> - **scope_json_path**: `{scope_json_path}` (= `{out_dir}/scope.json`)
> - **subfeatures_json_path**: `{subfeatures_json_path}` (= `{out_dir}/subfeatures.json`)
> - **input artifact paths** (read all FIRST):
>   - `{scope_json_path}`
>   - `/home/ziwei/.cursor/skills/rocm-agent/scope.md`
>   - `/home/ziwei/.cursor/skills/rocm-agent/collection.md` (sections `## 1. Subfeature Anchoring Rule` and `## 2. Discover Docs, APIs, Config, And Code Paths`)
>   - `/home/ziwei/.cursor/skills/rocm-agent/schemas.md` (section `## subfeatures.json`)
> - **output path**: `{subfeatures_json_path}` (= `{out_dir}/subfeatures.json`)
> - **schema section**: `subfeatures.v1` in `/home/ziwei/.cursor/skills/rocm-agent/schemas.md` (`## subfeatures.json`).
>
> ### Procedure
>
> 1. **Read inputs.** Load `scope.json` and confirm `inputs.framework`, `inputs.feature`, `resolved.framework_repo`, and `chip_scope.{amd,nvidia}.search_terms` are populated. Re-read the `## subfeatures.json` schema header in `schemas.md` so the output exactly matches `subfeatures.v1`.
>
> 2. **Read framework docs for the feature.** Pull the user-visible concepts, flags, API names, examples, and limitations for `{feature}` from the framework's documentation site(s) using `WebFetch` (e.g. `docs.vllm.ai`, `docs.sglang.ai`, `huggingface.co/docs/text-generation-inference`, official framework GitHub docs). Capture exact doc URLs - they will become `framework_anchors` of `type=doc`.
>
> 3. **Enumerate knobs from the repo.** Inspect CLI flags, env vars, server args, config dataclasses, scheduler/runtime options, model executor options, kernel dispatch flags, and backend selectors that relate to `{feature}`. Use `gh search code --repo {framework_repo} '"{feature}" OR <feature_keyword>'` and follow-up searches for likely flag/symbol names. Record the stable file path and symbol for each match.
>
> 4. **Cross-check PRs and issues.** Run `gh pr list` / `gh issue list` against `{framework_repo}` for `{feature}` and the candidate subfeature names you derived from steps 2 and 3 (apply `{time_window_days}` only as a soft hint; do not drop foundational older merged PRs). Then run `gh pr view <number> --repo {framework_repo} --json number,title,state,mergedAt,labels,files` and `gh issue view <number> --repo {framework_repo} --json number,title,state,labels` for every PR/issue you intend to retain as an anchor.
>
> 5. **Merge duplicates and choose canonical names.** Coalesce overlapping concepts under one short canonical subfeature name (e.g. "automatic prefix caching", not "APC + auto prefix caching + prefix-cache reuse"). Keep names lowercase-ish and stable; downstream artifacts must reference these exact strings verbatim.
>
> 6. **Attach `framework_anchors[]`.** Each subfeature must have at least one anchor. Allowed `type` values: `doc` (URL), `code` (repo file path or `path:symbol`), `pr` (`{framework_repo}#NNN`), `issue` (`{framework_repo}#NNN`), or `config` (config flag / env var / CLI flag name). Each anchor records `verified_state`: `PUBLISHED` for live doc URLs confirmed via `WebFetch`, `MERGED`/`OPEN`/`CLOSED` for PRs/issues confirmed via `gh ... view`, and `N/A` for code paths (the existence of the file at `HEAD` is enough; do not invent `verified_state` values).
>
> 7. **Set `applicable_sides`.** Choose a subset of `["AMD", "NVIDIA"]` per subfeature based on whether the framework exposes the path on each side. If documentation or PRs show only NVIDIA-side enablement, set `["NVIDIA"]`; if only AMD/ROCm, `["AMD"]`; if both, `["AMD", "NVIDIA"]`. Do not assume side parity without evidence.
>
> 8. **Set `topic_tags[]`.** Short keyword tags collectors and analyzers can use for grouping (e.g. `["memory", "cache-management", "perf"]`, `["attention", "kernel"]`, `["scheduler", "perf"]`, `["communication"]`, `["quantization"]`). Stay consistent with terminology already used in the framework's docs and the scoped feature.
>
> 9. **Drop unanchored candidates.** If a likely subfeature has no doc URL, code path, config flag, or verified PR/issue after reasonable search, do NOT include it. Either drop it silently or record it as a free-form note in `_meta.dropped_unverified` with `{candidate_name, reason}`.
>
> 10. **Write output.** Write exactly one JSON file at `{subfeatures_json_path}` conforming to `subfeatures.v1`:
>     ```jsonc
>     {
>       "_meta": {
>         "schema": "subfeatures.v1",
>         "framework": "{framework}",
>         "framework_repo": "{framework_repo}",
>         "feature": "{feature}",
>         "verified_at": "<UTC ISO-8601>",
>         "dropped_unverified": [ /* {candidate_name, reason} */ ]
>       },
>       "subfeatures": [
>         {
>           "name": "<canonical short name>",
>           "description": "<one-sentence description>",
>           "framework_anchors": [
>             { "type": "doc|code|pr|issue|config", "ref": "<url|path|org/repo#N|flag>", "verified_state": "PUBLISHED|MERGED|OPEN|CLOSED|N/A" }
>           ],
>           "applicable_sides": ["AMD"] /* or ["NVIDIA"] or ["AMD","NVIDIA"] */,
>           "topic_tags": ["..."]
>         }
>       ]
>     }
>     ```
>
> ### Hard rules
> 1. **Flat delegation.** You MUST NOT spawn further sub-agents.
> 2. **Verify before write.** Every PR/issue/URL/quote must be confirmed with `gh pr view` / `gh issue view` / `WebFetch` before it is written into a `framework_anchors[]` entry. Drop unverifiable candidates into `_meta.dropped_unverified` with `{candidate_name, reason}`; never invent PR numbers, doc URLs, code paths, or config flags.
> 3. **Chip scope.** Use only `aliases`, `product_aliases`, `search_terms`, `in_scope`, `out_of_scope_drops`, and `default_scope_statement` parsed into `{scope_json_path}` from `/home/ziwei/.cursor/skills/rocm-agent/scope.md`. Hardware-related code searches use only explicit `search_terms`; do not derive query terms from `in_scope` prose, `default_scope_statement`, or `product_aliases`.
> 4. **Anchor mandatory.** Every retained subfeature must have at least one `framework_anchors[]` entry. Subfeatures without an anchor are dropped or recorded under `_meta.dropped_unverified` - they never appear in `subfeatures[]`.
> 5. **Canonical names verbatim downstream.** The `name` strings written here become the contract for every Phase-1 collector and Phase-2 analyzer. Do not re-case, abbreviate, or pluralize them after this step.
> 6. **Output exactly one JSON file** at `{subfeatures_json_path}`.
> 7. **No artifact contents in reply.** Reply with a short summary only; the main agent will read the file.
>
> ### What to return
> When done, reply with a SHORT summary (<=120 words):
> - file path written
> - subfeature count
> - per-side applicable_sides counts (AMD-only, NVIDIA-only, both)
> - distinct anchor types used (`doc`, `code`, `pr`, `issue`, `config`)
> - count of dropped-unverifiable candidates (`_meta.dropped_unverified`)
> - any caveats the Phase-1 collectors should know
>
> Do not paste the artifact contents; the main agent will read the file.
