#!/usr/bin/env python3
"""Render an ecosystem-activity time-series PNG from a CSV produced by the
`plot_ecosystem_activity` Phase 4 sub-agent role.

Input CSV schema (header required):
    month,repo,vendor_group,count

Where:
- ``month`` is ``YYYY-MM``,
- ``repo`` is a full ``org/repo`` slug,
- ``vendor_group`` is one of the vendor names from ``scope/chip_scope_map.md``
  (e.g. ``AMD``, ``NVIDIA``) plus the literals ``BOTH`` and ``NEITHER``,
- ``count`` is an integer (a value of ``-1`` flags an upstream ``gh search``
  failure for that bucket and is skipped).

Upstream data-source variability (this script is unchanged):
    Per contract clarification C8, the CSV consumer contract
    ``month,repo,vendor_group,count`` is UNCHANGED — this renderer always
    consumes the same four-column CSV. All variability lives in the
    upstream Phase 4 sub-agent (``agents/plot_ecosystem_activity.md``):
    when ``MCP_SQL_USABLE=true`` (see ``sources/signals_service_discovered.md``)
    the agent issues ONE ``execute_sql`` per ``(repo, metric)`` returning
    RAW rows over the full window and classifies them client-side; when
    ``MCP_SQL_USABLE=false`` it falls back to the existing per-month
    per-repo ``gh search`` loop. **Either upstream path emits the same
    CSV schema**, so this script needs no changes either way.

    Per C8.1 the CSV and PNG live at the top-level
    ``{session_out_dir}/ecosystem_plots/`` (NOT under any vendor folder — Phase 4
    runs once per session, not per vendor). Per C8.2 the ``vendor_group``
    column values match the run's ``chip_list`` (e.g. ``AMD``, ``NVIDIA``
    by default, or ``Intel``, ``AMD`` when the user passes
    ``chip=[Intel, AMD]``); ``BOTH`` / ``NEITHER`` are CSV-only sentinels
    that the renderer drops.

The script plots one line per ``(repo, vendor_group)`` pair where
``vendor_group`` is in the canonical vendor list (``AMD``, ``NVIDIA``).
``BOTH`` and ``NEITHER`` rows are intentionally excluded — they live in
the CSV for downstream re-classification but are not plotted.

The visual style mirrors the reference chart: line + marker per series,
per-point integer labels, legend in the upper-left, and a wrapped footer
listing the window and (optionally) the keyword caveat.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

# matplotlib import is deferred until after argparse so ``--help`` works on
# environments where matplotlib is not yet installed.


PLOTTED_VENDOR_GROUPS = ("AMD", "NVIDIA")


METRIC_DEFAULT_TITLES = {
    "merged_prs": "Monthly Merged PRs Touching {vendors}",
    "opened_issues": "Monthly Opened Issues Touching {vendors}",
    "closed_issues": "Monthly Closed Issues Touching {vendors}",
}


DEFAULT_VENDOR_LABELS = {
    "AMD": "AMD/ROCm",
    "NVIDIA": "NVIDIA/CUDA",
}


# Framework names from the v1 default repo set; users can override via
# ``--repo-label`` to add other frameworks without touching this script.
DEFAULT_REPO_LABELS = {
    "vllm-project/vllm": "vLLM",
    "sgl-project/sglang": "SGLang",
}


# Color and marker assignments roughly matching the reference chart:
# vLLM/AMD = red, vLLM/NVIDIA = steel-blue, SGLang/AMD = orange,
# SGLang/NVIDIA = purple. Lookup falls back through the matplotlib default
# cycle for any new (repo, vendor) pair the user introduces.
SERIES_STYLE = {
    ("vLLM", "AMD"): {"color": "#D81B26", "marker": "o", "linestyle": "-"},
    ("vLLM", "NVIDIA"): {"color": "#1F6FB4", "marker": "s", "linestyle": "-"},
    ("SGLang", "AMD"): {"color": "#FF8C00", "marker": "^", "linestyle": "--"},
    ("SGLang", "NVIDIA"): {"color": "#7E57C2", "marker": "x", "linestyle": "--"},
}


def parse_kv_list(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items or []:
        if "=" not in item:
            sys.exit(f"--label argument must be KEY=VALUE, got: {item!r}")
        key, value = item.split("=", 1)
        out[key.strip()] = value.strip()
    return out


def load_rows(csv_path: Path) -> list[dict[str, str]]:
    if not csv_path.is_file():
        sys.exit(f"CSV not found: {csv_path}")
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"month", "repo", "vendor_group", "count"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            sys.exit(
                f"CSV {csv_path} is missing required columns: "
                f"{sorted(missing)}; got {reader.fieldnames}"
            )
        return list(reader)


def build_series(
    rows: list[dict[str, str]],
    vendor_groups: tuple[str, ...],
) -> tuple[list[str], dict[tuple[str, str], dict[str, int]]]:
    """Return (sorted_months, {(repo, vendor): {month: count}}).

    Rows where ``vendor_group`` is not in ``vendor_groups`` (e.g. ``BOTH`` /
    ``NEITHER``) or where ``count`` is negative (upstream ``gh search``
    error sentinel) are skipped silently for plotting; the methods note
    surfaces them.
    """

    months: set[str] = set()
    series: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        try:
            count = int(row["count"])
        except (TypeError, ValueError):
            continue
        if count < 0:
            continue
        vendor = row["vendor_group"].strip()
        if vendor not in vendor_groups:
            continue
        month = row["month"].strip()
        repo = row["repo"].strip()
        if not month or not repo:
            continue
        months.add(month)
        series[(repo, vendor)][month] += count
    return sorted(months), series


def label_for_repo(repo: str, overrides: dict[str, str]) -> str:
    if repo in overrides:
        return overrides[repo]
    if repo in DEFAULT_REPO_LABELS:
        return DEFAULT_REPO_LABELS[repo]
    return repo.split("/", 1)[-1] if "/" in repo else repo


def label_for_vendor(vendor: str, overrides: dict[str, str]) -> str:
    if vendor in overrides:
        return overrides[vendor]
    return DEFAULT_VENDOR_LABELS.get(vendor, vendor)


def style_for_series(repo_label: str, vendor: str, series_index: int) -> dict[str, str]:
    style = SERIES_STYLE.get((repo_label, vendor))
    if style is not None:
        return dict(style)
    fallback_markers = ["o", "s", "^", "x", "D", "P", "*", "v"]
    fallback_styles = ["-", "--", "-.", ":"]
    return {
        "color": f"C{series_index % 10}",
        "marker": fallback_markers[series_index % len(fallback_markers)],
        "linestyle": fallback_styles[(series_index // len(fallback_markers)) % len(fallback_styles)],
    }


def render(
    months: list[str],
    series: dict[tuple[str, str], dict[str, int]],
    *,
    title: str,
    repo_labels: dict[str, str],
    vendor_labels: dict[str, str],
    footer: str | None,
    out_path: Path,
) -> dict[tuple[str, str], int]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not months:
        sys.exit("No plottable rows found in CSV (after filtering BOTH / NEITHER / errors).")

    fig, ax = plt.subplots(figsize=(13, 6.5), dpi=120)

    series_totals: dict[tuple[str, str], int] = {}
    sorted_keys = sorted(
        series.keys(),
        key=lambda k: (label_for_repo(k[0], repo_labels), k[1]),
    )

    for index, (repo, vendor) in enumerate(sorted_keys):
        repo_label = label_for_repo(repo, repo_labels)
        vendor_label = label_for_vendor(vendor, vendor_labels)
        bucket = series[(repo, vendor)]
        ys = [bucket.get(month, 0) for month in months]
        series_totals[(repo, vendor)] = sum(ys)
        style = style_for_series(repo_label, vendor, index)
        line_label = f"{repo_label} \u2014 {vendor_label}"
        ax.plot(
            months,
            ys,
            label=line_label,
            color=style["color"],
            marker=style["marker"],
            linestyle=style["linestyle"],
            linewidth=1.6,
            markersize=6,
        )
        for month, value in zip(months, ys):
            if value <= 0:
                continue
            ax.annotate(
                str(value),
                xy=(month, value),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=7,
                color=style["color"],
            )

    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("Month")
    ax.set_ylabel(_axis_label_for_title(title))
    ax.grid(True, axis="y", linestyle=":", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9, frameon=True)
    fig.autofmt_xdate(rotation=60)

    if footer:
        fig.text(0.99, 0.01, footer, ha="right", va="bottom", fontsize=8, color="#444444")
        fig.subplots_adjust(bottom=0.22)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return series_totals


def _axis_label_for_title(title: str) -> str:
    lower = title.lower()
    if "issue" in lower:
        return "Issues / month"
    return "Merged PRs / month"


def default_title(metric: str, vendor_groups: tuple[str, ...], vendor_labels: dict[str, str]) -> str:
    template = METRIC_DEFAULT_TITLES.get(metric)
    if template is None:
        return f"Monthly Activity ({metric})"
    pretty = " vs ".join(label_for_vendor(v, vendor_labels) for v in vendor_groups)
    return template.format(vendors=pretty)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render an ecosystem-activity time-series PNG from a Phase 4 CSV.",
    )
    parser.add_argument(
        "--metric",
        required=True,
        choices=sorted(METRIC_DEFAULT_TITLES.keys()),
        help="Activity metric (drives the default plot title).",
    )
    parser.add_argument("--csv", required=True, type=Path, help="Input CSV path.")
    parser.add_argument("--out", required=True, type=Path, help="Output PNG path.")
    parser.add_argument(
        "--title",
        default=None,
        help="Overrides the default title for --metric.",
    )
    parser.add_argument(
        "--vendor-group",
        action="append",
        default=None,
        help=(
            "Vendor group name to plot; pass repeatedly. "
            "Defaults to AMD and NVIDIA. Names must match the vendor_group "
            "values present in the CSV."
        ),
    )
    parser.add_argument(
        "--vendor-label",
        action="append",
        default=[],
        metavar="VENDOR=LABEL",
        help="Override the legend label for a vendor (e.g. AMD=AMD/ROCm).",
    )
    parser.add_argument(
        "--repo-label",
        action="append",
        default=[],
        metavar="org/repo=LABEL",
        help="Override the legend prefix for a repo (e.g. vllm-project/vllm=vLLM).",
    )
    parser.add_argument(
        "--footer",
        default=None,
        help="Optional footer text drawn under the chart (e.g. window + caveats).",
    )

    args = parser.parse_args(argv)

    vendor_groups = tuple(args.vendor_group) if args.vendor_group else PLOTTED_VENDOR_GROUPS
    vendor_labels = parse_kv_list(args.vendor_label)
    repo_labels = parse_kv_list(args.repo_label)
    rows = load_rows(args.csv)
    months, series = build_series(rows, vendor_groups)
    title = args.title or default_title(args.metric, vendor_groups, vendor_labels)
    series_totals = render(
        months,
        series,
        title=title,
        repo_labels=repo_labels,
        vendor_labels=vendor_labels,
        footer=args.footer,
        out_path=args.out,
    )

    print(f"wrote {args.out}")
    print(f"months_plotted={len(months)} series={len(series_totals)}")
    for (repo, vendor), total in sorted(series_totals.items()):
        repo_label = label_for_repo(repo, repo_labels)
        vendor_label = label_for_vendor(vendor, vendor_labels)
        print(f"series_total {repo_label} {vendor_label} {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
