#!/usr/bin/env bash
# One line per resource for the USE method (Systems Performance, Appendix A).
# Read-only. Linux only. Prints raw numbers; you decide what they mean.
# Unverified flags (not in the books): df -x, df -i, nstat -az.
set -u
if [ "$(uname -s)" != "Linux" ]; then
  echo "triage_use_sweep.sh needs Linux; this is $(uname -s)." >&2
  exit 2
fi

cpus="$(nproc)"
read -r l1 l5 l15 _ < /proc/loadavg
echo "CPU    U/S  load $l1 $l5 $l15 on $cpus CPUs (load also counts tasks stuck in I/O)"

mem_total=$(awk '/^MemTotal:/ {print $2}' /proc/meminfo)
mem_avail=$(awk '/^MemAvailable:/ {print $2}' /proc/meminfo)
swap_total=$(awk '/^SwapTotal:/ {print $2}' /proc/meminfo)
swap_free=$(awk '/^SwapFree:/ {print $2}' /proc/meminfo)
echo "MEM    U    available ${mem_avail} kB of ${mem_total} kB; swap free ${swap_free} of ${swap_total} kB"
if dmesg >/dev/null 2>&1; then
  echo "MEM    E    dmesg lines with 'killed': $(dmesg 2>/dev/null | grep -c killed)"
else
  echo "MEM    E    dmesg not readable here (container or dmesg_restrict): known-unknown"
fi

for r in cpu memory io; do
  if [ -r "/proc/pressure/$r" ]; then
    echo "PSI    S    $r: $(head -n 1 /proc/pressure/$r)"
  else
    echo "PSI    S    $r: not available (needs Linux 4.20 or newer with PSI enabled)"
  fi
done

echo "FDS    U    system file-nr (allocated, unused, max): $(cat /proc/sys/fs/file-nr)"
echo "FDS    U    this shell ulimit -n: $(ulimit -n)"
echo "TASKS  U    threads-max: $(cat /proc/sys/kernel/threads-max)"
echo "DISK   U    capacity (df -h):"
df -h -x tmpfs -x devtmpfs 2>/dev/null | sed 's/^/                /'
echo "DISK   U    inodes (df -i):"
df -i -x tmpfs -x devtmpfs 2>/dev/null | sed 's/^/                /'
echo "NET    E    ip -s link (read the errors and dropped lines):"
ip -s link 2>/dev/null | sed 's/^/                /'
echo "NET    S    TCP retransmits (nstat TcpRetransSegs):"
nstat -az TcpRetransSegs 2>/dev/null | sed 's/^/                /'
echo "Known-unknowns: interconnects, per-disk errors, GPU. Use perf, smartctl, dcgmi."
