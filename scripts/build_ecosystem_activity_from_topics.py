#!/usr/bin/env python3
"""Build Phase 4 activity CSVs from audited Phase 1-3 topic JSON files.

This is the cheap/default data path for the feature-activity plot. It reuses the
refs already collected and verified by the research + monitor phases, then
emits the same CSV schema consumed by ``plot_ecosystem_activity.py``:

    month,repo,vendor_group,count

The resulting plot is a curated-run statistic, not a fresh exhaustive GitHub
search. The methods note records that distinction and any refs skipped because
the topic schema did not carry the timestamp required for the selected metric.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable


METRIC_DATE_KEYS = {
    "merged_prs": ("merged_at", "mergedAt", "merged_at_iso", "mergedAtIso"),
    "opened_issues": ("created_at", "createdAt", "created", "created_at_iso", "createdAtIso"),
    "closed_issues": ("closed_at", "closedAt", "closed", "closed_at_iso", "closedAtIso"),
}

METRIC_REF_KIND = {
    "merged_prs": "pr",
    "opened_issues": "issue",
    "closed_issues": "issue",
}

ISSUE_PATH_HINTS = ("issues", "issue", "rfcs", "rfc", "linked_rfcs", "linked_issues")
PR_PATH_HINTS = ("prs", "pr", "linked_prs")


@dataclass(frozen=True)
class ActivityRef:
    vendor_group: str
    repo: str
    kind: str
    number: int
    title: str
    bucket_date: date
    topic_file: Path

    @property
    def month(self) -> str:
        return self.bucket_date.strftime("%Y-%m")


def parse_date(raw: Any) -> date | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return None
    text = str(raw).strip()
    if not text:
        return None
    match = re.match(r"^(\d{4}-\d{2}-\d{2})", text)
    if not match:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        try:
            return date.fromisoformat(match.group(1))
        except ValueError:
            return None


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected top-level object in {path}")
    return data


def load_search_window(session_out_dir: Path, topic_files: list[Path]) -> tuple[date | None, date | None, str]:
    search_window_path = session_out_dir / "search_window.json"
    if search_window_path.is_file():
        data = read_json(search_window_path)
        window = data.get("search_window", data)
        start = parse_date(window.get("start_date"))
        end = parse_date(window.get("end_date"))
        display = str(window.get("display") or f"{start or '?'}..{end or '?'}")
        return start, end, display

    for path in topic_files:
        meta = read_json(path).get("_meta", {})
        if not isinstance(meta, dict):
            continue
        window = meta.get("search_window")
        if not isinstance(window, dict):
            continue
        start = parse_date(window.get("start_date"))
        end = parse_date(window.get("end_date"))
        display = str(window.get("display") or f"{start or '?'}..{end or '?'}")
        return start, end, display

    return None, None, "not recorded"


def topic_files_for(session_out_dir: Path, vendor_groups: set[str] | None) -> list[Path]:
    files: list[Path] = []
    for topics_dir in sorted(session_out_dir.glob("*/topics")):
        if not topics_dir.is_dir():
            continue
        vendor = topics_dir.parent.name
        if vendor_groups and vendor not in vendor_groups:
            continue
        files.extend(sorted(topics_dir.glob("*.json")))
    return files


def walk(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[tuple[str, ...], dict[str, Any]]]:
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from walk(child, path + (str(key),))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from walk(child, path + (str(index),))


def path_has(path: tuple[str, ...], hints: tuple[str, ...]) -> bool:
    normalized = {part.lower() for part in path}
    return any(hint in normalized for hint in hints)


def first_date(candidate: dict[str, Any], metric: str) -> date | None:
    for key in METRIC_DATE_KEYS[metric]:
        parsed = parse_date(candidate.get(key))
        if parsed is not None:
            return parsed
    return None


def normalize_number(raw: Any) -> int | None:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.strip().isdigit():
        return int(raw.strip())
    return None


def is_merged_pr(candidate: dict[str, Any], path: tuple[str, ...]) -> bool:
    if path_has(path, ISSUE_PATH_HINTS) and not path_has(path, PR_PATH_HINTS):
        return False
    state = str(candidate.get("state") or candidate.get("verified_state") or "").upper()
    return not state or state == "MERGED"


def is_issue(candidate: dict[str, Any], path: tuple[str, ...]) -> bool:
    if path_has(path, PR_PATH_HINTS) and not path_has(path, ISSUE_PATH_HINTS):
        return False
    return path_has(path, ISSUE_PATH_HINTS)


def collect_refs(
    topic_file: Path,
    metric: str,
    *,
    start_date: date | None,
    end_date: date | None,
    stats: Counter[str],
) -> list[ActivityRef]:
    data = read_json(topic_file)
    meta = data.get("_meta", {})
    if not isinstance(meta, dict):
        stats["files_missing_meta"] += 1
        return []

    topic_name = str(meta.get("topic_name") or topic_file.stem)
    if topic_name == "external_repo_dependencies":
        stats["skipped_external_repo_dependency_files"] += 1
        return []

    vendor = str(meta.get("chip") or topic_file.parent.parent.name).strip()
    repo = str(meta.get("framework_repo") or "").strip()
    if not vendor:
        stats["files_missing_vendor"] += 1
        return []
    if not repo:
        stats["files_missing_repo"] += 1
        return []

    entries = data.get("entries", [])
    refs: list[ActivityRef] = []
    for path, candidate in walk(entries):
        number = normalize_number(candidate.get("number"))
        if number is None:
            continue

        if metric == "merged_prs":
            if not is_merged_pr(candidate, path):
                continue
        elif not is_issue(candidate, path):
            continue

        bucket_date = first_date(candidate, metric)
        if bucket_date is None:
            stats[f"skipped_missing_{metric}_date"] += 1
            continue
        if start_date is not None and bucket_date < start_date:
            stats["skipped_before_window"] += 1
            continue
        if end_date is not None and bucket_date > end_date:
            stats["skipped_after_window"] += 1
            continue

        title = str(candidate.get("title") or "").strip()
        refs.append(
            ActivityRef(
                vendor_group=vendor,
                repo=repo,
                kind=METRIC_REF_KIND[metric],
                number=number,
                title=title,
                bucket_date=bucket_date,
                topic_file=topic_file,
            )
        )
    return refs


def write_csv(path: Path, rows: list[tuple[str, str, str, int]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["month", "repo", "vendor_group", "count"])
        writer.writerows(rows)


def write_methods(
    path: Path,
    *,
    metric: str,
    session_out_dir: Path,
    window_display: str,
    topic_files: list[Path],
    refs_seen: int,
    duplicate_count: int,
    totals: Counter[tuple[str, str]],
    stats: Counter[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    total_count = sum(totals.values())
    files_text = "\n".join(
        f"- `{file.relative_to(session_out_dir)}`" for file in topic_files
    )
    totals_text = "\n".join(
        f"- `{repo}` / `{vendor}`: {count}"
        for (repo, vendor), count in sorted(totals.items())
    ) or "- None"
    skipped_text = "\n".join(
        f"- `{key}`: {value}" for key, value in sorted(stats.items()) if value
    ) or "- None"

    path.write_text(
        "\n".join(
            [
                f"# {metric} Methods",
                "",
                "Data source: audited Phase 1-3 topic JSONs only. No MCP, GitHub CLI, or web fetch was run in Phase 4 for this metric.",
                "",
                f"Session directory: `{session_out_dir}`",
                f"Window: {window_display}",
                f"Refs accepted before de-duplication: {refs_seen}",
                f"Duplicate refs skipped: {duplicate_count}",
                f"Total plotted refs: {total_count}",
                "",
                "## Topic Files Read",
                files_text or "- None",
                "",
                "## Totals",
                totals_text,
                "",
                "## Skips And Limitations",
                skipped_text,
                "",
                "This is a simple statistic over the curated run evidence, not an exhaustive ecosystem search. It only counts refs that survived the Phase 1-3 research and monitor flow and that carry the timestamp needed by this metric. In particular, `closed_issues` is often sparse unless the topic schema includes close dates.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def build(args: argparse.Namespace) -> int:
    session_out_dir = args.session_out_dir.resolve()
    vendor_groups = set(args.vendor_group or []) or None
    topic_files = topic_files_for(session_out_dir, vendor_groups)
    if not topic_files:
        raise SystemExit(f"No topic JSON files found under {session_out_dir}/*/topics")

    start_date, end_date, window_display = load_search_window(session_out_dir, topic_files)
    stats: Counter[str] = Counter()
    refs: list[ActivityRef] = []
    for topic_file in topic_files:
        refs.extend(
            collect_refs(
                topic_file,
                args.metric,
                start_date=start_date,
                end_date=end_date,
                stats=stats,
            )
        )

    seen: set[tuple[str, str, str, int]] = set()
    buckets: Counter[tuple[str, str, str]] = Counter()
    totals: Counter[tuple[str, str]] = Counter()
    duplicate_count = 0
    for ref in refs:
        dedupe_key = (ref.vendor_group, ref.repo, ref.kind, ref.number)
        if dedupe_key in seen:
            duplicate_count += 1
            continue
        seen.add(dedupe_key)
        buckets[(ref.month, ref.repo, ref.vendor_group)] += 1
        totals[(ref.repo, ref.vendor_group)] += 1

    rows = [
        (month, repo, vendor, count)
        for (month, repo, vendor), count in sorted(buckets.items())
    ]
    write_csv(args.csv, rows)
    write_methods(
        args.methods,
        metric=args.metric,
        session_out_dir=session_out_dir,
        window_display=window_display,
        topic_files=topic_files,
        refs_seen=len(refs),
        duplicate_count=duplicate_count,
        totals=totals,
        stats=stats,
    )

    print(f"wrote {args.csv}")
    print(f"wrote {args.methods}")
    print(f"topic_files={len(topic_files)} refs_seen={len(refs)} duplicates={duplicate_count} plotted={sum(totals.values())}")
    for (repo, vendor), count in sorted(totals.items()):
        print(f"series_total {repo} {vendor} {count}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a Phase 4 activity CSV from audited topic JSON files.",
    )
    parser.add_argument("--session-out-dir", required=True, type=Path)
    parser.add_argument(
        "--metric",
        required=True,
        choices=sorted(METRIC_DATE_KEYS),
    )
    parser.add_argument("--csv", required=True, type=Path, help="Output CSV path.")
    parser.add_argument("--methods", required=True, type=Path, help="Output methods note path.")
    parser.add_argument(
        "--vendor-group",
        action="append",
        default=None,
        help="Vendor group to include. Defaults to every <session>/<vendor>/topics directory.",
    )
    return build(parser.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
