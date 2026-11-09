#!/usr/bin/env bash
# Scenario 2: a container is slow while the node is mostly idle. CFS quota throttling.
# Needs Docker on Linux. Uses a 0.5 CPU limit and 4 busy loops for 5 seconds.
set -euo pipefail
command -v docker >/dev/null || { echo "docker not found"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# cpu.stat lives at /sys/fs/cgroup/cpu.stat on cgroup v2 and under cpu/ on v1.
docker run --rm --cpus=0.5 alpine:3.20 sh -c '
  f=/sys/fs/cgroup/cpu.stat; [ -r "$f" ] || f=/sys/fs/cgroup/cpu/cpu.stat
  cat "$f" > /tmp/before
  for i in 1 2 3 4; do timeout 5 sh -c "while :; do :; done" & done
  wait
  cat "$f" > /tmp/after
  echo "--- before"; cat /tmp/before; echo "--- after"; cat /tmp/after
  echo "--- cpu.max (v2 only)"; cat /sys/fs/cgroup/cpu.max 2>/dev/null || true
' | tee "$TMP/out.txt"

awk '/--- before/{f="b";next} /--- after/{f="a";next} /--- cpu.max/{f="";next}
     f=="b"{print > "'"$TMP"'/before"} f=="a"{print > "'"$TMP"'/after"}' "$TMP/out.txt"
python3 "$HERE/c05_cpu_throttle.py" "$TMP/before" "$TMP/after"
