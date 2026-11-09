#!/usr/bin/env bash
# Collect the Linux 60-second checklist (Systems Performance, 2nd ed, section 1.10.1).
# Read-only. Linux only. Usage: triage_first60.sh [OUTDIR]   SAMPLES=5 by default.
# Unverified flags (not in the books): timeout 30, mktemp -d, top -b -n 1.
set -u
if [ "$(uname -s)" != "Linux" ]; then
  echo "triage_first60.sh needs Linux; this is $(uname -s)." >&2
  exit 2
fi
out="${1:-$(mktemp -d /tmp/first60.XXXXXX)}"
mkdir -p "$out"
n="${SAMPLES:-5}"

# run NAME COMMAND...  writes OUTDIR/NAME.txt and notes a missing tool.
run() {
  name="$1"; shift
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "missing tool: $1" | tee "$out/$name.txt" >&2
    return 0
  fi
  timeout 30 "$@" >"$out/$name.txt" 2>&1 || echo "exit $? from: $*" >>"$out/$name.txt"
}

nproc >"$out/nproc.txt"
run uptime  uptime
run dmesg   dmesg -T
tail -n 50 "$out/dmesg.txt" >"$out/dmesg_tail.txt" 2>/dev/null
run vmstat  vmstat -SM 1 "$n"
run mpstat  mpstat -P ALL 1 "$n"
run pidstat pidstat 1 "$n"
run iostat  iostat -sxz 1 "$n"
run free    free -m
run sar_dev sar -n DEV 1 "$n"
run sar_tcp sar -n TCP,ETCP 1 "$n"
run top     top -b -n 1
run ss      ss -s

# PSI exists from Linux 4.20 (Systems Performance, section 6.6.1).
for r in cpu memory io; do
  [ -r "/proc/pressure/$r" ] && cp "/proc/pressure/$r" "$out/psi_$r.txt"
done
echo "wrote $out"
