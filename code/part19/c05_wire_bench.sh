#!/usr/bin/env bash
# perftest wire benchmark between two nodes, host memory or GPU memory.
# Usage on the server node:  ROLE=server c05_wire_bench.sh
#        on the client node: ROLE=client SERVER=node-a c05_wire_bench.sh
# Optional: HCA (default mlx5_0), NUMA (default 0), GPU (set to test GPU memory).
# Not run in this repository. Check the flags against `ib_write_bw -h` on your build.
set -euo pipefail
ROLE="${ROLE:?ROLE=server or client}"
HCA="${HCA:-mlx5_0}"
NUMA="${NUMA:-0}"
DUR="${DUR:-30}"

cuda=()
[ -n "${GPU:-}" ] && cuda=("--use_cuda=$GPU")

cmd=(ib_write_bw -d "$HCA" -i 1 --report_gbits --duration "$DUR" "${cuda[@]}")
case "$ROLE" in
  server) exec numactl --cpunodebind="$NUMA" --membind="$NUMA" "${cmd[@]}" ;;
  client) exec numactl --cpunodebind="$NUMA" --membind="$NUMA" "${cmd[@]}" "${SERVER:?set SERVER}" ;;
  *) echo "ROLE must be server or client" >&2; exit 2 ;;
esac
