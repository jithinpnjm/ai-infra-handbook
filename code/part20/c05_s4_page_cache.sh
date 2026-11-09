#!/usr/bin/env bash
# Scenario 4: "free memory is almost zero". Page cache grows, then shrinks when the file is deleted.
# Safe: writes one 512 MiB file (override with MB) and removes it. Linux only.
set -euo pipefail
[ "$(uname -s)" = "Linux" ] || { echo "Linux only"; exit 1; }
MB="${MB:-512}"
[ "$MB" -le 2048 ] || { echo "refusing: MB<=2048"; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
FILE="${FILE:-/var/tmp/c05_s4.bin}"
trap 'rm -f "$FILE"' EXIT

show() {
  echo "== $1"
  grep -E '^(MemFree|MemAvailable|Cached|Dirty):' /proc/meminfo
  python3 "$HERE/c05_meminfo_parse.py"
}
show "before"
dd if=/dev/zero of="$FILE" bs=1M count="$MB" status=none
show "after writing $MB MiB (Cached up, MemAvailable barely moves)"
cat "$FILE" > /dev/null
rm -f "$FILE"
show "after deleting the file (its cache pages are freed)"
