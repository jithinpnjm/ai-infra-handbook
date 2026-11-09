#!/usr/bin/env bash
# Print the 'some' avg10 value of cpu, memory and io pressure once a second.
# Pass a cgroup v2 directory to watch one container instead of the whole node.
# Usage: c05_psi_watch.sh [SECONDS] [/sys/fs/cgroup/<path>]
set -euo pipefail
SECS="${1:-10}"
BASE="${2:-/proc/pressure}"
SUFFIX=""
[ "$BASE" = "/proc/pressure" ] || SUFFIX=".pressure"

for kind in cpu memory io; do
  [ -r "$BASE/$kind$SUFFIX" ] || { echo "no $BASE/$kind$SUFFIX (PSI needs Linux 4.20+)"; exit 1; }
done
printf '%-8s %8s %8s %8s\n' time cpu mem io
for _ in $(seq "$SECS"); do
  row="$(date +%T)"
  for kind in cpu memory io; do
    v="$(awk '$1=="some"{split($2,a,"="); print a[2]}' "$BASE/$kind$SUFFIX")"
    row="$row $v"
  done
  # shellcheck disable=SC2086
  printf '%-8s %8s %8s %8s\n' $row
  sleep 1
done
