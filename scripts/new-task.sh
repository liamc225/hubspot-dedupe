#!/usr/bin/env bash

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <branch-name> [--scope path1,path2]"
  exit 1
fi

branch_name="$1"
shift

scope="unrestricted"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope)
      if [[ $# -lt 2 ]]; then
        echo "--scope requires a comma-separated value"
        exit 1
      fi
      scope="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

case "$branch_name" in
  feat/*|fix/*|chore/*|refactor/*|test/*|docs/*)
    ;;
  *)
    echo "Branch names must start with feat/, fix/, chore/, refactor/, test/, or docs/"
    exit 1
    ;;
esac

if git show-ref --verify --quiet "refs/heads/$branch_name"; then
  echo "Branch already exists: $branch_name"
  exit 1
fi

safe_name="${branch_name//\//-}"
worktree_path="worktrees/$safe_name"

git worktree add -b "$branch_name" "$worktree_path" main

cp CLAUDE.md "$worktree_path/CLAUDE.md"

cat > "$worktree_path/SCOPE.md" <<EOF
# Scope

This worktree may modify:
- $scope
EOF

if [[ -f .env ]]; then
  cp .env "$worktree_path/.env"
fi

echo "Created worktree: $worktree_path"
echo "cd $worktree_path"
echo "Scope: $scope"

