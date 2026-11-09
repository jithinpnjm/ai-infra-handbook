#!/usr/bin/env bash
# Task 7: zombie processes, grouped by the parent that failed to reap them.
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/ps.txt}"
# STAT is column 3. A zombie starts with Z. Matching the column avoids false hits on
# names like ZMQ-broker. The fix is in the parent (column 2), not the zombie.
awk 'NR>1 && $3 ~ /^Z/ {c[$2]++} END {for (p in c) print "parent", p, "zombies", c[p]}' "$F" | sort -k4,4nr -k2,2n
