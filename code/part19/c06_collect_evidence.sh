#!/usr/bin/env bash
# Collect the evidence bundle for a hardware ticket on a cordoned node (chapter 19.6).
# Not run here: needs an NVIDIA driver and DCGM. Run it before any GPU reset or reboot,
# because a reset can erase the state you want to show the vendor.
# Usage: sudo ./c06_collect_evidence.sh <node-name> <gpu-index>
set -uo pipefail

NODE="$1"
GPU="$2"
OUT="evidence-${NODE}-gpu${GPU}-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "${OUT}"

# Kernel log lines that carry an Xid, oldest first.
journalctl -k --since "-30 days" --no-pager | grep "NVRM: Xid" > "${OUT}/xid-history.log" || true
dmesg -T > "${OUT}/dmesg.log" || true
lspci -nn > "${OUT}/lspci.log" || true
nvidia-smi -q -i "${GPU}" > "${OUT}/nvidia-smi-q.log" || true
dcgmi health -c > "${OUT}/dcgmi-health.log" || true
# The diagnostic is invasive: only run it on a node that is already drained.
dcgmi diag -r 3 -j > "${OUT}/dcgmi-diag-r3.json" || echo "dcgmi diag exit code $?" > "${OUT}/dcgmi-diag-exit.txt"
# NVIDIA's bug-report script writes nvidia-bug-report.log.gz in the current directory.
nvidia-bug-report.sh > "${OUT}/bug-report-stdout.log" 2>&1 || true
mv nvidia-bug-report.log.gz "${OUT}/" 2>/dev/null || true

tar czf "${OUT}.tar.gz" "${OUT}"
echo "wrote ${OUT}.tar.gz"
