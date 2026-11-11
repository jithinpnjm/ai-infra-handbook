#!/usr/bin/env bash
# Run the analyser over the saved tables. Exit status is non-zero on any flag.
# Usage: LAB_DIR=... LINK_GBPS=400 SINGLE_RANKS=8 MULTI_RANKS=16 c05_certify.sh
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
LAB_DIR="${LAB_DIR:?set LAB_DIR}"
LINK_GBPS="${LINK_GBPS:-400}"
SINGLE_RANKS="${SINGLE_RANKS:-8}"
MULTI_RANKS="${MULTI_RANKS:-16}"

rc=0
# The single-node run is bounded by NVLink, not the NIC, so the link-rate check is
# left out and the baseline comparison, when a baseline exists, does the work.
python3 "$here/c05_nccl_parse.py" "$LAB_DIR/single-node-allreduce.txt" \
  --ranks "$SINGLE_RANKS" ${BASELINE_SINGLE:+--baseline "$BASELINE_SINGLE"} || rc=1
python3 "$here/c05_nccl_parse.py" "$LAB_DIR/multi-node-allreduce.txt" \
  --ranks "$MULTI_RANKS" --link-gbps "$LINK_GBPS" ${BASELINE_MULTI:+--baseline "$BASELINE_MULTI"} || rc=1
exit "$rc"
