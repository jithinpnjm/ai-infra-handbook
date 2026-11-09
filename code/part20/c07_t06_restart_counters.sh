#!/usr/bin/env bash
# Task 6: highest systemd restart counter per unit, from journal text.
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/journal.txt}"
# The unit name is the word before the colon in "unit: Scheduled restart job, restart counter is at N."
grep 'restart counter is at' "$F" | sed -E 's/.* ([A-Za-z0-9_.@-]+): Scheduled restart job, restart counter is at ([0-9]+)\./\1 \2/' |
  awk '{ if ($2 > max[$1]) max[$1]=$2 } END { for (u in max) print u, max[u] }' | sort -k2,2nr -k1,1
