#!/usr/bin/env bash
# Record a 99 Hz system-wide CPU profile and turn it into a flame graph.
# Steps follow Systems Performance 2nd ed, chapters 6 and 13. Needs root and perf.
# 'perf script report flamegraph' needs Linux 5.8 or newer. For older kernels set
# FLAMEGRAPH_DIR to a clone of the FlameGraph repository.
set -euo pipefail
[ "$(uname -s)" = "Linux" ] || { echo "Linux only"; exit 1; }
command -v perf >/dev/null || { echo "perf not installed"; exit 1; }
SECONDS_TO_RECORD="${1:-10}"
OUT="${2:-/var/tmp/c05_flame}"
mkdir -p "$OUT"
cd "$OUT"

perf record -F 99 -a -g -o perf.data -- sleep "$SECONDS_TO_RECORD"
if [ -n "${FLAMEGRAPH_DIR:-}" ]; then
  perf script -i perf.data --header > out.stacks
  "$FLAMEGRAPH_DIR/stackcollapse-perf.pl" < out.stacks | "$FLAMEGRAPH_DIR/flamegraph.pl" --hash > flame.svg
  echo "wrote $OUT/flame.svg"
else
  perf script -i perf.data report flamegraph
  echo "wrote flamegraph.html in $OUT"
fi
echo "read the widest towers first; width is samples, left-to-right order has no meaning"
