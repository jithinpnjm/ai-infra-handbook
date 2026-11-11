#!/usr/bin/env bash
# Dump every InfiniBand port counter under /sys/class/infiniband to one file.
# Usage: c05_counters.sh OUTFILE
set -euo pipefail
out="${1:?usage: c05_counters.sh OUTFILE}"
for dev in /sys/class/infiniband/*/ports/*/counters; do
  [ -d "$dev" ] || continue
  echo "### $dev"
  grep -H . "$dev"/* 2>/dev/null || true
done > "$out"
echo "wrote $(wc -l < "$out") lines to $out"
