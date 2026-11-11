#!/usr/bin/env bash
# Build nccl-tests with MPI support. Run on every node, with the same paths.
# Needs a GPU host with CUDA, NCCL and an MPI install. Not run in this repository.
set -euo pipefail

: "${MPI_HOME:?set MPI_HOME to your MPI install, for example /opt/openmpi}"
: "${CUDA_HOME:=/usr/local/cuda}"
: "${NCCL_HOME:=}"                       # leave empty to use the system NCCL
SRC="${SRC:-$HOME/nccl-tests}"

[ -d "$SRC/.git" ] || git clone https://github.com/NVIDIA/nccl-tests.git "$SRC"

args=(MPI=1 "MPI_HOME=$MPI_HOME" "CUDA_HOME=$CUDA_HOME")
[ -n "$NCCL_HOME" ] && args+=("NCCL_HOME=$NCCL_HOME")
make -C "$SRC" -j "${args[@]}"

# Record exactly what was built, for the evidence pack.
git -C "$SRC" rev-parse HEAD | tee "$SRC/build/COMMIT"
ls "$SRC/build"/*_perf
