#!/usr/bin/env bash
# Multi-node baseline: one MPI process per GPU, NCCL INFO log kept with the table.
# Usage: LAB_DIR=... HOSTS=node-a:8,node-b:8 NP=16 c05_run_multi_node.sh
# Not run in this repository (needs GPUs, InfiniBand and MPI).
set -euo pipefail
LAB_DIR="${LAB_DIR:?set LAB_DIR}"
HOSTS="${HOSTS:-node-a:8,node-b:8}"
NP="${NP:-16}"
BIN="${NCCL_TESTS:-$HOME/nccl-tests}/build"
mkdir -p "$LAB_DIR"

export NCCL_DEBUG=INFO
export NCCL_DEBUG_SUBSYS=INIT,NET,GRAPH
export NCCL_TOPO_DUMP_FILE="$LAB_DIR/nccl-topo.xml"

mpirun -np "$NP" -H "$HOSTS" \
  -x NCCL_DEBUG -x NCCL_DEBUG_SUBSYS -x NCCL_TOPO_DUMP_FILE \
  "$BIN/all_reduce_perf" -b 8M -e 1G -f 2 -g 1 -w 5 -n 100 -c 1 \
  2>&1 | tee "$LAB_DIR/multi-node-allreduce.txt"
