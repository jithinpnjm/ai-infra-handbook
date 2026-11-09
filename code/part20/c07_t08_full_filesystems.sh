#!/usr/bin/env bash
# Task 8: filesystems at 85 percent or more, excluding tmpfs and overlay.
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/df.txt}"
# Mount points can contain spaces, so rebuild the mount from field 6 onward.
# Capacity is field 5, like 98%. awk converts it to a number with +0.
awk 'NR>1 && $1 != "tmpfs" && $1 != "overlay" && ($5+0) >= 85 {
       m=$6; for (i=7; i<=NF; i++) m=m " " $i
       print ($5+0) "% " m }' "$F" | sort -k1,1nr -k2
