# code/part19/c04_checkpoint_interval.py
"""Checkpoint interval calculator (Young / Daly) with a waste model.

All times are in seconds. Definitions used throughout:
    mtbf   M  mean time between interruptions of the whole job
    cost   C  time the job is blocked while one checkpoint is written
    tau       compute time between the end of one checkpoint and the start of the next

Formulas:
    young:  tau = sqrt(2*C*M)                                  (Young 1974)
    daly:   tau = sqrt(2*C*M) - C   if C < M/2, else tau = M   (Daly 2004, as summarised
            by A. Colyer; the paper's full higher-order series is not reproduced here)

Waste model (Aupy et al., arXiv 1302.3752, Section 3), with T = tau + C the full period:
    waste_ff    = C / T
    waste_fault = (D + R + T/2) / M        D = downtime, R = recovery/restart time
    waste       = 1 - (1 - waste_ff) * (1 - waste_fault)
"""
import argparse
import math


def cluster_mtbf(node_mtbf_s, nodes):
    """MTBF of a job that dies when any one node dies.

    Assumes independent nodes with exponential failures, so failure rates add.
    This is a modelling assumption; measure the real job MTBF from your logs.
    """
    if nodes < 1:
        raise ValueError("nodes must be >= 1")
    return node_mtbf_s / nodes


def young(cost, mtbf):
    return math.sqrt(2.0 * cost * mtbf)


def daly(cost, mtbf):
    if cost >= mtbf / 2.0:
        return mtbf
    return math.sqrt(2.0 * cost * mtbf) - cost


def waste(tau, cost, mtbf, downtime=0.0, restart=0.0):
    t = tau + cost
    w_ff = cost / t
    w_fault = min(1.0, (downtime + restart + t / 2.0) / mtbf)
    return 1.0 - (1.0 - w_ff) * (1.0 - w_fault)


def numeric_optimum(cost, mtbf, downtime=0.0, restart=0.0):
    """Golden-section search for the tau that minimises waste()."""
    lo, hi = 1e-3 * cost + 1e-9, 4.0 * mtbf
    g = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    c, d = b - g * (b - a), a + g * (b - a)
    for _ in range(200):
        if waste(c, cost, mtbf, downtime, restart) < waste(d, cost, mtbf, downtime, restart):
            b = d
        else:
            a = c
        c, d = b - g * (b - a), a + g * (b - a)
    return (a + b) / 2.0


def write_seconds(checkpoint_gb, aggregate_gb_per_s):
    """Blocking time of a synchronous write: size over aggregate bandwidth."""
    return checkpoint_gb / aggregate_gb_per_s


def report(cost, mtbf, downtime=0.0, restart=0.0, label=""):
    ty, td = young(cost, mtbf), daly(cost, mtbf)
    tn = numeric_optimum(cost, mtbf, downtime, restart)
    return {
        "label": label,
        "mtbf_s": mtbf,
        "cost_s": cost,
        "young_s": ty,
        "daly_s": td,
        "numeric_opt_s": tn,
        "waste_at_daly": waste(td, cost, mtbf, downtime, restart),
        "waste_at_numeric": waste(tn, cost, mtbf, downtime, restart),
        "waste_every_5min": waste(300.0, cost, mtbf, downtime, restart),
        "waste_every_4h": waste(14400.0, cost, mtbf, downtime, restart),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mtbf-hours", type=float, help="job MTBF in hours")
    ap.add_argument("--node-mtbf-hours", type=float, help="per-node MTBF in hours")
    ap.add_argument("--nodes", type=int, default=1)
    ap.add_argument("--cost-seconds", type=float, help="blocking checkpoint time")
    ap.add_argument("--checkpoint-gb", type=float)
    ap.add_argument("--write-gb-per-s", type=float)
    ap.add_argument("--downtime-seconds", type=float, default=0.0)
    ap.add_argument("--restart-seconds", type=float, default=0.0)
    a = ap.parse_args()
    if a.mtbf_hours is not None:
        mtbf = a.mtbf_hours * 3600.0
    elif a.node_mtbf_hours is not None:
        mtbf = cluster_mtbf(a.node_mtbf_hours * 3600.0, a.nodes)
    else:
        ap.error("give --mtbf-hours or --node-mtbf-hours")
    if a.cost_seconds is not None:
        cost = a.cost_seconds
    elif a.checkpoint_gb is not None and a.write_gb_per_s:
        cost = write_seconds(a.checkpoint_gb, a.write_gb_per_s)
    else:
        ap.error("give --cost-seconds or --checkpoint-gb with --write-gb-per-s")
    r = report(cost, mtbf, a.downtime_seconds, a.restart_seconds)
    for k, v in r.items():
        if k == "label":
            continue
        print(f"{k:18s} {v:.4f}" if isinstance(v, float) else f"{k:18s} {v}")


if __name__ == "__main__":
    main()
