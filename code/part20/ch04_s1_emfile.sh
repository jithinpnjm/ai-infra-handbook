#!/usr/bin/env bash
# Scenario 1: "Too many open files". A process leaks descriptors until open() fails.
# Run as a normal user on Linux: bash ch04_s1_emfile.sh   (answer key: bash ch04_s1_emfile.sh answer)
# Safe: the leaker lowers ITS OWN soft limit to 24 and only opens one temp file.
set -u
if [ "${1:-}" = answer ]; then
  cat <<'KEY'
Cause: the process holds as many descriptors as its soft RLIMIT_NOFILE allows (24 here).
Proof: count of /proc/PID/fd entries is at or one below the Soft Limit in /proc/PID/limits, and nearly every
       extra entry points at the same file. strace would show openat() = -1 EMFILE.
Not the cause: /proc/sys/fs/file-max (system-wide, would give ENFILE, not EMFILE).
Fix now: restart the process, or raise its limit live with prlimit --pid PID --nofile=N:N (needs privilege).
Fix for good: find the missing close() and set LimitNOFILE= in the unit if the real need is high.
KEY
  exit 0
fi
[ "$(uname -s)" = Linux ] || { echo "Linux only. Use a Linux VM or container." >&2; exit 2; }
[ "$(id -u)" -ne 0 ] || { echo "Run as a normal user, not root." >&2; exit 2; }
W=$(mktemp -d "${TMPDIR:-/tmp}/ch04-s1.XXXXXX") || exit 1
trap 'kill $(jobs -p) 2>/dev/null; rm -rf "$W"' EXIT
echo data > "$W/data"

# The broken "service": leaks one descriptor per loop until open() fails.
(
  ulimit -n 24
  # bash numbers {fd} redirections from 10 upward, so fill 3 to 8 by hand. Fd 9 is the log
  # file, opened first, because no redirect can be made once the limit is hit.
  exec 9>"$W/leaker.log" 3<"$W/data" 4<"$W/data" 5<"$W/data" 6<"$W/data" 7<"$W/data" 8<"$W/data"
  n=0
  while exec {fd}<"$W/data" 2>/dev/null; do n=$((n + 1)); done
  exec 1>&9
  echo "leaker: open() failed after $n extra descriptors"
  exec sleep 120
) &
LEAKER=$!
for _ in 1 2 3 4 5 6 7 8 9 10; do [ -s "$W/leaker.log" ] && break; sleep 0.2; done

echo "--- 1. what the app logged"
cat "$W/leaker.log"
echo "--- 2. USE method: descriptors in use versus the soft limit"
echo "open: $(ls /proc/$LEAKER/fd | wc -l)"
grep 'Max open files' /proc/$LEAKER/limits
echo "--- 3. what the descriptors point at"
ls -l /proc/$LEAKER/fd | awk 'NR > 1 {print $NF}' | sort | uniq -c
echo "--- 4. is it the system-wide limit? (three numbers: allocated, free, max)"
cat /proc/sys/fs/file-nr
echo "--- 5. the same view from the helper"
HERE=$(cd "$(dirname "$0")" && pwd)
[ -f "$HERE/ch04_fd_triage.py" ] && python3 "$HERE/ch04_fd_triage.py" "$LEAKER"
