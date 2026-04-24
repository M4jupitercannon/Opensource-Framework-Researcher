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
- **in_scope**: `SM90` (Hopper datacenter H100/H200/H20/GH200), `SM100` (Blackwell datacenter B100/B200/GB200), `SM103` (Blackwell Ultra datacenter B300/GB300), `SM120` (Blackwell — consumer GeForce RTX 50-series **and** workstation RTX PRO 6000 Blackwell), `SM121` (Blackwell DGX-Spark desktop AI workstation, GB10B)
- **out_of_scope_drops**:
  - `SM80` — Ampere A100 (prior generation)
  - `SM86` — Ampere consumer/workstation (RTX 30-series, A6000) — prior generation
  - `SM89` — Ada Lovelace (L40/L40S datacenter, RTX 40-series consumer) — prior generation; user-scoped to Hopper+Blackwell only
  - `SM110` — Jetson AGX Thor / DRIVE AGX Thor (Blackwell-based embedded/automotive) — outside "datacenter or consumer GPU" framing
  - All ROCm/AMD/MI300 references — different vendor
- **default_scope_statement**: `NVIDIA Hopper and Blackwell GPUs (datacenter and consumer) — Hopper SM90 (H100/H200/H20/GH200), Blackwell SM100 (B100/B200/GB200), Blackwell Ultra SM103 (B300/GB300), Blackwell SM120 (GeForce RTX 50-series and RTX PRO 6000 Blackwell), Blackwell SM121 (DGX-Spark/GB10B). Prior generations (Ampere SM80/SM86, Ada SM89) and embedded/automotive Blackwell (Jetson/DRIVE AGX Thor SM110) are excluded; specific dropped items are listed in the Verification Footer.`

---

## AMD

- **aliases**: `AMD`, `amd`, `rocm`, `instinct`, `radeon`
- **in_scope**: `CDNA3` (MI300X, MI300A, MI325X, datacenter), `CDNA4` (MI355X, MI350X, datacenter), `RDNA3` (consumer Radeon RX 7000, workstation Radeon PRO W7000), `RDNA4` (consumer Radeon RX 9000, workstation Radeon AI PRO R9700/R9600D)
- **out_of_scope_drops**:
  - `CDNA2` — MI210/MI250/MI250X (prior datacenter generation, limited FP8)
  - `CDNA1` — MI100
  - `RDNA2` — Radeon RX 6000 / W6000 (prior consumer generation)
  - `RDNA1` — Radeon RX 5000
  - `RDNA3.5` — Strix Point/Halo integrated APU graphics (not a discrete AI accelerator)
  - GCN-era and older
  - All NVIDIA/CUDA-only references
- **default_scope_statement**: `AMD CDNA3/CDNA4 Instinct datacenter accelerators and RDNA3/RDNA4 consumer/workstation Radeon — CDNA3 (MI300X/MI300A/MI325X), CDNA4 (MI355X/MI350X), RDNA3 (RX 7000, PRO W7000), RDNA4 (RX 9000, AI PRO R9700/R9600D). Prior generations (CDNA1/CDNA2 MI100/MI210/MI250, RDNA1/RDNA2 RX 5000/6000), RDNA3.5 integrated APUs, and GCN-era are excluded; specific dropped items are listed in the Verification Footer.`

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
