#!/usr/bin/env bash

set -euo pipefail

current_path=""
current_branch=""
current_head=""

print_row() {
  if [[ -z "$current_path" || -z "$current_head" || -z "$current_branch" ]]; then
    return
  fi

  local branch_display="${current_branch#refs/heads/}"
  local commit_date
  commit_date="$(git log -1 --format=%cs "$current_head")"
  printf "%-20s %-60s %s\n" "$branch_display" "$current_path" "$commit_date"
}

while IFS= read -r line || [[ -n "$line" ]]; do
  if [[ -z "$line" ]]; then
    print_row
    current_path=""
    current_branch=""
    current_head=""
    continue
  fi

  case "$line" in
    worktree\ *)
      current_path="${line#worktree }"
      ;;
    HEAD\ *)
      current_head="${line#HEAD }"
      ;;
    branch\ *)
      current_branch="${line#branch }"
      ;;
  esac
done < <(git worktree list --porcelain)

print_row
