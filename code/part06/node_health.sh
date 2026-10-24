#!/bin/bash
# Minimal Slurm node health check (HealthCheckProgram). Runs as root on the compute node.
# Each check prints "OK name" or "FAIL name: reason"; any FAIL drains the node (unless DRY_RUN=1).
# Tunables via environment so the script can be tested with stub commands:
#   EXPECT_GPUS (default 8)  MIN_TMP_MB (default 20480)  REQUIRED_MOUNTS ("/scratch /home")  DRY_RUN=1
set -u
EXPECT_GPUS=${EXPECT_GPUS:-8}
MIN_TMP_MB=${MIN_TMP_MB:-20480}
REQUIRED_MOUNTS=${REQUIRED_MOUNTS:-"/scratch /home"}
NODE=${NODE:-$(hostname -s)}
fails=()

check() { # check NAME "command" -> records failure text from command's stdout when it returns non-zero
  local name=$1; shift
  local out
  if out=$("$@" 2>&1); then echo "OK   $name"; else echo "FAIL $name: $out"; fails+=("$name: $out"); fi
}

gpu_count()   { n=$(nvidia-smi -L | grep -c '^GPU'); [ "$n" -eq "$EXPECT_GPUS" ] || { echo "found $n GPUs, expected $EXPECT_GPUS"; return 1; }; }
gpu_errors()  { dmesg 2>/dev/null | grep -E 'NVRM: Xid \((PCI:[0-9a-f:.]+)\): (48|63|64|74|79|94|95)' | tail -3 | grep . && return 1 || return 0; }
tmp_space()   { free=$(df -Pm /tmp | awk 'NR==2{print $4}'); [ "$free" -ge "$MIN_TMP_MB" ] || { echo "only ${free} MB free in /tmp"; return 1; }; }
mounts_ok()   { for m in $REQUIRED_MOUNTS; do mountpoint -q "$m" || { echo "$m not mounted"; return 1; }; done; }
time_sync()   { chronyc tracking 2>/dev/null | awk '/Leap status/{s=$4} END{exit (s=="Normal")?0:1}' || { echo "clock not synchronised"; return 1; }; }
ib_links()    { bad=$(ibstat 2>/dev/null | grep -c 'State: Down'); [ "$bad" -eq 0 ] || { echo "$bad IB ports down"; return 1; }; }

check gpu_count   gpu_count
check gpu_xid     gpu_errors
check tmp_space   tmp_space
check mounts      mounts_ok
check time_sync   time_sync
check ib_links    ib_links

if [ ${#fails[@]} -gt 0 ]; then
  reason="health: $(printf '%s; ' "${fails[@]}" | cut -c1-200)"
  if [ "${DRY_RUN:-0}" = 1 ]; then echo "DRY_RUN would drain $NODE: $reason"; else scontrol update NodeName="$NODE" State=drain Reason="$reason"; fi
  exit 1
fi
exit 0
