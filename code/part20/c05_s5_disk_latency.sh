#!/usr/bin/env bash
# Scenario 5: same disk, two workloads. Many small synchronous writes versus big sequential ones.
# Compare await, areq-sz and %util. Safe: 20 MiB of 4 KiB writes, then 256 MiB of 1 MiB writes.
# Writes to a real disk under DIR. Do not run on a busy production host.
set -euo pipefail
[ "$(uname -s)" = "Linux" ] || { echo "Linux only"; exit 1; }
command -v iostat >/dev/null || { echo "install sysstat for iostat"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
DIR="${DIR:-/var/tmp/c05_s5}"
mkdir -p "$DIR"
trap 'kill $(jobs -p) 2>/dev/null || true; rm -rf "$DIR"' EXIT

run() {  # $1 label, rest = dd arguments
  local label="$1"; shift
  iostat -sxz 1 6 > "$DIR/iostat.txt" &
  sleep 1
  dd if=/dev/zero of="$DIR/f" status=none "$@"
  wait
  echo "== $label"
  python3 "$HERE/c05_iostat_parse.py" < "$DIR/iostat.txt"
  rm -f "$DIR/f"
}
run "small synchronous writes (4 KiB, dsync)" bs=4k count=5000 oflag=dsync
run "large sequential writes (1 MiB, direct)" bs=1M count=256 oflag=direct
