<!-- markdownlint-disable MD041 -->
# {{framework}} {{feature}} Comparison — {{vendor_a}} vs {{vendor_b}}

> **Scope:** v1 supports exactly two vendors per C4. For three or more, run separate pairs. Known v2 work item: extend to N>2 vendors (see plan §C4).

**Generated:** {{date}} · **Window:** {{search_window.display}} · **Vendors:** {{vendor_a}}, {{vendor_b}}

## At-a-Glance Comparison

| Topic | {{vendor_a}} | {{vendor_b}} | Delta / Notes |
|---|---|---|---|
[loop topic in topics]
| {{topic.heading}} | {{topic.count_a}} | {{topic.count_b}} | {{topic.delta_note}} |
[/loop]

## Per-topic Highlights

[loop topic in topics]
### {{topic.heading}}

- **{{vendor_a}}**: {{topic.headline_a}} ([full]({{vendor_a}}/REPORT.md#{{topic.anchor}}))
- **{{vendor_b}}**: {{topic.headline_b}} ([full]({{vendor_b}}/REPORT.md#{{topic.anchor}}))
- **Common items**: {{topic.common}}
- **Vendor-only items**: {{topic.unique}}
[/loop]

[render_if_present ecosystem_plots]
## Ecosystem Activity Context

[loop plot in ecosystem_plots]
![{{plot.title}}](ecosystem_plots/{{plot.png_filename}})

Window: {{plot.window}}. Repos: {{plot.repos_summary}}. Vendor groups: {{vendor_a}} vs {{vendor_b}}. Source: {{plot.source_tag}} (see [`ecosystem_plots/{{plot.methods_filename}}`](ecosystem_plots/{{plot.methods_filename}})).

[/loop]
[/render_if_present]

## Verification Footer

Per-vendor verification reports:
- {{vendor_a}}: [`{{vendor_a}}/verification_existence.md`]({{vendor_a}}/verification_existence.md), [`{{vendor_a}}/verification_scope.md`]({{vendor_a}}/verification_scope.md), [`{{vendor_a}}/verification_feature.md`]({{vendor_a}}/verification_feature.md)
- {{vendor_b}}: [`{{vendor_b}}/verification_existence.md`]({{vendor_b}}/verification_existence.md), [`{{vendor_b}}/verification_scope.md`]({{vendor_b}}/verification_scope.md), [`{{vendor_b}}/verification_feature.md`]({{vendor_b}}/verification_feature.md)

Fallback usage (mcp:signals → gh): {{vendor_a}} {{fallback_count_a}} of {{ref_total_a}} refs · {{vendor_b}} {{fallback_count_b}} of {{ref_total_b}} refs.

---

## Notes

- All ecosystem-plot paths are relative to `out_dir/` (top-level `ecosystem_plots/` per C8.1, NOT under any vendor folder).
- All per-vendor links are relative to `out_dir/` (per-vendor outputs live under `out_dir/{vendor}/` per Phase 0 multi-vendor pathing).
- `{{search_window.display}}` (not `{{search_window}}` raw) per C2 + the `check_comparison_template` assertion.
- `[render_if_present ecosystem_plots]` because Phase 4 runs first per C1 (Phase 4 → Phase 5 → Phase 6).

## v2 work item

C4 caps comparison at exactly 2 vendors in v1. For N>2, run separate pairs of vendors. A future v2 extension would generalise `{{vendor_a}}`/`{{vendor_b}}` to `{{vendors[*]}}` looped across the N-element vendor list — left as a documented known limitation.
