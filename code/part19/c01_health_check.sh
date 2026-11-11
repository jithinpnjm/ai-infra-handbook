#!/bin/bash
# /etc/slurm/health_check.sh - runs on compute nodes
HOST=$(hostname)

if ! pgrep -x slurmd >/dev/null; then
    scontrol update NodeName="$HOST" State=drain Reason="slurmd not running"
    exit 1
fi

if dmesg 2>/dev/null | grep -qi "xid"; then
    scontrol update NodeName="$HOST" State=drain Reason="Xid event in dmesg"
    exit 1
fi

if ! nvidia-smi -q -d ECC 2>/dev/null | grep -q "No ECC errors detected"; then
    scontrol update NodeName="$HOST" State=drain Reason="ECC errors detected"
    exit 1
fi

exit 0
