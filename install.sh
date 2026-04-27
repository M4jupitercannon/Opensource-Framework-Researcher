#!/usr/bin/env bash
set -euo pipefail

SKILL_NAME="feature-research"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="symlink"
FORCE=0
TARGETS=()

usage() {
  cat <<'USAGE'
Install feature-research for Claude Code, Cursor, and/or Codex.

Usage:
  ./install.sh [--target all|claude|cursor|codex] [--symlink|--copy] [--force]

Options:
  --target VALUE   Install one target. May be repeated. Default: all.
  --symlink        Link this repo into skill directories. Default.
  --copy           Copy this repo into skill directories.
  --force          Move an existing non-matching install path to a timestamped backup.
  -h, --help       Show this help.

Targets:
  claude           ~/.claude/skills/feature-research
  cursor           ~/.cursor/skills/feature-research
  codex            ~/.codex/skills/feature-research plus a managed block in ~/.codex/AGENTS.md
USAGE
}

log() {
  printf '%s\n' "$*"
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_repo_file() {
  local path="$1"
  [[ -f "$REPO_DIR/$path" ]] || die "missing required repo file: $path"
}

backup_existing() {
  local dest="$1"
  local backup="${dest}.bak.$(date +%Y%m%d%H%M%S)"
  mv "$dest" "$backup"
  log "Moved existing $dest to $backup"
}

install_skill_dir() {
  local label="$1"
  local base_dir="$2"
  local dest="$base_dir/$SKILL_NAME"

  mkdir -p "$base_dir"

  if [[ -L "$dest" ]]; then
    local current
    current="$(readlink "$dest")"
    if [[ "$current" == "$REPO_DIR" ]]; then
      log "$label already installed at $dest"
      return
    fi
  fi

  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ "$FORCE" -ne 1 ]]; then
      die "$dest already exists. Re-run with --force to back it up and replace it."
    fi
    backup_existing "$dest"
  fi

  if [[ "$MODE" == "symlink" ]]; then
    ln -s "$REPO_DIR" "$dest"
    log "Installed $label skill symlink: $dest -> $REPO_DIR"
  else
    cp -a "$REPO_DIR" "$dest"
    log "Installed $label skill copy: $dest"
  fi
}

install_codex_agents_block() {
  local codex_dir="$HOME/.codex"
  local agents_file="$codex_dir/AGENTS.md"

  mkdir -p "$codex_dir"

  AGENTS_FILE="$agents_file" REPO_DIR="$REPO_DIR" python3 - <<'PY'
from __future__ import annotations

import os
from pathlib import Path

agents_file = Path(os.environ["AGENTS_FILE"])
repo_dir = Path(os.environ["REPO_DIR"])

begin = "<!-- BEGIN feature-research installer -->"
end = "<!-- END feature-research installer -->"
block = f"""{begin}

## feature-research

Use the feature-research workflow when the user asks for the state, roadmap,
status, dashboard, or report for a `(chip vendor, framework, feature)` triple.

Workflow repo: `{repo_dir}`

Read `{repo_dir / "AGENTS.md"}` first, then `{repo_dir / "SKILL.md"}` as the
canonical runbook. If no sub-agent or delegation tool is available, use the
serial fallback mode from `SKILL.md`.

{end}
"""

existing = agents_file.read_text(encoding="utf-8") if agents_file.exists() else ""
if begin in existing and end in existing:
    before, rest = existing.split(begin, 1)
    _, after = rest.split(end, 1)
    updated = before.rstrip() + "\n\n" + block + after.lstrip("\n")
else:
    prefix = existing.rstrip()
    updated = (prefix + "\n\n" if prefix else "") + block

agents_file.write_text(updated, encoding="utf-8")
PY

  log "Installed Codex managed instructions in $agents_file"
}

install_claude() {
  install_skill_dir "Claude Code" "$HOME/.claude/skills"
}

install_cursor() {
  install_skill_dir "Cursor" "$HOME/.cursor/skills"
}

install_codex() {
  install_skill_dir "Codex" "$HOME/.codex/skills"
  install_codex_agents_block
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      [[ $# -ge 2 ]] || die "--target requires a value"
      TARGETS+=("$2")
      shift 2
      ;;
    --symlink)
      MODE="symlink"
      shift
      ;;
    --copy)
      MODE="copy"
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

if [[ ${#TARGETS[@]} -eq 0 ]]; then
  TARGETS=("all")
fi

require_repo_file "SKILL.md"
require_repo_file "AGENTS.md"

expanded_targets=()
for target in "${TARGETS[@]}"; do
  case "$target" in
    all)
      expanded_targets+=("claude" "cursor" "codex")
      ;;
    claude|cursor|codex)
      expanded_targets+=("$target")
      ;;
    *)
      die "unknown target: $target"
      ;;
  esac
done

for target in "${expanded_targets[@]}"; do
  case "$target" in
    claude) install_claude ;;
    cursor) install_cursor ;;
    codex) install_codex ;;
  esac
done

log "Done."
