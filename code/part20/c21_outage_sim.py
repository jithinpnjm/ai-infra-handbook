"""Discrete-event simulation of a partial outage behind a blind load balancer.

Eight replicas each have a few slots and a short queue. For a window of time
a quarter of the replicas fail fast. Clients retry by a chosen policy. The
point is the shape of the result, not a prediction for any real fleet.

Simplifications, all deliberate:
- the balancer picks a replica uniformly at random and does not eject any;
- service time is fixed, so there is no long-prompt tail;
- a replica finishes work for an attempt that already timed out, which is the
  worst case for engines that do not abort on client disconnect.
Standard library only. The random generator is seeded, so runs repeat.
"""
import heapq
import random
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Policy:
    name: str
    max_attempts: int = 1
    backoff: str = "none"        # none | exp | full
    budget_ratio: float = 0.0    # 0 means no retry budget
    budget_cap: float = 10.0


@dataclass
class Config:
    duration: float = 120.0
    outage: tuple = (30.0, 70.0)
    rate: float = 40.0           # user requests per second
    replicas: int = 8
    failed: int = 2              # replicas that fail fast during the outage
    slots: int = 4
    queue: int = 8
    service_s: float = 0.5
    attempt_timeout_s: float = 2.0
    fail_fast_s: float = 0.02
    reject_s: float = 0.005
    base_backoff_s: float = 0.2
    cap_backoff_s: float = 3.0
    seed: int = 7


def backoff_delay(kind, retry_no, base, cap, rng):
    """Delay before retry number retry_no (1 for the first retry)."""
    if kind == "none":
        return 0.0
    ceiling = min(cap, base * 2 ** (retry_no - 1))
    if kind == "exp":
        return ceiling
    if kind == "full":
        return rng.uniform(0.0, ceiling)
    raise ValueError(f"unknown backoff kind: {kind}")


@dataclass
class _Replica:
    busy: int = 0
    waiting: list = field(default_factory=list)


def simulate(policy, cfg=None):
    cfg = cfg or Config()
    rng = random.Random(cfg.seed)
    reps = [_Replica() for _ in range(cfg.replicas)]
    events, seq = [], 0

    def push(t, kind, data):
        nonlocal seq
        seq += 1
        heapq.heappush(events, (t, seq, kind, data))

    reqs = {}       # req id -> dict(start, attempts, done)
    attempts = {}   # attempt id -> dict(req, resolved, replica)
    tokens = policy.budget_cap
    next_aid = 0
    per_sec = [0] * (int(cfg.duration) + 1)
    wasted, peak_queue = 0, 0

    t = 0.0
    rid = 0
    while True:                       # Poisson arrivals for all user requests
        t += rng.expovariate(cfg.rate)
        if t >= cfg.duration:
            break
        push(t, "arrive", rid)
        reqs[rid] = {"start": t, "attempts": 0, "done": False, "ok": False, "lat": None}
        rid += 1

    def in_outage(now):
        return cfg.outage[0] <= now < cfg.outage[1]

    def launch(now, r):
        nonlocal next_aid, peak_queue
        reqs[r]["attempts"] += 1
        aid = next_aid
        next_aid += 1
        idx = rng.randrange(cfg.replicas)
        attempts[aid] = {"req": r, "resolved": False, "replica": idx}
        per_sec[min(int(now), len(per_sec) - 1)] += 1
        push(now + cfg.attempt_timeout_s, "timeout", aid)
        rep = reps[idx]
        if in_outage(now) and idx < cfg.failed:
            push(now + cfg.fail_fast_s, "error", aid)
        elif rep.busy < cfg.slots:
            rep.busy += 1
            push(now + cfg.service_s, "done", aid)
        elif len(rep.waiting) < cfg.queue:
            rep.waiting.append(aid)
            peak_queue = max(peak_queue, len(rep.waiting))
        else:
            push(now + cfg.reject_s, "error", aid)

    def fail_attempt(now, aid):
        nonlocal tokens
        a = attempts[aid]
        if a["resolved"]:
            return
        a["resolved"] = True
        r = a["req"]
        q = reqs[r]
        if q["done"]:
            return
        if q["attempts"] >= policy.max_attempts:
            q["done"] = True
            return
        if policy.budget_ratio > 0:
            if tokens < 1.0:
                q["done"] = True        # budget empty: surface the failure
                return
            tokens -= 1.0
        d = backoff_delay(policy.backoff, q["attempts"], cfg.base_backoff_s,
                          cfg.cap_backoff_s, rng)
        push(now + d, "retry", r)

    while events:
        now, _, kind, data = heapq.heappop(events)
        if kind == "arrive":
            if policy.budget_ratio > 0:
                tokens = min(policy.budget_cap, tokens + policy.budget_ratio)
            launch(now, data)
        elif kind == "retry":
            if not reqs[data]["done"]:
                launch(now, data)
        elif kind in ("error", "timeout"):
            fail_attempt(now, data)
        elif kind == "done":
            a = attempts[data]
            rep = reps[a["replica"]]
            rep.busy -= 1
            while rep.waiting and rep.busy < cfg.slots:
                nxt = rep.waiting.pop(0)
                rep.busy += 1
                push(now + cfg.service_s, "done", nxt)
            if a["resolved"]:
                wasted += 1             # finished after the client gave up
            else:
                a["resolved"] = True
                q = reqs[a["req"]]
                if not q["done"]:
                    q["done"], q["ok"], q["lat"] = True, True, now - q["start"]

    def phase(lo, hi):
        ids = [r for r, q in reqs.items() if lo <= q["start"] < hi]
        n = len(ids)
        ok = sum(1 for r in ids if reqs[r]["ok"])
        att = sum(reqs[r]["attempts"] for r in ids)
        return {"requests": n, "success_rate": round(ok / n, 3) if n else None,
                "amplification": round(att / n, 3) if n else None}

    o0, o1 = cfg.outage
    return {"policy": policy.name,
            "before": phase(0, o0), "during": phase(o0, o1), "after": phase(o1, cfg.duration),
            "peak_attempts_per_s": max(per_sec),
            "wasted_completions": wasted, "peak_queue": peak_queue}


POLICIES = (
    Policy("no_retry", 1),
    Policy("naive_4_immediate", 4, "none"),
    Policy("exp_4_no_jitter", 4, "exp"),
    Policy("full_jitter_4", 4, "full"),
    Policy("full_jitter_4_budget10", 4, "full", budget_ratio=0.10),
)


SCENARIOS = {
    "short queue (rejects fast)": Config(rate=52, queue=8),
    "deep queue (waits pass the timeout)": Config(rate=52, queue=24),
}


def table(cfg):
    lines = [f"{'policy':<24}{'amp.during':>11}{'ok.during':>11}{'ok.after':>10}"
             f"{'peak att/s':>12}{'wasted':>8}"]
    for p in POLICIES:
        r = simulate(p, cfg)
        lines.append(f"{p.name:<24}{r['during']['amplification']:>11}"
                     f"{r['during']['success_rate']:>11}{r['after']['success_rate']:>10}"
                     f"{r['peak_attempts_per_s']:>12}{r['wasted_completions']:>8}")
    return "\n".join(lines)


if __name__ == "__main__":
    for name, cfg in SCENARIOS.items():
        print(f"== {name}, {cfg.rate:.0f} user req/s, outage {cfg.outage[0]:.0f}-{cfg.outage[1]:.0f} s")
        print(table(cfg))
