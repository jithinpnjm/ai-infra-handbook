# code/part19/c04_straggler_detector.py
"""Straggler and stall detector from per-rank step-time records.

Input is a CSV with the columns: ts,step,rank,host,data_s,compute_s
    data_s     time the rank waited for its next batch
    compute_s  time from batch ready to just before the gradient collective starts

Why two columns and not one step time: in synchronous training every rank
leaves the collective together, so the full step time is almost the same on
every rank. The slow rank shows up in the time it spends before the
collective (its own compute) or waiting for data. This is reasoning, not a
measurement from a vendor source; the thresholds below are starting points to
tune against your own healthy baseline.

Verdicts:
    straggler_rank   one rank is slow in at least `persist` of the last `window` steps
    straggler_host   at least half of one host's ranks are flagged
    global_slowdown  the median of all ranks moved up against the early baseline
    stalled          no new record for `stale_s` seconds
A single spike is not flagged. A global slowdown is not blamed on one rank.
"""
import argparse
import csv
import random
import statistics
import sys
import time
from collections import defaultdict

FIELDS = ["ts", "step", "rank", "host", "data_s", "compute_s"]


def load(path):
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "ts": float(r["ts"]), "step": int(r["step"]), "rank": int(r["rank"]),
                "host": r["host"], "data_s": float(r["data_s"]), "compute_s": float(r["compute_s"]),
            })
    return rows


def _by_step(rows):
    d = defaultdict(list)
    for r in rows:
        d[r["step"]].append(r)
    return d


def analyze(rows, window=20, ratio=1.15, persist=0.8, global_ratio=1.3, baseline_steps=20,
            data_floor_s=0.05):
    """Return a dict with the verdicts. ratio is rank value over the per-step median."""
    steps = _by_step(rows)
    ordered = sorted(steps)
    out = {"straggler_rank": [], "straggler_host": [], "global_slowdown": False, "steps": len(ordered)}
    if len(ordered) < window:
        out["note"] = "not enough steps for a verdict"
        return out
    recent = ordered[-window:]
    slow = defaultdict(lambda: {"compute": 0, "data": 0})
    host_of = {}
    for s in recent:
        recs = steps[s]
        med_c = statistics.median(r["compute_s"] for r in recs)
        med_d = max(statistics.median(r["data_s"] for r in recs), data_floor_s)
        for r in recs:
            host_of[r["rank"]] = r["host"]
            if r["compute_s"] > ratio * med_c:
                slow[r["rank"]]["compute"] += 1
            if r["data_s"] > ratio * med_d and r["data_s"] > data_floor_s:
                slow[r["rank"]]["data"] += 1
    flagged_hosts = defaultdict(set)
    for rank, c in sorted(slow.items()):
        for kind in ("compute", "data"):
            frac = c[kind] / window
            if frac >= persist:
                out["straggler_rank"].append(
                    {"rank": rank, "host": host_of[rank], "kind": kind, "fraction_slow": round(frac, 2)})
                flagged_hosts[host_of[rank]].add(rank)
    ranks_per_host = defaultdict(set)
    for rank, h in host_of.items():
        ranks_per_host[h].add(rank)
    for h, flagged in sorted(flagged_hosts.items()):
        if len(flagged) * 2 >= len(ranks_per_host[h]):
            out["straggler_host"].append(h)
    base = statistics.median(r["compute_s"] for s in ordered[:baseline_steps] for r in steps[s])
    now = statistics.median(r["compute_s"] for s in recent for r in steps[s])
    out["global_slowdown"] = now > global_ratio * base
    out["baseline_compute_s"] = round(base, 4)
    out["recent_compute_s"] = round(now, 4)
    if out["global_slowdown"]:
        # Everyone moved together: not a single-rank problem. Drop per-rank blame.
        out["straggler_rank"] = []
        out["straggler_host"] = []
    return out


def check_stall(rows, now, stale_s):
    last = max(r["ts"] for r in rows) if rows else 0.0
    return {"stalled": (now - last) > stale_s, "seconds_since_last_record": round(now - last, 1)}


def synth(kind, ranks_per_host=8, hosts=4, steps=100, seed=7, t0=1_700_000_000.0):
    """Deterministic synthetic records for the fixtures."""
    rng = random.Random(seed)
    rows = []
    t = t0
    for s in range(steps):
        t += 1.0
        for h in range(hosts):
            for i in range(ranks_per_host):
                rank = h * ranks_per_host + i
                comp = 0.80 * (1 + rng.uniform(-0.02, 0.02))
                data = 0.010 * (1 + rng.uniform(-0.2, 0.2))
                if kind == "slow_gpu" and rank == 19:
                    comp *= 1.35
                if kind == "slow_host" and h == 1:
                    data += 0.40
                if kind == "spike" and rank == 3 and s in (40, 41, 70):
                    comp *= 2.0
                if kind == "global_slowdown" and s >= 50:
                    comp *= 1.5
                rows.append([f"{t:.1f}", s, rank, f"trainer-{h}", f"{data:.4f}", f"{comp:.4f}"])
    return rows


def write_fixtures(outdir):
    import os
    os.makedirs(outdir, exist_ok=True)
    for kind in ("healthy", "slow_gpu", "slow_host", "spike", "global_slowdown"):
        with open(os.path.join(outdir, f"{kind}.csv"), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(FIELDS)
            w.writerows(synth(kind))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--stale-seconds", type=float)
    ap.add_argument("--make-fixtures")
    a = ap.parse_args()
    if a.make_fixtures:
        write_fixtures(a.make_fixtures)
        return 0
    rows = load(a.csv)
    res = analyze(rows)
    code = 0
    if a.stale_seconds is not None:
        st = check_stall(rows, time.time(), a.stale_seconds)
        res.update(st)
        code = 2 if st["stalled"] else code
    print(res)
    if res["straggler_rank"] or res["straggler_host"] or res["global_slowdown"]:
        code = max(code, 1)
    return code


if __name__ == "__main__":
    sys.exit(main())
