#!/usr/bin/env bash
# One sweep per remaining collective on a single node.
# Usage: LAB_DIR=... [NGPUS=8] c05_run_matrix.sh
# Not run in this repository (needs GPUs).
set -euo pipefail
LAB_DIR="${LAB_DIR:?set LAB_DIR}"
NGPUS="${NGPUS:-8}"
BIN="${NCCL_TESTS:-$HOME/nccl-tests}/build"
mkdir -p "$LAB_DIR"

for t in reduce_scatter_perf all_gather_perf alltoall_perf broadcast_perf reduce_perf; do
  "$BIN/$t" -b 8M -e 1G -f 2 -g "$NGPUS" -w 5 -n 50 -c 1 | tee "$LAB_DIR/single-node-$t.txt"
done
