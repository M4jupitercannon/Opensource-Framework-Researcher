# Chip-vendor scope map

The main agent reads this file in Phase 0 to derive a `scope.json` for the chip vendor argument. Each vendor block defines:
- `in_scope` — accelerator generations / SM-or-equivalent codes treated as in-scope.
- `out_of_scope_drops` — known SKUs to actively drop from research outputs (with reasons).
- `default_scope_statement` — a one-line string the main agent embeds VERBATIM into the report header.
- `aliases` — strings that resolve to this vendor (case-insensitive).

If the user passes `scope_override`, it replaces the derived spec; the `default_scope_statement` is then synthesized as `f"User-supplied scope: {scope_override}"`.

---

## NVIDIA

- **aliases**: `NVIDIA`, `nv`, `nvidia`, `cuda`
- **in_scope**: `SM89` (L40/L40S, Ada datacenter), `SM90` (Hopper H100/H200/H20), `SM100` (Blackwell datacenter B100/B200/GB200), `SM120` (Blackwell datacenter RTX 6000 PRO Blackwell)
- **out_of_scope_drops**:
  - `SM80` — Ampere A100 (datacenter but pre-Ada/Hopper feature set)
  - `SM86` — Ampere A6000 / consumer (workstation, non-datacenter)
  - `SM89` consumer RTX 40-series — keep only L40/L40S (datacenter); drop RTX 4090/4080
  - `SM103` — B300 (not yet GA)
  - `SM121` — DGX-Spark
  - All ROCm/AMD/MI300 references — different vendor
- **default_scope_statement**: `NVIDIA datacenter GPUs only — Hopper (SM89/SM90), Blackwell (SM100/SM120). Out-of-scope NVIDIA SKUs (Ampere SM80/SM86, future B300/SM103, DGX-Spark/SM121, workstation RTX/SM120 non-PRO) are excluded; specific dropped items are listed in the Verification Footer.`

---

## AMD

- **aliases**: `AMD`, `amd`, `rocm`, `instinct`
- **in_scope**: `CDNA3` (MI300X, MI300A, MI325X), `CDNA4` (MI355X, MI350X)
- **out_of_scope_drops**:
  - `CDNA2` — MI250/MI250X (older datacenter, limited FP8)
  - `CDNA1` — MI100
  - `RDNA3`/`RDNA4` — consumer/workstation Radeon
  - All NVIDIA/CUDA-only references
- **default_scope_statement**: `AMD Instinct datacenter accelerators only — CDNA3 (MI300X/MI300A/MI325X), CDNA4 (MI355X/MI350X). Older CDNA1/CDNA2 (MI100/MI250) and consumer RDNA are excluded.`

---

## Intel

- **aliases**: `Intel`, `intel`, `xpu`, `gaudi`, `habana`, `pvc`
- **in_scope**: `Gaudi2`, `Gaudi3` (Habana datacenter), `PVC` (Ponte Vecchio / Data Center GPU Max), `BMG` if datacenter (Battlemage)
- **out_of_scope_drops**:
  - Consumer Arc (`A770`, `B580`)
  - `Gaudi1` (older)
  - All NVIDIA/AMD references
- **default_scope_statement**: `Intel datacenter accelerators only — Habana Gaudi2/Gaudi3 and Data Center GPU Max (Ponte Vecchio). Consumer Arc and Gaudi1 are excluded.`

---

## Google TPU

- **aliases**: `Google`, `google`, `TPU`, `tpu`
- **in_scope**: `TPUv4`, `TPUv5e`, `TPUv5p`, `TPUv6` (Trillium), `TPUv7` (Ironwood) when GA
- **out_of_scope_drops**:
  - `TPUv2`, `TPUv3` (legacy)
  - Edge TPU
  - All non-Google references
- **default_scope_statement**: `Google Cloud TPU — v4, v5e, v5p, v6 Trillium, v7 Ironwood (when GA). Legacy v2/v3 and Edge TPU are excluded.`

---

## Multi-vendor (`MULTI` / unspecified)

If chip is `MULTI`, `all`, `any`, or unspecified: `default_scope_statement` = `Multi-vendor scope — items kept regardless of accelerator. Each entry annotated with hardware in its own field.`. No `out_of_scope_drops`.
