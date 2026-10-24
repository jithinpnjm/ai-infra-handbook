#!/usr/bin/env python3
"""Minimal Prometheus exporter for Slurm node and job state (illustrative; production sites use a maintained exporter).

Collects from the CLI:
  sinfo -h -N -O "NodeList:32,StateLong:20,Gres:40,GresUsed:60,Reason:80,Partition:24"   (fixed-width columns)
  squeue -h -o "%T|%P|%u|%D"
Metrics: slurm_nodes{state}, slurm_node_drain_reason{reason_class}, slurm_gpus{state=total|allocated},
         slurm_jobs{state,partition}, slurm_exporter_scrape_ok.
Run `slurm_exporter.py --selftest` to execute the parser tests with canned command output (no Slurm needed),
or `slurm_exporter.py --port 9341` to serve /metrics.
"""
import re
import subprocess
import sys
from collections import Counter

from prometheus_client import CollectorRegistry, Gauge, generate_latest, start_http_server

WIDTHS = [32, 20, 40, 60, 80, 24]
SINFO = ["sinfo", "-h", "-N", "-O", ",".join(f"{n}:{w}" for n, w in zip(["NodeList", "StateLong", "Gres", "GresUsed", "Reason", "Partition"], WIDTHS))]
SQUEUE = ["squeue", "-h", "-o", "%T|%P|%u|%D"]


def split_fixed(line):
    out, pos = [], 0
    for w in WIDTHS:
        out.append(line[pos:pos + w].strip())
        pos += w
    return out


def gpu_count(spec):
    m = re.search(r"gpu(?::[^:(,]+)?:(\d+)", spec or "")
    return int(m.group(1)) if m else 0


def reason_class(reason):
    r = (reason or "").lower()
    for key, cls in (("xid", "gpu"), ("gpu", "gpu"), ("ecc", "memory"), ("ib", "network"), ("nccl", "network"), ("mount", "storage"),
                     ("nfs", "storage"), ("lustre", "storage"), ("prolog", "prolog"), ("not responding", "unresponsive"),
                     ("kill task failed", "unkillable"), ("health", "health"), ("maint", "maintenance")):
        if key in r:
            return cls
    return "other" if r else "none"


def parse(sinfo_text, squeue_text):
    nodes, gpus_total, gpus_alloc, reasons, seen = Counter(), 0, 0, Counter(), set()
    for line in sinfo_text.splitlines():
        if not line.strip():
            continue
        name, state, gres, used, reason, _part = split_fixed(line)
        if name in seen:                      # a node in several partitions appears several times
            continue
        seen.add(name)
        nodes[state.lower().rstrip("*~#$@+")] += 1
        gpus_total += gpu_count(gres)
        gpus_alloc += gpu_count(used)
        if state.lower().startswith(("drain", "down", "fail")):
            reasons[reason_class(reason)] += 1
    jobs = Counter()
    for line in squeue_text.splitlines():
        if line.strip():
            st, part, _user, _nodes = line.split("|")
            jobs[(st.lower(), part)] += 1
    return nodes, gpus_total, gpus_alloc, reasons, jobs


def render(sinfo_text, squeue_text, ok=1):
    reg = CollectorRegistry()
    nodes, gt, ga, reasons, jobs = parse(sinfo_text, squeue_text)
    g = Gauge("slurm_nodes", "Nodes by state", ["state"], registry=reg)
    for s, n in nodes.items():
        g.labels(s).set(n)
    d = Gauge("slurm_node_drain_reason", "Drained/down nodes by reason class", ["reason_class"], registry=reg)
    for s, n in reasons.items():
        d.labels(s).set(n)
    gg = Gauge("slurm_gpus", "GPUs by status", ["status"], registry=reg)
    gg.labels("total").set(gt)
    gg.labels("allocated").set(ga)
    j = Gauge("slurm_jobs", "Jobs by state and partition", ["state", "partition"], registry=reg)
    for (s, p), n in jobs.items():
        j.labels(s, p).set(n)
    Gauge("slurm_exporter_scrape_ok", "1 if the last collection worked", registry=reg).set(ok)
    return generate_latest(reg).decode()


def collect():
    return render(subprocess.run(SINFO, capture_output=True, text=True, check=True).stdout,
                  subprocess.run(SQUEUE, capture_output=True, text=True, check=True).stdout)


def row(name, state, gres, used, reason, part):
    return "".join(str(v).ljust(w) for v, w in zip([name, state, gres, used, reason, part], WIDTHS))


def selftest():
    sinfo = "\n".join([
        row("gpu001", "allocated", "gpu:h100:8(S:0-1)", "gpu:h100:8(IDX:0-7)", "none", "gpu"),
        row("gpu002", "mixed", "gpu:h100:8(S:0-1)", "gpu:h100:3(IDX:0-2)", "none", "gpu"),
        row("gpu002", "mixed", "gpu:h100:8(S:0-1)", "gpu:h100:3(IDX:0-2)", "none", "debug"),
        row("gpu003", "drained", "gpu:h100:8(S:0-1)", "gpu:h100:0(IDX:N/A)", "health: gpu_xid: Xid 79 fell off bus", "gpu"),
        row("gpu004", "down*", "gpu:h100:8(S:0-1)", "gpu:h100:0(IDX:N/A)", "Not responding", "gpu"),
        row("gpu005", "idle", "gpu:h100:8(S:0-1)", "gpu:h100:0(IDX:N/A)", "none", "gpu"),
    ])
    squeue = "RUNNING|gpu|alice|4\nPENDING|gpu|bob|8\nPENDING|gpu|carol|1\nRUNNING|debug|dave|1\n"
    text = render(sinfo, squeue)
    nodes, gt, ga, reasons, jobs = parse(sinfo, squeue)
    assert nodes == {"allocated": 1, "mixed": 1, "drained": 1, "down": 1, "idle": 1}, nodes     # gpu002 counted once
    assert (gt, ga) == (40, 11), (gt, ga)
    assert reasons == {"gpu": 1, "unresponsive": 1}, reasons
    assert jobs[("pending", "gpu")] == 2 and jobs[("running", "debug")] == 1
    assert 'slurm_gpus{status="allocated"} 11.0' in text
    return text


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        print(selftest())
        print("selftest passed")
    else:
        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 9341
        start_http_server(port)
        import time
        while True:
            time.sleep(3600)
