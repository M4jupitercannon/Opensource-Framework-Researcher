# Source playbook

Each researcher sub-agent receives this file and chooses sources per topic. Every fact in a topic JSON must be traceable to one of the source IDs below; the researcher records which sources it used in `_meta.sources_used` (e.g. `["gh", "WebFetch:docs.vllm.ai", "inferencex"]`).

---

## 1. `gh` — GitHub CLI (PRIMARY for completed_subfeatures, open_issues, roadmap)

**When**: any claim about a PR, issue, RFC, or release in the framework's repo.

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

## 2. `WebFetch` — vendor docs, RFC pages, release notes

**When**: official documentation, blog posts (when the URL is known), framework release notes, RFC discussion pages.

**Useful hosts**:
- NVIDIA: `docs.nvidia.com`, `developer.nvidia.com/blog`
- AMD: `rocm.docs.amd.com`, `community.amd.com/t5/instinct-accelerators`
- Intel: `intel.com/content/www/us/en/developer/tools/...`, `habana.ai/blog`
- Google: `cloud.google.com/tpu/docs`, `cloud.google.com/blog`
- Framework docs: `docs.vllm.ai`, `docs.sglang.ai`, `huggingface.co/docs/text-generation-inference`
- PyTorch blog: `pytorch.org/blog`

Always pass a SPECIFIC extraction prompt to WebFetch (e.g. "Extract the section about FP8 grouped GEMM kernel for MI355X").

---

## 3. `WebSearch` — discovery (when the URL is unknown)

**When**: looking for blog posts / talks / vendor announcements about `{feature}` on `{chip}` for `{framework}` whose URL is not known. Always cross-reference with a `WebFetch` of the result before quoting.

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

Use `WebFetch` against the results page or `gh` against the `mlcommons/inference_results_v*` repo for a specific submission.

---

## 5. SemiAnalysis InferenceX — third-party perf reference

**When**: cross-checking framework-claimed perf numbers, finding alternative configurations, or sanity-checking absolute throughput.

**Source**: `https://github.com/SemiAnalysisAI/InferenceX`. Per memory, configs live under `.github/configs/{vendor}-master.yaml` (e.g. `nvidia-master.yaml`, `amd-master.yaml`).

Recipes:
```bash
gh api repos/SemiAnalysisAI/InferenceX/contents/.github/configs/<vendor>-master.yaml -H "Accept: application/vnd.github.raw"
gh search code 'in:file repo:SemiAnalysisAI/InferenceX <feature>' --limit 50
```

---

## Source-tag conventions

In `_meta.sources_used` use these tags exactly:
- `gh` — any GitHub CLI / API call
- `WebFetch:<host>` — e.g. `WebFetch:docs.vllm.ai`
- `WebSearch` — discovery search (the followup `WebFetch` is logged separately)
- `mlperf` — MLPerf data
- `inferencex` — SemiAnalysis InferenceX data
