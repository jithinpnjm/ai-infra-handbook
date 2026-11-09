#!/usr/bin/env bash
# Task 9: log files over 100 KiB that are not newer than ref.stamp, safe for spaces in names.
# Usage: c07_t09_find_old_logs.sh TREE   (TREE made by: c07_make_fixtures.py --tree TREE)
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic.
set -euo pipefail
T="${1:?usage: $0 TREE}"
# -print0 and xargs -0 use a NUL byte between names, so spaces never split a name.
# wc -c prints one byte count per file plus a "total" line, which sed and awk remove.
cd "$T"
find . -type f -name '*.log' -size +100k ! -newer ref.stamp -print0 | xargs -0 wc -c |
  awk '$2 != "total" {n=$1; sub(/^ *[0-9]+ /, ""); print n, $0}' | sort -k1,1nr -k2
