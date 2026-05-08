# Chip-vendor scope map

The ROCm-agent reads this file in Phase 0 to derive `scope.json`. Each vendor block defines:
- `in_scope` - accelerator generations / SM-or-equivalent codes treated as in-scope.
- `out_of_scope_drops` - known SKUs to actively drop from research outputs (with reasons).
- `default_scope_statement` - a one-line string the agent embeds VERBATIM into the report header.
- `aliases` - strings that resolve to this vendor (case-insensitive), not a complete search term list.
- `product_aliases` - structured product identifiers grouped by in-scope code.
- `search_terms` - explicit tokens allowed for GitHub and web hardware queries.

Product identifiers that appear only in `in_scope` prose, `default_scope_statement`, or `product_aliases` are descriptive context, not searchable terms. Phase 0 must derive hardware queries only from explicit `search_terms`, with `product_aliases` used for validation and grouping unless the same value also appears in `search_terms`.

If the user passes a hardware focus input, preserve `default_scope_statement` verbatim and write the narrowed wording separately as `effective_scope_statement`.

## Machine-readable source of truth

Phase 0 parses the fenced JSON block below as the authoritative AMD/NVIDIA chip scope. The human-readable vendor sections that follow are a mirror for review. If they drift, the JSON block wins and the scope monitor must report the drift.

```json
{
  "schema": "rocm_agent_scope.v1",
  "vendors": {
    "nvidia": {
      "aliases": ["NVIDIA", "nv", "nvidia", "cuda"],
      "product_aliases": {
        "SM90": ["Hopper", "H100", "H200", "H20", "GH200"],
        "SM100": ["Blackwell", "B100", "B200", "GB200"],
        "SM103": ["Blackwell Ultra", "B300", "GB300"],
        "SM120": ["GeForce RTX 50", "RTX 50", "RTX PRO 6000 Blackwell"],
        "SM121": ["DGX Spark", "DGX-Spark", "GB10B"]
      },
      "search_terms": ["NVIDIA", "CUDA", "Hopper", "Blackwell", "Blackwell Ultra", "SM90", "SM100", "SM103", "SM120", "SM121", "H100", "H200", "H20", "GH200", "B100", "B200", "GB200", "B300", "GB300", "GeForce RTX 50", "RTX PRO 6000 Blackwell", "DGX Spark", "GB10B"],
      "in_scope": ["SM90 (Hopper datacenter H100/H200/H20/GH200)", "SM100 (Blackwell datacenter B100/B200/GB200)", "SM103 (Blackwell Ultra datacenter B300/GB300)", "SM120 (Blackwell consumer GeForce RTX 50-series and workstation RTX PRO 6000 Blackwell)", "SM121 (Blackwell DGX-Spark desktop AI workstation, GB10B)"],
      "out_of_scope_drops": ["SM80 - Ampere A100 (prior generation)", "SM86 - Ampere consumer/workstation (RTX 30-series, A6000) - prior generation", "SM89 - Ada Lovelace (L40/L40S datacenter, RTX 40-series consumer) - prior generation; user-scoped to Hopper+Blackwell only", "SM110 - Jetson AGX Thor / DRIVE AGX Thor (Blackwell-based embedded/automotive) - outside \"datacenter or consumer GPU\" framing", "All ROCm/AMD/MI300 references - different vendor"],
      "default_scope_statement": "NVIDIA Hopper and Blackwell GPUs (datacenter and consumer) - Hopper SM90 (H100/H200/H20/GH200), Blackwell SM100 (B100/B200/GB200), Blackwell Ultra SM103 (B300/GB300), Blackwell SM120 (GeForce RTX 50-series and RTX PRO 6000 Blackwell), Blackwell SM121 (DGX-Spark/GB10B). Prior generations (Ampere SM80/SM86, Ada SM89) and embedded/automotive Blackwell (Jetson/DRIVE AGX Thor SM110) are excluded; specific dropped items are listed in the Verification Footer."
    },
    "amd": {
      "aliases": ["AMD", "amd", "rocm", "instinct", "radeon"],
      "product_aliases": {
        "CDNA3": ["MI300X", "MI300A", "MI325X"],
        "CDNA4": ["MI355X", "MI350X"],
        "RDNA3": ["Radeon RX 7000", "Radeon PRO W7000", "RX 7000", "PRO W7000"],
        "RDNA4": ["Radeon RX 9070", "Radeon RX 9070 XT", "Radeon AI PRO R9700", "Radeon AI PRO R9600D", "RX 9070", "RX 9070 XT", "AI PRO R9700", "AI PRO R9600D"]
      },
      "search_terms": ["AMD", "ROCm", "HIP", "Instinct", "Radeon", "CDNA3", "CDNA4", "RDNA3", "RDNA4", "MI300X", "MI300A", "MI325X", "MI355X", "MI350X", "Radeon RX 7000", "Radeon PRO W7000", "Radeon RX 9070", "Radeon RX 9070 XT", "Radeon AI PRO R9700", "Radeon AI PRO R9600D"],
      "in_scope": ["CDNA3 (MI300X, MI300A, MI325X, datacenter)", "CDNA4 (MI355X, MI350X, datacenter)", "RDNA3 (consumer Radeon RX 7000, workstation Radeon PRO W7000)", "RDNA4 (consumer Radeon RX 9070/9070 XT, workstation Radeon AI PRO R9700/R9600D)"],
      "out_of_scope_drops": ["CDNA2 - MI210/MI250/MI250X (prior datacenter generation, limited FP8)", "CDNA1 - MI100", "RDNA2 - Radeon RX 6000 / W6000 (prior consumer generation)", "RDNA1 - Radeon RX 5000", "RDNA3.5 - Strix Point/Halo integrated APU graphics (not a discrete AI accelerator)", "GCN-era and older", "All NVIDIA/CUDA-only references"],
      "default_scope_statement": "AMD CDNA3/CDNA4 Instinct datacenter accelerators and RDNA3/RDNA4 consumer/workstation Radeon - CDNA3 (MI300X/MI300A/MI325X), CDNA4 (MI355X/MI350X), RDNA3 (RX 7000, PRO W7000), RDNA4 (RX 9070/9070 XT, AI PRO R9700/R9600D). Prior generations (CDNA1/CDNA2 MI100/MI210/MI250, RDNA1/RDNA2 RX 5000/6000), RDNA3.5 integrated APUs, and GCN-era are excluded; specific dropped items are listed in the Verification Footer."
    }
  }
}
```

---

## NVIDIA

- **aliases**: `NVIDIA`, `nv`, `nvidia`, `cuda`
- **product_aliases**:
  - `SM90`: `Hopper`, `H100`, `H200`, `H20`, `GH200`
  - `SM100`: `Blackwell`, `B100`, `B200`, `GB200`
  - `SM103`: `Blackwell Ultra`, `B300`, `GB300`
  - `SM120`: `GeForce RTX 50`, `RTX 50`, `RTX PRO 6000 Blackwell`
  - `SM121`: `DGX Spark`, `DGX-Spark`, `GB10B`
- **search_terms**: `NVIDIA`, `CUDA`, `Hopper`, `Blackwell`, `Blackwell Ultra`, `SM90`, `SM100`, `SM103`, `SM120`, `SM121`, `H100`, `H200`, `H20`, `GH200`, `B100`, `B200`, `GB200`, `B300`, `GB300`, `GeForce RTX 50`, `RTX PRO 6000 Blackwell`, `DGX Spark`, `GB10B`
- **in_scope**: `SM90` (Hopper datacenter H100/H200/H20/GH200), `SM100` (Blackwell datacenter B100/B200/GB200), `SM103` (Blackwell Ultra datacenter B300/GB300), `SM120` (Blackwell consumer GeForce RTX 50-series and workstation RTX PRO 6000 Blackwell), `SM121` (Blackwell DGX-Spark desktop AI workstation, GB10B)
- **out_of_scope_drops**:
  - `SM80` - Ampere A100 (prior generation)
  - `SM86` - Ampere consumer/workstation (RTX 30-series, A6000) - prior generation
  - `SM89` - Ada Lovelace (L40/L40S datacenter, RTX 40-series consumer) - prior generation; user-scoped to Hopper+Blackwell only
  - `SM110` - Jetson AGX Thor / DRIVE AGX Thor (Blackwell-based embedded/automotive) - outside "datacenter or consumer GPU" framing
  - All ROCm/AMD/MI300 references - different vendor
- **default_scope_statement**: `NVIDIA Hopper and Blackwell GPUs (datacenter and consumer) - Hopper SM90 (H100/H200/H20/GH200), Blackwell SM100 (B100/B200/GB200), Blackwell Ultra SM103 (B300/GB300), Blackwell SM120 (GeForce RTX 50-series and RTX PRO 6000 Blackwell), Blackwell SM121 (DGX-Spark/GB10B). Prior generations (Ampere SM80/SM86, Ada SM89) and embedded/automotive Blackwell (Jetson/DRIVE AGX Thor SM110) are excluded; specific dropped items are listed in the Verification Footer.`

---

## AMD

- **aliases**: `AMD`, `amd`, `rocm`, `instinct`, `radeon`
- **product_aliases**:
  - `CDNA3`: `MI300X`, `MI300A`, `MI325X`
  - `CDNA4`: `MI355X`, `MI350X`
  - `RDNA3`: `Radeon RX 7000`, `Radeon PRO W7000`, `RX 7000`, `PRO W7000`
  - `RDNA4`: `Radeon RX 9070`, `Radeon RX 9070 XT`, `Radeon AI PRO R9700`, `Radeon AI PRO R9600D`, `RX 9070`, `RX 9070 XT`, `AI PRO R9700`, `AI PRO R9600D`
- **search_terms**: `AMD`, `ROCm`, `HIP`, `Instinct`, `Radeon`, `CDNA3`, `CDNA4`, `RDNA3`, `RDNA4`, `MI300X`, `MI300A`, `MI325X`, `MI355X`, `MI350X`, `Radeon RX 7000`, `Radeon PRO W7000`, `Radeon RX 9070`, `Radeon RX 9070 XT`, `Radeon AI PRO R9700`, `Radeon AI PRO R9600D`
- **in_scope**: `CDNA3` (MI300X, MI300A, MI325X, datacenter), `CDNA4` (MI355X, MI350X, datacenter), `RDNA3` (consumer Radeon RX 7000, workstation Radeon PRO W7000), `RDNA4` (consumer Radeon RX 9070/9070 XT, workstation Radeon AI PRO R9700/R9600D)
- **out_of_scope_drops**:
  - `CDNA2` - MI210/MI250/MI250X (prior datacenter generation, limited FP8)
  - `CDNA1` - MI100
  - `RDNA2` - Radeon RX 6000 / W6000 (prior consumer generation)
  - `RDNA1` - Radeon RX 5000
  - `RDNA3.5` - Strix Point/Halo integrated APU graphics (not a discrete AI accelerator)
  - GCN-era and older
  - All NVIDIA/CUDA-only references
- **default_scope_statement**: `AMD CDNA3/CDNA4 Instinct datacenter accelerators and RDNA3/RDNA4 consumer/workstation Radeon - CDNA3 (MI300X/MI300A/MI325X), CDNA4 (MI355X/MI350X), RDNA3 (RX 7000, PRO W7000), RDNA4 (RX 9070/9070 XT, AI PRO R9700/R9600D). Prior generations (CDNA1/CDNA2 MI100/MI210/MI250, RDNA1/RDNA2 RX 5000/6000), RDNA3.5 integrated APUs, and GCN-era are excluded; specific dropped items are listed in the Verification Footer.`

---

## Other vendors

This skill is ROCm-agent and intentionally restricts chip scope to AMD and NVIDIA only. The fenced `rocm_agent_scope.v1` JSON block above is the sole source of truth for both vendors. Other accelerator scopes (Intel, Google TPU, multi-vendor) belong in a sibling skill or a shared scope file and must not be added here.
