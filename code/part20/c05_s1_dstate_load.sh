#!/usr/bin/env bash
# Scenario 1: load average is high but CPUs are idle. Tasks wait on disk (state D).
# Safe: 8 writers x 512 MiB by default, in one scratch directory that is removed on exit.
# Run on a Linux VM, not on a shared production host.
set -euo pipefail
[ "$(uname -s)" = "Linux" ] || { echo "Linux only"; exit 1; }
WORKERS="${WORKERS:-8}"
MB="${MB:-512}"
DIR="${DIR:-/var/tmp/c05_s1}"
[ "$WORKERS" -le 16 ] && [ "$MB" -le 512 ] || { echo "refusing: keep WORKERS<=16 MB<=512"; exit 1; }
mkdir -p "$DIR"
trap 'kill $(jobs -p) 2>/dev/null || true; rm -rf "$DIR"' EXIT

for i in $(seq "$WORKERS"); do
  dd if=/dev/zero of="$DIR/f$i" bs=1M count="$MB" oflag=direct conv=fsync status=none &
done

sleep 1
echo "== uptime (load average counts D-state tasks on Linux)"
uptime
echo "== tasks in D state"
ps -eo stat,pid,comm | awk '$1 ~ /^D/' || true
echo "== vmstat: r is runnable, b is blocked, wa is iowait"
vmstat 1 3
echo "== PSI io (some = at least one task stalled)"
if [ -r /proc/pressure/io ]; then
  cat /proc/pressure/io
  python3 "$(dirname "$0")/c05_psi_parse.py" /proc/pressure/io /proc/pressure/cpu
else
  echo "no /proc/pressure/io on this kernel (PSI not enabled): read vmstat b and wa instead"
fi
wait
echo "done; scratch directory removed"
