#!/usr/bin/env bash
# Scenario 6: pinned (page-locked) memory fails or a pod is OOM killed on a GPU host.
# Part A: lowered locked-memory limit. Needs Docker on Linux. Docker's default
# capabilities do not include IPC_LOCK, so RLIMIT_MEMLOCK applies inside the container.
# Part B: host-memory budget arithmetic for a hypothetical inference pod.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
command -v docker >/dev/null || { echo "docker not found"; exit 1; }

echo "== A: memlock limit 8 MiB, try to lock 1, 8, 64, 512 MiB"
docker run --rm --ulimit memlock=8388608:8388608 -v "$HERE:/w:ro" python:3.12-slim \
  python /w/c05_mlock_probe.py 1 8 64 512

echo "== A2: same, with IPC_LOCK granted (limit no longer enforced)"
docker run --rm --cap-add IPC_LOCK --ulimit memlock=8388608:8388608 -v "$HERE:/w:ro" \
  python:3.12-slim python /w/c05_mlock_probe.py 1 8 64 512

echo "== B: pod limit 24 GiB, 4 workers, 4 GiB pinned + 3 GiB anon each, 15 GiB weight cache"
python3 "$HERE/c05_host_mem_budget.py" 24 4 4 3 15
