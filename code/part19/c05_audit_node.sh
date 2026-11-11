#!/usr/bin/env bash
# Pre-benchmark audit of one node: topology, port state, modules, error counters.
# Usage: LAB_DIR=$HOME/fabric-lab-<stamp> c05_audit_node.sh
# Run once per node. Not run in this repository (needs GPUs and InfiniBand).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
LAB_DIR="${LAB_DIR:?set LAB_DIR}"
host="$(hostname -s)"
mkdir -p "$LAB_DIR/$host"

nvidia-smi topo -m          | tee "$LAB_DIR/$host/topology.txt"
nvidia-smi nvlink --status  | tee "$LAB_DIR/$host/nvlink-status.txt"
ibstat                      | tee "$LAB_DIR/$host/ibstat.txt"
rdma link show              | tee "$LAB_DIR/$host/rdma-links.txt"
lsmod | grep -Ei 'nvidia|peermem|rdma' | tee "$LAB_DIR/$host/modules.txt" || true
"$here/c05_counters.sh" "$LAB_DIR/$host/counters-before.txt"
