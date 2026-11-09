#!/usr/bin/env bash
# Task 4: p50, p95 and p99 of request_time by hand (nearest-rank method).
# Portable: runs with BSD (macOS) and GNU tools. Fixture is synthetic (see c07_make_fixtures.py).
set -euo pipefail
F="${1:-$(dirname "$0")/c07_fixtures/access.log}"
# Nearest rank: sort ascending, then take the value at position ceil(p/100 * N).
# awk has no ceil, so add 0.999999 and truncate with int().
awk '{print $NF}' "$F" | sort -n | awk '
  {v[NR]=$1}
  END {
    n=NR
    printf "n=%d", n
    split("50 95 99", ps, " ")
    for (i=1; i<=3; i++) {
      r=int(ps[i]/100*n + 0.999999); if (r<1) r=1
      printf " p%s=%.3f", ps[i], v[r]
    }
    printf "\n"
  }'
