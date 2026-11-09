#!/usr/bin/env bash
# Scenario 2: the disk is full but du cannot find the files. A deleted file is still open.
# Run as a normal user on Linux: bash ch04_s2_deleted_open.sh   (answer key: ... answer)
# Safe: one 20 MB file inside a temp dir, removed on exit.
set -u
if [ "${1:-}" = answer ]; then
  cat <<'KEY'
Cause: rm removed the NAME (link count went to 0) but a process still holds an open file
       description, so the kernel keeps the blocks until the last descriptor closes.
Proof: ls /proc/PID/fd shows the target with " (deleted)"; stat -L on the fd shows links=0
       and a size that df still counts; lsof +L1 lists files with link count below 1.
Not the cause: inode exhaustion (df -i is fine) or hidden mounts.
Fix now: copy out what you need with cp /proc/PID/fd/N, then truncate in place with
         : > /proc/PID/fd/N. No restart needed.
Fix for good: make the logger reopen its file on rotation (signal or copytruncate).
KEY
  exit 0
fi
[ "$(uname -s)" = Linux ] || { echo "Linux only. Use a Linux VM or container." >&2; exit 2; }
[ "$(id -u)" -ne 0 ] || { echo "Run as a normal user, not root." >&2; exit 2; }
W=$(mktemp -d "${TMPDIR:-/tmp}/ch04-s2.XXXXXX") || exit 1
trap 'kill $(jobs -p) 2>/dev/null; rm -rf "$W"' EXIT
F="$W/app.log"
dd if=/dev/zero of="$F" bs=1M count=20 status=none
used() { df -Pk "$W" | awk 'NR == 2 {print $3}'; }

( exec 3<>"$F"; exec sleep 300 ) &   # the "service" keeps the log open
HOLDER=$!
sleep 0.3
echo "--- before rm: filesystem used KB = $(used)"
rm "$F"
echo "--- after rm:  filesystem used KB = $(used)  (should barely move)"
echo "--- 1. du and ls cannot see it"
du -sk "$W"; ls -A "$W"
echo "--- 2. the process still holds it"
ls -l /proc/$HOLDER/fd/3
stat -L -c 'size=%s bytes, links=%h' /proc/$HOLDER/fd/3
command -v lsof >/dev/null && lsof +L1 -p "$HOLDER" 2>/dev/null | head -5
echo "--- 3. rescue the content, then free the space without a restart"
cp /proc/$HOLDER/fd/3 "$W/recovered.log" && ls -l "$W/recovered.log"
: > /proc/$HOLDER/fd/3
stat -L -c 'size after truncate=%s bytes' /proc/$HOLDER/fd/3
rm -f "$W/recovered.log"
echo "--- after truncate: filesystem used KB = $(used)"
