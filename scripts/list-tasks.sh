#!/usr/bin/env bash

set -euo pipefail

git worktree list --porcelain | awk '
  /^worktree / { path=$2 }
  /^branch / { branch=$2 }
  /^HEAD / {
    cmd = "git log -1 --format=%cs " $2
    cmd | getline date
    close(cmd)
    gsub("refs/heads/", "", branch)
    printf "%-20s %-40s %s\n", branch, path, date
  }
'

