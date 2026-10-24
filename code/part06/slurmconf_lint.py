#!/usr/bin/env python3
"""Small slurm.conf sanity checker (not a replacement for slurmctld's own parser).

Checks: node CPU arithmetic, partitions referencing undefined nodes, exactly one Default partition,
overlapping NodeName definitions, GresTypes vs Gres, and the cgroup-related settings that most often
get forgotten. Hostlist expansion supports simple forms such as gpu[01-04,07] and name[1-3].
"""
import re
import sys


def expand(expr):
    out = []
    for part in re.findall(r"[^,\[]+(?:\[[^\]]*\])?[^,\[]*", expr):
        m = re.match(r"^(.*?)\[([^\]]+)\](.*)$", part)
        if not m:
            out.append(part)
            continue
        pre, body, post = m.groups()
        for item in body.split(","):
            if "-" in item:
                a, b = item.split("-")
                w = len(a)
                out += [f"{pre}{i:0{w}d}{post}" for i in range(int(a), int(b) + 1)]
            else:
                out.append(f"{pre}{item}{post}")
    return out


def parse(path):
    kv, nodes, parts = {}, [], []
    for raw in open(path):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        fields = dict(f.split("=", 1) for f in line.split() if "=" in f)
        if "NodeName" in fields:
            nodes.append(fields)
        elif "PartitionName" in fields:
            parts.append(fields)
        else:
            kv.update(fields)
    return kv, nodes, parts


def lint(path):
    kv, nodes, parts = parse(path)
    problems, warns = [], []
    defined = {}
    defaults = {}
    for n in nodes:
        if n["NodeName"] == "DEFAULT":
            defaults.update({k: v for k, v in n.items() if k != "NodeName"})
            continue
        merged = {**defaults, **n}
        for name in expand(n["NodeName"]):
            if name in defined:
                problems.append(f"node {name} defined more than once")
            defined[name] = merged
        s = int(merged.get("Sockets", merged.get("SocketsPerBoard", 1)))
        c = int(merged.get("CoresPerSocket", 1))
        t = int(merged.get("ThreadsPerCore", 1))
        if "CPUs" in merged and ("CoresPerSocket" in merged or "Sockets" in merged):
            if int(merged["CPUs"]) != s * c * t:
                problems.append(f"{n['NodeName']}: CPUs={merged['CPUs']} but Sockets*CoresPerSocket*ThreadsPerCore={s*c*t}")
        if "CPUs" not in merged and "CoresPerSocket" not in merged:
            warns.append(f"{n['NodeName']}: no CPU topology; scheduling and binding will be crude")
        if "RealMemory" not in merged:
            warns.append(f"{n['NodeName']}: RealMemory not set (defaults to 1 MB; memory limits will not work)")
        if "Gres" in merged and "gres/" not in "".join(kv.get("GresTypes", "")) and merged["Gres"].split(":")[0] not in kv.get("GresTypes", ""):
            problems.append(f"{n['NodeName']}: Gres={merged['Gres']} but GresTypes does not list {merged['Gres'].split(':')[0]}")
    n_default = 0
    for p in parts:
        if p["PartitionName"] == "DEFAULT":
            continue
        if p.get("Default", "NO").upper() in ("YES", "TRUE"):
            n_default += 1
        for name in expand(p.get("Nodes", "")) if p.get("Nodes") not in (None, "ALL") else []:
            if name not in defined:
                problems.append(f"partition {p['PartitionName']}: node {name} is not defined")
    if parts and n_default != 1:
        problems.append(f"{n_default} partitions marked Default=YES (expected exactly 1)")
    sel = kv.get("SelectTypeParameters", "")
    if "Memory" not in sel:
        warns.append("SelectTypeParameters has no *_Memory: memory is not a consumable resource, ConstrainRAMSpace has no effect")
    if "cgroup" not in kv.get("TaskPlugin", "") or "cgroup" not in kv.get("ProctrackType", ""):
        warns.append("TaskPlugin/ProctrackType do not both use cgroup: job cleanup and containment will be weak")
    if kv.get("ReturnToService") == "2":
        warns.append("ReturnToService=2 returns any DOWN node automatically when it registers; make sure a health check gates this")
    return problems, warns


if __name__ == "__main__":
    bad = False
    for f in sys.argv[1:]:
        problems, warns = lint(f)
        print(f"== {f}")
        for p in problems:
            print("ERROR:", p)
        for w in warns:
            print("warn: ", w)
        if not problems and not warns:
            print("no findings")
        bad |= bool(problems)
    sys.exit(1 if bad else 0)
