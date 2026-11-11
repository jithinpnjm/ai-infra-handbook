#!/usr/bin/env bash
# Single-node baseline: one process, all GPUs, AllReduce sweep with the check on.
# Usage: LAB_DIR=... [NGPUS=8] [NCCL_TESTS=$HOME/nccl-tests] c05_run_single_node.sh
# Not run in this repository (needs GPUs).
set -euo pipefail
LAB_DIR="${LAB_DIR:?set LAB_DIR}"
NGPUS="${NGPUS:-8}"
BIN="${NCCL_TESTS:-$HOME/nccl-tests}/build"
mkdir -p "$LAB_DIR"

NCCL_DEBUG=INFO "$BIN/all_reduce_perf" -b 8M -e 1G -f 2 -g "$NGPUS" -w 5 -n 50 -c 1 \
  | tee "$LAB_DIR/single-node-allreduce.txt"
