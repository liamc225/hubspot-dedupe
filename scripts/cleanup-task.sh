#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <branch-name-or-path>"
  exit 1
fi

target="$1"

if [[ -d "$target" ]]; then
  worktree_path="$target"
  branch_name="$(git -C "$worktree_path" branch --show-current)"
else
  safe_name="${target//\//-}"
  worktree_path="worktrees/$safe_name"
  branch_name="$target"
fi

git worktree remove --force "$worktree_path"

if git branch --merged main | grep -q " $branch_name$"; then
  git branch -d "$branch_name"
fi

git worktree list
