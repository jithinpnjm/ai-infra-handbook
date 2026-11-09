# code/part20/c20_autoscale_sim.py
"""Autoscaler simulator for an LLM-engine fleet. A TOY MODEL, not vLLM and not Kubernetes.

It replays a traffic trace second by second. Replicas take a cold-start delay before they serve.
The scaling controller copies the HPA rules from the Kubernetes docs: the ratio formula, the 0.1
tolerance, a 15 second sync period, a scale-down stabilization window, and the rule that
not-yet-ready pods count as 0 percent of target when scaling up.
Every number in DEFAULTS is an assumption for teaching, not a measurement of any real system.
Standard library only.
"""
import argparse
import json
import math
import random
from collections import deque
from dataclasses import dataclass, field

DEFAULTS = {
    "slots": 16,               # concurrent sequences one replica serves
    "service_s": 20,           # seconds one streamed request holds a slot
    "util_saturation": 0.25,   # fraction of slots in use at which the GPU already looks 100 percent busy
    "node_provision_s": 240,   # assumed: new GPU node joins the cluster
    "image_pull_s": 90,        # assumed: pull a large serving image onto a fresh node
    "weight_load_s": 120,      # assumed: read weights from storage into GPU memory
    "warmup_s": 30,            # assumed: first requests, graph capture, caches
    "sync_s": 15,              # HPA default sync period
    "grace_s": 120,            # terminationGracePeriodSeconds for a draining replica
}


def hpa_desired(current, metric, target, tolerance=0.1):
    """The documented HPA ratio rule. Returns current when the ratio is inside the tolerance."""
    ratio = metric / target
    if abs(ratio - 1.0) <= tolerance:
        return current
    return math.ceil(current * ratio)


def cold_start_s(p, has_node):
    """Seconds from the scale decision until a replica serves. A spare node skips two steps."""
    base = p["weight_load_s"] + p["warmup_s"]
    return base if has_node else base + p["node_provision_s"] + p["image_pull_s"]


def lead_time_headroom(ramp_rps_per_min, cold_s, per_replica_rps):
    """Replicas of spare capacity that cover demand growth during one cold start."""
    growth = ramp_rps_per_min * (cold_s / 60.0)
    return math.ceil(growth / per_replica_rps)


def make_trace(kind="burst", seconds=3600, seed=7):
    """Arrivals per second as floats. Deterministic for a given seed."""
    rnd = random.Random(seed)
    out = []
    for t in range(seconds):
        if kind == "steady":
            rate = 1.2
        elif kind == "burst":      # base 1.2 rps, a 5x burst from minute 10 to minute 25
            rate = 6.0 if 600 <= t < 1500 else 1.2
        elif kind == "ramp":       # climbs from 1.2 to 7.2 rps over 30 minutes, then falls
            rate = 1.2 + min(t, 1800) / 1800 * 6.0 if t < 2400 else 1.2
        elif kind == "sawtooth":   # short bursts every 6 minutes, the flapping test
            rate = 4.0 if (t % 360) < 90 else 1.2
        else:
            raise ValueError(kind)
        out.append(max(0.0, rate * (0.9 + 0.2 * rnd.random())))
    return out


@dataclass
class Replica:
    ready_at: int
    running: list = field(default_factory=list)   # remaining seconds per request
    draining: bool = False
    drain_started: int = -1


class Fleet:
    def __init__(self, p, replicas, spare_nodes=0, drain=True):
        self.p, self.drain, self.spare_target = p, drain, spare_nodes
        self.spare = spare_nodes
        self.refills = []                       # times when a spare node is back
        self.reps = [Replica(ready_at=0) for _ in range(replicas)]
        self.queue = deque()
        self.waits, self.dropped = [], 0
        self.replica_s = 0.0
        self.spare_s = 0.0
        self.starting_events = 0

    def ready(self, t):
        return [r for r in self.reps if r.ready_at <= t and not r.draining]

    def starting(self, t):
        return [r for r in self.reps if r.ready_at > t]

    def scale_to(self, t, desired):
        live = [r for r in self.reps if not r.draining]
        while len(live) < desired:
            use_spare = self.spare > 0
            if use_spare:
                self.spare -= 1
                self.refills.append(t + self.p["node_provision_s"] + self.p["image_pull_s"])
            rep = Replica(ready_at=t + cold_start_s(self.p, use_spare))
            self.reps.append(rep)
            live.append(rep)
            self.starting_events += 1
        if len(live) > desired:
            # remove the replicas that still start first, then the least busy
            order = sorted(live, key=lambda r: (r.ready_at <= t, len(r.running)))
            for r in order[: len(live) - desired]:
                self._stop(t, r)

    def _stop(self, t, r):
        if r.ready_at > t or not r.running:
            self.reps.remove(r)
        elif self.drain:
            r.draining, r.drain_started = True, t
        else:
            self.dropped += len(r.running)
            self.reps.remove(r)

    def step(self, t, arrivals):
        for _ in range(int(arrivals)):
            self.queue.append(t)
        frac = arrivals - int(arrivals)
        if frac and random.Random(t).random() < frac:
            self.queue.append(t)
        for rd in [x for x in self.refills if x <= t]:
            self.refills.remove(rd)
            self.spare = min(self.spare_target, self.spare + 1)
        slots = self.p["slots"]
        ready = self.ready(t)
        while self.queue and ready:   # least-loaded routing, like a load-aware router
            r = min(ready, key=lambda x: len(x.running))
            if len(r.running) >= slots:
                break
            self.waits.append(t - self.queue.popleft())
            r.running.append(self.p["service_s"])
        for r in list(self.reps):
            r.running = [x - 1 for x in r.running if x - 1 > 0]
            if r.draining and (not r.running or t - r.drain_started >= self.p["grace_s"]):
                self.dropped += len(r.running)
                self.reps.remove(r)
        self.replica_s += len(self.reps)
        self.spare_s += self.spare

    def snapshot(self, t):
        rd, st = self.ready(t), self.starting(t)
        sat = self.p["slots"] * self.p["util_saturation"]
        return {
            "waiting": len(self.queue),
            "running": sum(len(r.running) for r in rd),
            "ready": len(rd),
            "starting": len(st),
            "util": [min(1.0, len(r.running) / sat) for r in rd],
        }


def metric_util(snap):
    return sum(snap["util"]) / max(1, snap["ready"])


def metric_queue(snap):
    return snap["waiting"]


def metric_inflight(snap):
    return snap["running"] + snap["waiting"]


POLICIES = {
    # name: (metric function, target per replica, scale on a per-pod average)
    "util": (metric_util, 0.7),
    "queue": (metric_queue, 2.0),
    "inflight": (metric_inflight, None),   # target set from slots below, 70 percent of slots
}


class Hpa:
    """HPA-style controller. Ratio rule, tolerance, scale-up policy, scale-down policy and window."""

    def __init__(self, policy, p, min_r=3, max_r=16, down_window_s=300, down_pct_per_period=100,
                 up_pods=4, up_pct=100):
        self.name, self.p = policy, p
        self.fn, tgt = POLICIES[policy]
        self.target = tgt if tgt is not None else 0.7 * p["slots"]
        self.min_r, self.max_r = min_r, max_r
        self.down_window_s, self.down_pct = down_window_s, down_pct_per_period
        self.up_pods, self.up_pct = up_pods, up_pct
        self.recs = deque()           # (time, recommendation) for the stabilization window
        self.last_dir = 0
        self.flips = 0
        self.history = []

    def avg_metric(self, snap, scaling_up):
        """Per-pod average. Not-ready pods count as 0 percent of target when scaling up."""
        raw = self.fn(snap)
        if self.name == "util":
            ready_avg = raw
            n = snap["ready"] + snap["starting"] if scaling_up else snap["ready"]
            return ready_avg * snap["ready"] / max(1, n)
        n = snap["ready"] + snap["starting"] if scaling_up else max(1, snap["ready"])
        return raw / max(1, n)

    def decide(self, t, snap, current):
        up = self.avg_metric(snap, True)
        rec = hpa_desired(current, up, self.target)
        if rec <= current:
            rec = hpa_desired(current, self.avg_metric(snap, False), self.target)
        rec = max(self.min_r, min(self.max_r, rec))
        self.recs.append((t, rec))
        while self.recs and self.recs[0][0] < t - self.down_window_s:
            self.recs.popleft()
        if rec > current:
            step = max(self.up_pods, math.ceil(current * self.up_pct / 100))
            new = min(rec, current + step)
        elif rec < current:
            stable = max(r for _, r in self.recs)     # highest recommendation in the window
            new = min(current, stable)
            per = max(1, math.ceil(current * self.down_pct / 100))
            new = max(new, current - per)
        else:
            new = current
        new = max(self.min_r, min(self.max_r, new))
        d = (new > current) - (new < current)
        if d and self.last_dir and d != self.last_dir:
            self.flips += 1
        if d:
            self.last_dir = d
        self.history.append((t, current, new))
        return new


def percentile(xs, q):
    if not xs:
        return 0.0
    s = sorted(xs)
    return float(s[min(len(s) - 1, math.ceil(q * len(s)) - 1)])


def run(trace, policy=None, static_replicas=None, p=None, spare_nodes=0, min_r=3, max_r=16,
        down_window_s=300, down_pct=100, drain=True, slo_wait_s=5):
    p = dict(DEFAULTS, **(p or {}))
    start = static_replicas if policy is None else min_r
    fleet = Fleet(p, start, spare_nodes, drain)
    hpa = None if policy is None else Hpa(policy, p, min_r, max_r, down_window_s, down_pct)
    peak_q = 0
    for t, a in enumerate(trace):
        if hpa and t % p["sync_s"] == 0 and t > 0:
            snap = fleet.snapshot(t)
            cur = len([r for r in fleet.reps if not r.draining])
            fleet.scale_to(t, hpa.decide(t, snap, cur))
        fleet.step(t, a)
        peak_q = max(peak_q, len(fleet.queue))
    waits = fleet.waits + [len(trace) - 1 - w for w in fleet.queue]
    total = max(1, len(waits))
    return {
        "policy": policy or "static",
        "spare_nodes": spare_nodes,
        "served": len(fleet.waits),
        "wait_p50_s": percentile(waits, 0.50),
        "wait_p99_s": percentile(waits, 0.99),
        "wait_max_s": max(waits) if waits else 0,
        "slo_violation_pct": round(100.0 * sum(1 for w in waits if w > slo_wait_s) / total, 1),
        "peak_queue": peak_q,
        "gpu_hours": round((fleet.replica_s + fleet.spare_s) / 3600.0, 2),
        "final_replicas": len([r for r in fleet.reps if not r.draining]),
        "replica_starts": fleet.starting_events,
        "direction_flips": hpa.flips if hpa else 0,
        "dropped_streams": fleet.dropped,
    }


def compare(kind="burst", **kw):
    trace = make_trace(kind)
    rows = [run(trace, None, static_replicas=3, **kw)]
    for pol in ("util", "queue", "inflight"):
        rows.append(run(trace, pol, **kw))
    return rows


def format_table(rows):
    cols = ["policy", "spare_nodes", "wait_p50_s", "wait_p99_s", "slo_violation_pct",
            "peak_queue", "gpu_hours", "final_replicas", "replica_starts", "direction_flips", "dropped_streams"]
    out = ["  ".join(f"{c:>17}" for c in cols)]
    for r in rows:
        out.append("  ".join(f"{str(r[c]):>17}" for c in cols))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trace", default="burst", choices=["steady", "burst", "ramp", "sawtooth"])
    ap.add_argument("--spare-nodes", type=int, default=0)
    ap.add_argument("--min-replicas", type=int, default=3)
    ap.add_argument("--down-window", type=int, default=300)
    ap.add_argument("--no-drain", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    rows = compare(a.trace, spare_nodes=a.spare_nodes, min_r=a.min_replicas, down_window_s=a.down_window,
                   drain=not a.no_drain)
    print(json.dumps(rows, indent=2) if a.json else format_table(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
