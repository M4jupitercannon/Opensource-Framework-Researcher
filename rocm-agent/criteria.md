# ROCm-agent Criteria Reference

> Note: This rubric is the source of truth for `/home/ziwei/.cursor/skills/rocm-agent/agents/analyzer_criteria_scores.md` (which writes `analysis/criteria_scores.json`) and for the downstream `tables.score_rows` rendered by `/home/ziwei/.cursor/skills/rocm-agent/agents/analyzer_dashboard_data.md`. Keep scoring policy here; do not duplicate it inside the role files.

Use this reference when scoring AMD/ROCm versus NVIDIA/CUDA evidence for a specific inference framework feature. Every scored row must use exactly one of two dimensions:

- `feature_relevance`
- `performance_relevance`

Do not create operational, readiness, stability, ecosystem, or maintenance scores. Stability is not a third score. Include stability evidence only when it affects feature correctness, feature availability, or performance paths for the requested feature.

## Scoring Scale

Score each side from 0 to 5 per criterion:

- 0: Not present or actively broken.
- 1: Experimental, blocked by major bugs, or only available on out-of-scope hardware.
- 2: Usable, but limited by model, dtype, shape, hardware, or a large performance gap.
- 3: Usable on representative configurations, with known but bounded gaps.
- 4: At parity on most representative configurations.
- 5: State of the art for the requested feature.

The reported gap is `nvidia_score - amd_score`. Positive means NVIDIA leads. Negative means AMD leads. Sort dashboards by absolute gap when identifying the largest deltas.

## Feature Relevance

Use `feature_relevance` for criteria that determine whether the requested feature or one of its subfeatures is correct, exposed, usable, and available to users.

Feature criteria should cover:

- Feature completeness for the requested feature and its discovered subfeatures.
- API, CLI, config flag, environment variable, and server argument parity.
- Default enablement versus experimental or opt-in flags when this changes usable coverage or benchmark comparability.
- Correctness of the feature on the scoped side, including wrong outputs, unsupported modes, disabled paths, or runtime failures.
- Model coverage for representative architectures affected by the feature.
- Shape, batch size, sequence length, context length, and request pattern coverage.
- Dtype and quantization mode coverage when the requested feature depends on them.
- Hardware generation coverage for the requested AMD and NVIDIA focus hardware.
- Framework integration state, including merged support, open blockers, docs, and release exposure.
- Feature-critical dependency maturity, but only for libraries that directly gate the feature.

Examples of feature-relevance gaps:

- The feature exists on NVIDIA but is missing on AMD.
- AMD supports the feature only behind an experimental flag while NVIDIA enables it by default.
- AMD supports only a subset of models, dtypes, sequence lengths, or quantization modes required by the feature.
- A crash, hang, wrong result, or build/runtime blocker disables the scoped feature on AMD.
- Documentation, config, or API exposure makes one side usable and the other side effectively unavailable.

Do not score generic repo activity, contributor count, release cadence, CI status, or packaging convenience as `feature_relevance` unless it directly changes feature correctness or availability.

## Performance Relevance

Use `performance_relevance` for criteria that determine throughput, latency, memory efficiency, scaling, or benchmark behavior for the requested feature.

Performance criteria should cover:

- Kernel availability and maturity for feature-critical attention, GEMM, MoE, quantization, communication, cache-management, and custom kernels.
- Missing kernels, immature kernels, fallback paths, missing fusion, poor lowering, excessive host sync, or unnecessary data movement.
- Compiler and codegen maturity where it affects feature execution or performance, including Triton/HIP lowering, graph capture, fusion, scheduling, and generated kernel quality.
- Communication performance when the feature depends on collectives, all-to-all, expert parallelism, KV transfer, remote cache movement, or overlap.
- Memory-system behavior when the feature depends on paging, KV cache reuse, allocators, fragmentation, prefill/decode separation, cache eviction, or cache transfer.
- Quantization, dtype, and layout paths when they change kernel choice or performance.
- End-to-end benchmark results and microbenchmark results for comparable model/config/hardware evidence.
- Benchmark harness maturity only when it affects measured performance for the requested feature.
- Power, clock, or hardware generation differences when they materially change interpretation of performance evidence.

Examples of performance-relevance gaps:

- NVIDIA has a fused feature-critical kernel while AMD falls back to eager or unfused code.
- AMD executes the same feature but loses throughput because graph capture is disabled.
- AMD uses a slow compiler lowering path, extra host synchronization, or excessive memory movement.
- The feature works on both sides, but AMD lacks comparable benchmark coverage for the representative model and shape.
- A stability issue forces a slow path, disables a fast kernel, serializes execution, or prevents overlap.

Do not score generic build speed, test flakiness, deployment ergonomics, issue response time, or unrelated runtime problems as `performance_relevance` unless they directly affect measured or expected performance for the requested feature.

## Stability Handling

Stability is not a third score and must not appear as a separate scored dimension.

Route stability evidence as follows:

- Feed `feature_relevance` when a crash, hang, wrong result, unsupported mode, build failure, or runtime failure breaks correctness or availability of the scoped feature.
- Feed `performance_relevance` when a stability problem forces slow paths, disables fast kernels, disables graph capture, prevents overlap, serializes execution, changes scheduling, or otherwise changes performance behavior.
- Drop stability evidence when it is generic operational noise, unrelated CI flake, unrelated crash, unrelated build issue, or a problem outside the requested feature scope.

Each stability-derived row must state the affected subfeature, the side affected, the score dimension it feeds, and the rationale linking it to feature correctness, feature availability, or performance behavior.

## Severity Rating

Severity is a per-side impact tag on every `stability_gaps.json` and `performance_kernel_gaps.json` entry. It is independent of `confidence` (how sure we are of the evidence) and `evidence_tier` (how strong the source is). Severity describes how badly the symptom or kernel/path gap affects the requested feature on that one side. Severity is not a score; it does not replace `feature_relevance` or `performance_relevance`. Both AMD and NVIDIA severities must be assigned on every retained row, even when one side has `none` / `0`.

### Stability severity scale (enum)

Use one of `none`, `low`, `medium`, `high`, `critical` for `amd_severity` and `nvidia_severity` on every `stability_gaps.json` entry.

- `critical`: data corruption, silent wrong outputs, complete unavailability of the scoped subfeature on representative configs, or a hang/crash that makes the affected path unusable for representative serving runs.
- `high`: blocks a major code path, model, or dtype on representative hardware; a workaround exists but the primary path is unusable.
- `medium`: bounded but visible impact on representative configs; partial coverage loss, a known fallback that still functions, or a flaky path that succeeds with retry.
- `low`: edge-case impact, narrow shape/dtype/hardware corner, easily worked around, or rare conditions outside representative configs.
- `none`: no matching symptom on this side.

Calibration:

- The side previously identified as `side_affected` must have severity `>= medium`. If the highest severity on either side is `low` or `none`, drop the row into `_meta.dropped_below_threshold` with reason `severity_too_low_to_feed_scored_dimension`; the row is operational noise, not a scored gap.
- The non-affected side defaults to `none` unless retained collector evidence shows the same symptom under different conditions; in that case, score that side at the lower severity that the verified evidence supports (typically `low` or `medium`).

### Performance severity scale (integer 0..5)

Use an integer in `[0, 5]` for `amd_severity` and `nvidia_severity` on every `performance_kernel_gaps.json` entry.

- `0`: no impact - this side has the fast path or is not affected by the gap.
- `1`: minor, edge-case slowdown only on narrow configs (rare dtype, rare shape, out-of-scope HW corner).
- `2`: measurable slowdown on narrow configs; representative configs are largely unaffected.
- `3`: noticeable slowdown on representative configs, still bounded; a working performant path exists with caveats.
- `4`: major slowdown or forced fallback on representative configs; the optimized kernel/fusion/lowering is missing or disabled.
- `5`: no working performant path - serialized execution, broken graph capture, or kernel completely unavailable for the scoped subfeature on representative hardware.

Calibration:

- For `missing_kernel` or `fallback_path` AMD-only gaps, AMD severity is typically `4-5` and NVIDIA severity is typically `0-1`.
- For `excessive_host_sync`, `poor_lowering`, and `missing_fusion` rows, calibrate by how representative the affected config is: representative-config impact warrants `>= 3` on the affected side.
- For `immature_kernel` rows backed by `quantitative_benchmark`, calibrate by the measured delta: `< 1.2x` slower -> `2`, `1.2-2x` -> `3`, `2-5x` -> `4`, `> 5x` or no working path -> `5`.
- The unaffected side defaults to `0` when the path comparison shows no symmetric gap; raise it only when retained evidence shows the same kind of gap on that side too.

### Severity is required and verifiable

- Every retained `stability_gaps.json` entry must include both `amd_severity` and `nvidia_severity` from the enum above.
- Every retained `performance_kernel_gaps.json` entry must include both `amd_severity` and `nvidia_severity` as integers in `[0, 5]`.
- Severity values must be defensible from the same structured `evidence_refs` source pointers that justify the row; do not invent severities beyond what the verified evidence supports. Lower severity when evidence is asymmetric. Anecdotal evidence can inform context but must not be the sole retained source for a performance-kernel gap or a high-confidence scored row.
- Severity is independent of the dashboard `gap = nvidia_score - amd_score`; do not derive severity from scores or vice versa.

## Performance Evidence Comparability

Use `evidence_tier` for source strength (`primary`, `secondary`, `anecdotal`). Use `comparability_note` or a structured `comparability` block for methodology completeness. Do not use `primary`, `secondary`, or `anecdotal` as comparability labels.

### Quantitative Benchmark Checklist

Apply this checklist to `quantitative_benchmark` claims: any performance row that relies on a numeric benchmark, kernel timing, throughput, latency, memory, or scaling delta. If comparability is incomplete, keep the number only with lower confidence and an explicit note; drop the number when missing methodology makes the comparison misleading.

- Same requested framework and feature.
- Same subfeature or a clearly mapped equivalent subfeature.
- Same model family and size, or a documented reason the models differ.
- Same dtype, quantization mode, tensor layout, and precision policy where relevant.
- Same batch size, concurrency, request distribution, and scheduler settings where relevant.
- Same prompt length, generation length, sequence length, and context length where relevant.
- Same feature flags, default settings, cache settings, graph capture state, and kernel backend choices.
- Same metric definition, such as tokens per second, time to first token, inter-token latency, latency percentile, memory usage, or scaling efficiency.
- Same warmup, measurement window, repetition count, and reporting method when available.
- Comparable hardware generation and memory capacity, or an explicit hardware asymmetry note.
- Power, clock, thermal, container, driver, ROCm, CUDA, framework, and dependency versions when available.
- Clear distinction between microbenchmark and end-to-end benchmark evidence.
- Clear note when different code paths are compared, such as fused NVIDIA kernels versus eager AMD fallback paths.

### Qualitative Performance Path Checklist

Apply this smaller checklist to `performance_path` claims: qualitative findings such as `missing_kernel`, `fallback_path`, `missing_fusion`, `poor_lowering`, or `excessive_host_sync` when no numeric delta is retained.

- Same requested framework and feature.
- Same subfeature or a clearly mapped equivalent subfeature.
- Side-specific code paths, kernels, dispatch branches, or backend repos are named.
- Feature flags, runtime dispatch conditions, graph-capture state, or fallback triggers are documented when known.
- Hardware generation is comparable or an explicit hardware asymmetry note is present.
- Dependency or backend versions are documented when known.
- The row states whether the paths are equivalent, intentionally different, or not comparable.

Evidence tiers:

- `primary`: Upstream PR evidence, reproducible benchmark harnesses, or directly inspectable benchmark artifacts.
- `secondary`: Official vendor or framework blogs, docs, release notes, or benchmark posts with methodology.
- `anecdotal`: Issue comments, discussion posts, third-party posts, or claims without enough reproduction detail. Anecdotal evidence may appear in collector artifacts and report caveats, but it must not be the sole basis for retained `performance_kernel_gaps.json entries[]`, headline quantitative deltas, or high-confidence `criteria_scores.json` rows.

## Ownership Confidence Rules

Assign ownership for each actionable gap to the framework repo, a backend repo, or a feature-critical dependency. Use side-specific owner fields in `criteria_scores.json` when AMD and NVIDIA have different owners: `primary_amd_owner`, `primary_nvidia_owner`, `amd_co_owners`, `nvidia_co_owners`, `amd_integration_surface`, and `nvidia_integration_surface`. Use `confidence` to describe the ownership and scoring confidence.

Use `high` confidence when:

- A verified PR, issue, doc, code path, or release note directly names the owning repo or component.
- The failing or missing path is tied to a concrete file, kernel, library, dispatch path, or dependency bump.
- The evidence links the subfeature to the owner on the affected side.

Use `medium` confidence when:

- Multiple sources point to the same owner, but the exact code path or fix location is not fully verified.
- The framework integrates through a known dependency, but the missing behavior may require both framework and backend changes.
- The benchmark or issue identifies the symptom and stack, but not the exact kernel or component.

Use `low` confidence when:

- Ownership is inferred from ecosystem role rather than direct evidence.
- Evidence is anecdotal, incomplete, or based on asymmetric AMD/NVIDIA data.
- Several repos could plausibly own the fix and no source identifies a primary owner.

Ownership rules:

- Prefer the narrowest repo that can plausibly fix the gap.
- Use the framework repo as owner for API exposure, feature flags, scheduler integration, docs, benchmark harness wiring, or dispatch decisions.
- Use backend repos for kernels, compiler lowering, communication libraries, memory systems, attention libraries, quantization libraries, and feature-critical dependencies.
- Use `co_owners` when both framework integration and backend implementation are required.
- Lower confidence when comparability is incomplete or evidence is not primary.

## Exclusions

Exclude non-performance operational criteria unless they directly affect the requested feature.

Do not score:

- Generic CI health.
- Generic build, packaging, or installation convenience.
- Release cadence, star count, issue count, or contributor count.
- Broad ecosystem maturity unrelated to the scoped feature.
- Documentation quality unrelated to using or benchmarking the scoped feature.
- Unrelated crashes, hangs, flakes, or runtime errors.
- General hardware availability, pricing, procurement, or cloud instance availability.
- Security, governance, licensing, or support process topics.
- Repo maintenance practices that do not change feature behavior or performance.

Include operational evidence only when it directly changes:

- Feature correctness.
- Feature availability.
- Feature enablement.
- Benchmark comparability.
- Kernel or compiler path selection.
- Runtime performance behavior.
- Memory, communication, or scheduling behavior for the requested feature.

## Criteria Row Requirements

Every row written to `criteria_scores.json` must include:

- A criterion name tied to the requested feature or one of its subfeatures.
- `dimension` set to either `feature_relevance` or `performance_relevance`.
- `subfeatures` as an array of one or more canonical names from `subfeatures.json`. Group multiple subfeatures only when the same criterion, evidence, and score apply to every listed subfeature.
- AMD and NVIDIA scores from 0 to 5.
- A short rationale that explains the score delta.
- Structured evidence references that were verified by the monitors. Each ref points to a source artifact JSON Pointer plus stable `evidence_id` or `row_id`.
- `evidence_tier` set to `primary`, `secondary`, or `anecdotal`.
- `comparability_note` for methodology completeness; quantitative performance rows may also include a structured `comparability` block.
- Side-specific ownership fields when the row implies a fix or follow-up. Populate AMD fields for AMD follow-up owners, NVIDIA fields for NVIDIA follow-up owners, and both sides when the row compares distinct owner surfaces.

When rendering `dashboard/dashboard_data.json`, explode each `criteria_scores.json` row's `subfeatures[]` into one `tables.score_rows` row per `(criterion, subfeature, dimension)` tuple. Carry each criteria row rationale, `evidence_tier`, and `comparability_note` into every exploded row. Fill `tables.score_rows.primary_amd_owner`, `primary_nvidia_owner`, `amd_co_owners`, `nvidia_co_owners`, `amd_integration_surface`, and `nvidia_integration_surface` from `criteria_scores.json` first; if a row lacks side-specific owners, enrich the missing fields from `analysis/backend_repo_map.json` by matching `(subfeature, side)`. Leave an owner field empty only when no verified owner exists.

Never write a scored row whose dimension is stability, operations, readiness, ecosystem, or maintenance.
