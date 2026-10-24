#!/usr/bin/env python3
"""Generate slurm.conf, gres.conf and cgroup.conf for a small GPU cluster from a hardware inventory.

CSV columns: name,sockets,cores_per_socket,threads_per_core,mem_mb,gpus,gpu_type,partition
Nodes with identical hardware are folded into one NodeName line with a hostlist (gpu[001-004]).
Usage: gen_slurm_conf.py inventory.csv OUTDIR [--cluster mycluster] [--ctl ctl1] [--db db1]
"""
import argparse
import csv
import os
import re
from itertools import groupby


def fold(names):
    """['gpu001','gpu002','gpu004'] -> 'gpu[001-002,004]' (names must share prefix and width)."""
    m = [re.fullmatch(r"([a-z-]+)(\d+)", n) for n in names]
    prefix, width = m[0].group(1), len(m[0].group(2))
    nums = sorted(int(x.group(2)) for x in m)
    ranges, start, prev = [], nums[0], nums[0]
    for n in nums[1:] + [None]:
        if n is not None and n == prev + 1:
            prev = n
            continue
        ranges.append(f"{start:0{width}d}" if start == prev else f"{start:0{width}d}-{prev:0{width}d}")
        if n is not None:
            start = prev = n
    return f"{prefix}[{','.join(ranges)}]" if len(nums) > 1 else names[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("outdir")
    ap.add_argument("--cluster", default="mycluster")
    ap.add_argument("--ctl", default="ctl1")
    ap.add_argument("--db", default="db1")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv)))
    key = lambda r: (r["sockets"], r["cores_per_socket"], r["threads_per_core"], r["mem_mb"], r["gpus"], r["gpu_type"])
    node_lines, parts = [], {}
    for k, grp in groupby(sorted(rows, key=key), key=key):
        grp = list(grp)
        s, c, t, mem, g, gt = k
        cpus = int(s) * int(c) * int(t)
        real_mem = int(int(mem) * 0.97)                # leave a little below detected memory (slurmd -C shows exact value)
        line = f"NodeName={fold([r['name'] for r in grp])} CPUs={cpus} Sockets={s} CoresPerSocket={c} ThreadsPerCore={t} RealMemory={real_mem}"
        if int(g):
            line += f" Gres=gpu:{gt}:{g}"
        node_lines.append(line + " State=UNKNOWN")
        for r in grp:
            parts.setdefault(r["partition"], []).append(r["name"])
    gpu = any(int(r["gpus"]) for r in rows)
    conf = [f"ClusterName={a.cluster}", f"SlurmctldHost={a.ctl}", "SlurmUser=slurm", "AuthType=auth/munge",
            "StateSaveLocation=/var/spool/slurmctld", "SlurmdSpoolDir=/var/spool/slurmd",
            "SchedulerType=sched/backfill", "SelectType=select/cons_tres", "SelectTypeParameters=CR_Core_Memory",
            "ProctrackType=proctrack/cgroup", "TaskPlugin=task/affinity,task/cgroup", "JobAcctGatherType=jobacct_gather/cgroup",
            "PriorityType=priority/multifactor", "PriorityWeightFairshare=100000", "PriorityWeightAge=1000",
            f"AccountingStorageType=accounting_storage/slurmdbd", f"AccountingStorageHost={a.db}",
            "AccountingStorageEnforce=associations,limits,qos", "ReturnToService=1", "SlurmdTimeout=300",
            "HealthCheckProgram=/usr/local/sbin/node_health.sh", "HealthCheckInterval=300", "HealthCheckNodeState=ANY,CYCLE",
            "MaxJobCount=50000", "MinJobAge=300"]
    if gpu:
        conf += ["GresTypes=gpu", "AccountingStorageTRES=gres/gpu"]
    conf += node_lines
    gpu_parts = {r["partition"] for r in rows if int(r["gpus"])}
    default = sorted(gpu_parts)[0] if gpu_parts else sorted(parts)[0]
    for p, names in sorted(parts.items()):
        extra = " MaxTime=2-00:00:00"
        if p == default:
            extra = " Default=YES" + extra
        if p in gpu_parts:
            extra += " DefMemPerGPU=65536 DefCpuPerGPU=8"
        conf.append(f"PartitionName={p} Nodes={fold(names)}{extra} State=UP")
    os.makedirs(a.outdir, exist_ok=True)
    open(os.path.join(a.outdir, "slurm.conf"), "w").write("\n".join(conf) + "\n")
    open(os.path.join(a.outdir, "cgroup.conf"), "w").write("CgroupPlugin=autodetect\nConstrainCores=yes\nConstrainRAMSpace=yes\nConstrainDevices=yes\n")
    if gpu:
        open(os.path.join(a.outdir, "gres.conf"), "w").write("AutoDetect=nvml\n")
    print(f"wrote slurm.conf ({len(node_lines)} node groups, {len(parts)} partitions), cgroup.conf" + (", gres.conf" if gpu else ""))


if __name__ == "__main__":
    main()
