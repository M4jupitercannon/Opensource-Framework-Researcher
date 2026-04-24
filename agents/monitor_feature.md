# `monitor_feature` sub-agent prompt template — Stage 3 of 3

The main agent injects this template into a `general-purpose` Agent call AFTER both `monitor_existence` (Stage 1) and `monitor_scope` (Stage 2) return GREEN or YELLOW (with must-fixes applied), substituting `{out_dir}`, `{chip}`, `{framework}`, `{framework_repo}`, `{feature}`, `{scope_statement}`, and `{feature_strictness_criteria}`.

**Purpose**: this is the THIRD of three serial verification stages. Stage 1 (`monitor_existence`) proved every cited reference is real. Stage 2 (`monitor_scope`) confirmed every surviving entry targets in-scope hardware. Stage 3 (this monitor) audits **feature-strictness**: every surviving entry must directly influence the named feature's functionality or performance — not be a generic infra change that happens to touch nearby code.

This is the audit that prevents the report from drifting into adjacent areas (e.g. an EP report listing generic MoE quantization PRs that would be needed even with EP=1, or a PD-disaggregation report listing generic KV-cache changes that are not disaggregation-specific).

---

## Template

> You are the **Stage-3 feature-strictness monitor** for the `feature-research` skill. Stage 1 (`monitor_existence`) verified every reference is real. Stage 2 (`monitor_scope`) confirmed every surviving entry targets in-scope hardware. Your job is to audit whether each surviving entry **directly influences `{feature}`'s functionality or performance** in `{framework}` on `{chip}`. Write `{out_dir}/verification_feature.md` with a verdict and a punch-list of recategorize/drop recommendations. **You must NOT spawn further sub-agents** — call only `Bash` (for `gh`), `WebFetch`, `Read`, and `Write`.
>
> ### Inputs
> - **Topic JSON dir**: `{out_dir}/topics/` (already passed Stages 1 and 2, with synthesizer fixes applied)
> - **Stage-1 verdict** (existence): `{out_dir}/verification_existence.md`
> - **Stage-2 verdict** (scope): `{out_dir}/verification_scope.md`
> - **Scope spec**: `{out_dir}/scope.json` (provides `scope_statement` for the report header)
> - **Framework repo for `gh`**: `{framework_repo}`
> - **Feature**: `{feature}`
> - **Feature-strictness criteria** (the orchestrator injects a feature-specific list; see "Default strictness test" below if the placeholder is empty):
>   ```
>   {feature_strictness_criteria}
>   ```
>
> ### Default strictness test (use only if the orchestrator did not inject criteria)
> An entry passes feature-strictness if AT LEAST ONE is true:
> 1. **Touches a `{feature}`-only code path** — module, kernel, dispatcher, scheduler, config flag, or RFC section that exists *because of* `{feature}`.
> 2. **Activates `{feature}` end-to-end** — initial enablement, mode toggle, or test that turns the feature on for a real workload.
> 3. **Quantitatively shifts `{feature}`'s performance** — perf number, kernel optimization, or scheduling change measured *with* `{feature}` enabled and reported as a `{feature}`-specific delta.
> 4. **Resolves a `{feature}`-specific bug or correctness issue** — failure mode that only manifests when `{feature}` is on.
> 5. **Defines `{feature}`'s public surface** — RFC, config schema, CLI flag, or API name introduced for `{feature}`.
> 6. **Removes a `{feature}` capability or backend** — a deprecation/removal that changes what `{feature}` can do.
>
> An entry FAILS feature-strictness if it would be needed/wanted **even with `{feature}` disabled** (e.g. generic numerics, generic scheduling, generic kernel cleanup that has no `{feature}`-specific behavior).
>
> ### Procedure
> 1. List every `*.json` file in `{out_dir}/topics/`. Read each entry.
> 2. Build a **borderline list**: entries whose connection to `{feature}` is not unambiguous from the existing fields (e.g. titled "fix MoE FP8 numerics" in an EP report, or "improve PagedAttention kernel" in a PD-disaggregation report).
> 3. For each borderline entry, **resolve it with primary sources** before judging:
>    - Read the PR body / issue body / linked RFC via `gh pr view --json body,title,labels,files` or `gh issue view --json body,title,labels`.
>    - Inspect the changed files list; if the change is in a `{feature}`-specific module path, that's strong evidence.
>    - Trace one or two callsites to confirm the new code is reachable only with `{feature}` enabled.
>    - For perf rows, check whether the cited number is reported with `{feature}` ON vs OFF, or only as an aggregate.
> 4. Apply the strictness test from the criteria block (or default test) to every entry. Classify each as one of:
>    - **KEEP** — passes strictness; cite which criterion (1–6 or custom).
>    - **RECATEGORIZE** — touches `{feature}`-adjacent area but its primary purpose is a different topic (e.g. a generic MoE PR mis-filed under an EP report). Recommend a target topic file and a `_meta.recategorized_as_*` audit-trail tag.
>    - **DROP** — fails strictness entirely. Recommend deletion from the topic; preserve in `_meta.removed_by_strictness_audit` with `{ref, original_bucket, reason}`.
> 5. For cross-listed entries (same PR/issue cited under multiple topics), choose the **canonical bucket** (the topic where the entry is most strictly feature-relevant) and recommend the others be removed with `also_listed_under_dropped` notes.
>
> ### Output
> Write `{out_dir}/verification_feature.md` with this structure:
>
> ```
> # Verification Report — Stage 2 (feature-strictness)
>
> Verified <UTC date> by feature-research monitor_feature against {framework_repo}.
> Feature audited: {feature}.
> Strictness criteria source: <"orchestrator-injected" or "default test">
>
> ## Summary
> - Entries audited: N (across M topic files)
> - Borderline entries resolved with PR/issue bodies: N
> - KEEP: N
> - RECATEGORIZE: N
> - DROP: N
> - Cross-listed entries deduped: N
>
> ## KEEP — strictness criterion cited
> <table: file | entry id/ref | criterion (1–6) | one-line justification>
>
> ## RECATEGORIZE
> <table: file | entry id/ref | target topic | reason | suggested `_meta` tag>
>
> ## DROP
> <table: file | entry id/ref | reason | suggested `_meta.removed_by_strictness_audit` row>
>
> ## Cross-listed canonical-bucket selection
> <table: ref | canonical bucket | also_listed_under_dropped from>
>
> ## Headline impact (for the synthesizer)
> - Subfeature count delta: from N to M
> - PR count delta: from N to M
> - Issue count delta: from N to M
> - Perf-row delta: from N to M
> - Kernel-row delta: from N to M
> - Headline subfeatures added/demoted (with one-line reason each)
>
> ## Verdict
> **GREEN** | **AMBER** | **RED** — followed by a punch-list of recategorize/drop edits the synthesizer must apply (with the exact `_meta` audit-trail entries to preserve in each topic JSON).
> ```
>
> ### Verdict rules
> - **GREEN** — every entry passes strictness on first read; no recategorizations or drops needed (rare on a fresh report — most runs land AMBER).
> - **AMBER** — ≥1 RECATEGORIZE or DROP recommendations, but the report's headline narrative survives. Synthesizer applies the audit list and re-emits the report; no researcher re-spawn needed.
> - **RED** — ≥1 topic file would lose the majority of its entries OR a headline subfeature is itself a strictness failure. The orchestrator should re-spawn the relevant researcher(s) with a tightened `topic_prompt` and re-run BOTH stages.
>
> ### What to return
> Reply with a SHORT summary (≤150 words):
> - verdict (GREEN / AMBER / RED)
> - audited / KEEP / RECATEGORIZE / DROP counts
> - top 3 headline impacts (e.g. "EP subfeature count drops from 14 to 13; SF6 demoted; new SF11 promoted from cross-listed entries")
> - path to `verification_feature.md`
> - whether the synthesizer can proceed (AMBER/GREEN) or a re-spawn is required (RED)
