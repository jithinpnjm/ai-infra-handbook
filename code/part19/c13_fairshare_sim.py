#!/usr/bin/env python3
"""Fair-share, quota and preemption simulator for a shared research GPU pool (chapter 19.13).

Standard library only. One step is one minute. The trace is generated from a seed and is MADE UP to
show mechanisms. It is not a measurement of any real cluster.

Cluster: 64 GPUs = 56 batch GPUs (four teams with 14 nominal each, like Kueue ClusterQueues in one
cohort) + 8 notebook GPUs (the ResourceQuota pool). Policies for the batch pool:

  static        no borrowing, no preemption          (hard quota)
  borrow        borrow idle quota, never preempt     (owners wait for borrowers to finish)
  reclaim       borrow, and preempt borrowers to give an owner its nominal quota back,
                plus lower-priority preemption inside a team
  reclaim_cull  reclaim + idle notebooks are culled after a timeout

Simplifications (my modelling, NOT verified against Kueue internals):
  - a borrower is preempted only for the part of its usage above nominal quota;
  - victims are picked lowest priority first, then most recently started;
  - a job may trigger preemption when its team's usage at the same or higher priority, plus the job,
    stays within nominal quota (lower-priority jobs of the team count as displaceable);
  - a preemption plan is executed only if it frees enough GPUs for the whole gang;
  - a preempted job loses the work since its last checkpoint and goes back to the queue.
"""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field

TEAMS = ("a", "b", "c", "d")
NOMINAL = 14            # batch GPUs per team
BATCH_TOTAL = NOMINAL * len(TEAMS)
NOTEBOOK_GPUS = 8
HORIZON = 2880          # two days of minutes
PRIO = {"sweep": 0, "eval": 5, "train": 10}


@dataclass
class Job:
    id: int
    team: str
    kind: str
    gpus: int
    submit: int
    work: int                      # minutes of work at full speed
    ckpt: int | None = None        # checkpoint interval in minutes of work, None = no checkpoint
    done: int = 0
    start: int | None = None
    first_start: int | None = None
    entitled: bool = False         # fit inside nominal quota at submit time
    preemptions: int = 0

    @property
    def prio(self) -> int:
        return PRIO[self.kind]


@dataclass
class Notebook:
    id: int
    team: str
    submit: int
    hold: int      # minutes the user keeps the GPU if nobody culls it
    active: int    # minutes of real GPU use at the start of the session
    start: int | None = None
    end: int | None = None
    culled: bool = False


def make_trace(seed: int = 7):
    rng = random.Random(seed)
    jobs: list[Job] = []
    nid = 0

    def add(team, kind, gpus, submit, work, ckpt=None):
        nonlocal nid
        nid += 1
        jobs.append(Job(nid, team, kind, gpus, submit, work, ckpt))

    # Team a: four sweep waves of 1-GPU trials. A heavy borrower.
    for wave_start in (0, 300, 600, 900, 1500, 1800, 2100):
        for _ in range(100):
            add("a", "sweep", 1, wave_start + rng.randint(0, 20), rng.randint(60, 180))
    # Teams b and c: long gang training jobs with 30 minute checkpoints.
    for t0 in (30, 400, 800, 1500, 2000):
        add("b", "train", 8, t0 + rng.randint(0, 30), rng.randint(240, 420), 30)
    for t0 in (60, 500, 1100, 1700):
        add("c", "train", 12, t0 + rng.randint(0, 30), rng.randint(240, 360), 30)
    # Team d is quiet, then needs its quota back mid-day one.
    add("d", "train", 12, 700, 300, 30)
    add("d", "train", 12, 720, 300, 30)
    # Everybody runs small evals.
    for _ in range(150):
        add(rng.choice(TEAMS), "eval", rng.choice((1, 1, 2)), rng.randint(0, HORIZON - 200), rng.randint(15, 40))
    jobs.sort(key=lambda j: (j.submit, j.id))

    notebooks: list[Notebook] = []
    for day in (0, 1440):
        for i in range(34):
            hold = rng.randint(120, 480)
            active = max(20, int(hold * rng.uniform(0.2, 0.6)))
            notebooks.append(Notebook(len(notebooks) + 1, rng.choice(TEAMS), day + rng.randint(0, 600), hold, active))
    notebooks.sort(key=lambda n: (n.submit, n.id))
    return jobs, notebooks


def mark_entitled(jobs):
    """A job is entitled if it fits in its team's nominal quota given the team's other work that is
    alive at its submit time on an infinitely large cluster. This does not depend on the policy,
    so entitled-job wait times are comparable across policies."""
    for j in jobs:
        alive = sum(o.gpus for o in jobs if o.team == j.team and o.submit <= j.submit < o.submit + o.work)
        j.entitled = alive <= NOMINAL


def _usage(running):
    u = {t: 0 for t in TEAMS}
    for j in running:
        u[j.team] += j.gpus
    return u


def run_batch(jobs_in, policy: str):
    """Run the batch pool. policy in static, borrow, reclaim."""
    if policy not in ("static", "borrow", "reclaim"):
        raise ValueError(f"unknown policy {policy!r}")
    borrow = policy != "static"
    preempt = policy == "reclaim"
    jobs = [Job(**{k: getattr(j, k) for k in ("id", "team", "kind", "gpus", "submit", "work", "ckpt")}) for j in jobs_in]
    pending = {t: [] for t in TEAMS}
    running: list[Job] = []
    finished: list[Job] = []
    arrivals = list(jobs)
    ai = 0
    lost_gpu_min = 0
    alloc_gpu_min = 0
    delivered = {t: 0 for t in TEAMS}
    mark_entitled(jobs)
    rejected = [j for j in jobs if j.gpus > BATCH_TOTAL]   # can never be gang-scheduled
    rejected_ids = {j.id for j in rejected}
    preempt_events = 0
    max_over_nominal = {t: 0 for t in TEAMS}

    for now in range(HORIZON):
        for j in list(running):
            if j.done >= j.work:
                running.remove(j)
                finished.append(j)
        while ai < len(arrivals) and arrivals[ai].submit <= now:
            j = arrivals[ai]
            ai += 1
            if j.id in rejected_ids:
                continue
            pending[j.team].append(j)
        # Teams furthest below their nominal share are served first.
        usage = _usage(running)
        for team in sorted(TEAMS, key=lambda t: (usage[t] / NOMINAL, t)):
            queue = sorted(pending[team], key=lambda j: (-j.prio, j.submit, j.id))
            for j in queue:
                usage = _usage(running)
                free = BATCH_TOTAL - sum(usage.values())
                fits_nominal = usage[team] + j.gpus <= NOMINAL
                admit = False
                if j.gpus <= free and (borrow or fits_nominal):
                    admit = True
                elif preempt and sum(r.gpus for r in running if r.team == team and r.prio >= j.prio) + j.gpus <= NOMINAL:
                    victims = _plan_preemption(j, running, usage, free)
                    if victims is not None:
                        for v in victims:
                            running.remove(v)
                            lost = v.done - ((v.done // v.ckpt) * v.ckpt if v.ckpt else 0)
                            lost_gpu_min += lost * v.gpus
                            v.done -= lost
                            v.preemptions += 1
                            preempt_events += 1
                            pending[v.team].append(v)
                        admit = True
                if admit:
                    pending[team].remove(j)
                    j.start = now
                    if j.first_start is None:
                        j.first_start = now
                    running.append(j)
        usage = _usage(running)
        for t in TEAMS:
            delivered[t] += usage[t]
            max_over_nominal[t] = max(max_over_nominal[t], usage[t] - NOMINAL)
        alloc_gpu_min += sum(usage.values())
        for j in running:
            j.done += 1
    return {
        "policy": policy,
        "jobs": jobs,
        "finished": finished,
        "unfinished": [j for j in jobs if j not in finished and j.id not in rejected_ids],
        "rejected": rejected,
        "lost_gpu_hours": lost_gpu_min / 60,
        "alloc_gpu_hours": alloc_gpu_min / 60,
        "utilization": alloc_gpu_min / (BATCH_TOTAL * HORIZON),
        "delivered_gpu_hours": {t: delivered[t] / 60 for t in TEAMS},
        "preemptions": preempt_events,
        "max_over_nominal": max_over_nominal,
    }


def _plan_preemption(job, running, usage, free):
    """Return victims that free enough GPUs for job, or None. See module docstring for the rules."""
    need = job.gpus - free
    victims: list[Job] = []
    # 1. borrowers in other teams, only for the part above nominal
    spare = {t: usage[t] - NOMINAL for t in TEAMS}
    cands = [r for r in running if r.team != job.team and spare[r.team] > 0]
    for r in sorted(cands, key=lambda r: (r.prio, -(r.start or 0), r.id)):
        if need <= 0:
            break
        if spare[r.team] - r.gpus >= 0:
            victims.append(r)
            spare[r.team] -= r.gpus
            need -= r.gpus
    # 2. lower priority jobs in the same team
    if need > 0:
        own = [r for r in running if r.team == job.team and r.prio < job.prio]
        for r in sorted(own, key=lambda r: (r.prio, -(r.start or 0), r.id)):
            if need <= 0:
                break
            victims.append(r)
            need -= r.gpus
    return victims if need <= 0 else None


def run_notebooks(notebooks_in, cull_after: int | None):
    """Notebook pool of NOTEBOOK_GPUS. cull_after = idle minutes before the culler stops a server."""
    nbs = [Notebook(n.id, n.team, n.submit, n.hold, n.active) for n in notebooks_in]
    queue: list[Notebook] = []
    running: list[Notebook] = []
    done: list[Notebook] = []
    ai = 0
    held_min = 0
    idle_min = 0
    for now in range(HORIZON + 600):
        for n in list(running):
            if now >= n.end:
                running.remove(n)
                done.append(n)
        while ai < len(nbs) and nbs[ai].submit <= now:
            queue.append(nbs[ai])
            ai += 1
        while queue and len(running) < NOTEBOOK_GPUS:
            n = queue.pop(0)
            n.start = now
            stop = n.hold
            if cull_after is not None and n.active + cull_after < n.hold:
                stop = n.active + cull_after
                n.culled = True
            n.end = now + stop
            running.append(n)
        for n in running:
            held_min += 1
            if now - n.start >= n.active:
                idle_min += 1
    waits = [n.start - n.submit for n in done]
    return {
        "cull_after": cull_after,
        "sessions": len(done),
        "culled": sum(n.culled for n in done),
        "held_gpu_hours": held_min / 60,
        "idle_gpu_hours": idle_min / 60,
        "wait_p50": _pct(waits, 50),
        "wait_p95": _pct(waits, 95),
        "still_queued": len(queue),
    }


def _pct(xs, p):
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = min(len(xs) - 1, max(0, round(p / 100 * (len(xs) - 1))))
    return float(xs[k])


def entitled_wait(result):
    """Minutes from submit to first start for train and eval jobs that fit inside their team's nominal
    quota. Sweep trials are excluded: they are the bulk filler and queue behind each other by design."""
    w = [j.first_start - j.submit for j in result["jobs"]
         if j.entitled and j.kind != "sweep" and j.first_start is not None]
    return {"n": len(w), "p50": _pct(w, 50), "p95": _pct(w, 95), "max": max(w) if w else 0}


def summarize(seed: int = 7):
    jobs, notebooks = make_trace(seed)
    rows = []
    for pol in ("static", "borrow", "reclaim"):
        r = run_batch(jobs, pol)
        ew = entitled_wait(r)
        rows.append((pol, r["utilization"], ew["p50"], ew["p95"], r["preemptions"], r["lost_gpu_hours"], len(r["unfinished"])))
    nb = {"no_cull": run_notebooks(notebooks, None), "cull_30": run_notebooks(notebooks, 30)}
    return rows, nb


def main():
    rows, nb = summarize()
    print(f"{'policy':<10}{'util':>7}{'wait p50':>10}{'wait p95':>10}{'preempt':>9}{'lost GPUh':>11}{'unfinished':>11}")
    for pol, u, p50, p95, pe, lost, unf in rows:
        print(f"{pol:<10}{u:>7.2f}{p50:>10.0f}{p95:>10.0f}{pe:>9d}{lost:>11.1f}{unf:>11d}")
    print()
    print(f"{'notebooks':<10}{'sessions':>9}{'culled':>8}{'held h':>9}{'idle h':>9}{'wait p50':>10}{'wait p95':>10}{'queued':>8}")
    for name, r in nb.items():
        print(f"{name:<10}{r['sessions']:>9}{r['culled']:>8}{r['held_gpu_hours']:>9.0f}{r['idle_gpu_hours']:>9.0f}{r['wait_p50']:>10.0f}{r['wait_p95']:>10.0f}{r['still_queued']:>8}")


if __name__ == "__main__":
    main()
