#!/usr/bin/env python3
"""Queue arithmetic used by chapter 19.2 (standard library only).

Three small models, each taken from upstream documentation, none of them a scheduler:

* kai_fair_share: how KAI Scheduler divides a pool among sibling queues. Phase 1 gives each queue
  min(quota, request). Phase 2 hands surplus to the highest-priority bucket first, split by
  overQuotaWeight inside a bucket, never above a queue's request or limit
  (KAI Scheduler docs/fairness and docs/scheduling-deep-dive, v0.18.7).
* Kueue admission and reclaim for ClusterQueues in one cohort: a workload is admitted if it fits the
  unused nominal quota, or by borrowing unused nominal quota of cohort members, capped by the
  borrowingLimit and by each lender's lendingLimit (Kueue docs, ClusterQueue page, v0.20).
* Day-2 capacity arithmetic: blast radius in GPUs, drain headroom, and the partial-placement deadlock.

Run `python3 c02_queue_math.py` to print the numbers the chapter quotes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

INF = float("inf")


# --------------------------------------------------------------------------- KAI fair share
@dataclass
class KaiQueue:
    name: str
    quota: float = 0.0            # deserved, guaranteed
    request: float = 0.0          # what the queue's jobs ask for right now
    weight: float = 1.0           # overQuotaWeight
    priority: int = 100           # queue priority; KAI's default is 100
    limit: Optional[float] = None  # None or -1 means no limit
    children: List["KaiQueue"] = field(default_factory=list)

    def cap(self) -> float:
        lim = INF if self.limit is None or self.limit < 0 else self.limit
        return min(self.demand(), lim)

    def demand(self) -> float:
        if self.children:
            return sum(c.cap() for c in self.children)
        return self.request


def kai_fair_share(total: float, queues: List[KaiQueue], eps: float = 1e-9) -> Dict[str, float]:
    """Fair share of `total` among sibling `queues`, then recursively inside each parent."""
    if total < 0:
        raise ValueError("total must be >= 0")
    share = {q.name: 0.0 for q in queues}
    remaining = float(total)
    # Phase 1: guaranteed quota, capped by what the queue wants. Quota is honoured first.
    for q in queues:
        give = min(q.quota, q.cap(), remaining)
        share[q.name] += give
        remaining -= give
    # Phase 2: surplus, highest priority bucket first, weighted inside the bucket.
    for prio in sorted({q.priority for q in queues}, reverse=True):
        bucket = [q for q in queues if q.priority == prio]
        while remaining > eps:
            hungry = [q for q in bucket if q.cap() - share[q.name] > eps and q.weight > 0]
            if not hungry:
                break
            wsum = sum(q.weight for q in hungry)
            handed = 0.0
            for q in hungry:
                give = min(remaining * q.weight / wsum, q.cap() - share[q.name])
                share[q.name] += give
                handed += give
            remaining -= handed
            if handed <= eps:
                break
    out = dict(share)
    for q in queues:
        if q.children:
            out.update(kai_fair_share(share[q.name], q.children, eps))
    return out


# --------------------------------------------------------------------------- Kueue cohort
@dataclass
class ClusterQueue:
    name: str
    nominal: int
    borrowing_limit: Optional[int] = None   # None = unlimited borrowing
    lending_limit: Optional[int] = None     # None = can lend everything unused
    used: int = 0

    def unused_nominal(self) -> int:
        return max(0, self.nominal - self.used)

    def lendable(self) -> int:
        lend = self.unused_nominal()
        if self.lending_limit is not None:
            lend = min(lend, self.lending_limit)
        return lend

    def borrowed(self) -> int:
        return max(0, self.used - self.nominal)


def can_admit(cohort: Dict[str, ClusterQueue], name: str, request: int) -> bool:
    """Kueue's three conditions for one resource of one flavor."""
    cq = cohort[name]
    if request <= cq.unused_nominal():
        return True                                    # fits nominal quota, no borrowing
    need = request - cq.unused_nominal()               # amount that must be borrowed
    lendable = sum(o.lendable() for n, o in cohort.items() if n != name)
    if need > lendable:
        return False                                   # the cohort has no such unused quota
    if cq.borrowing_limit is not None and need + cq.borrowed() > cq.borrowing_limit:
        return False                                   # over this queue's borrowingLimit
    return True


def admit(cohort: Dict[str, ClusterQueue], name: str, request: int) -> bool:
    if not can_admit(cohort, name, request):
        return False
    cohort[name].used += request
    return True


def reclaimable(cohort: Dict[str, ClusterQueue], name: str, request: int) -> int:
    """GPUs that reclaimWithinCohort can take back for `name`.

    A pending workload that fits the queue's own nominal quota may preempt workloads in other
    queues that are using more than their nominal quota. Only borrowed capacity can be taken, and
    only for the part of the request that is not already free.
    """
    cq = cohort[name]
    entitled = min(request, cq.unused_nominal())
    shortfall = max(0, entitled - max(0, free_now_for(cohort, name)))
    borrowed_by_others = sum(o.borrowed() for n, o in cohort.items() if n != name)
    return min(shortfall, borrowed_by_others)


def free_now_for(cohort: Dict[str, ClusterQueue], name: str, pool: Optional[int] = None) -> int:
    """Physical GPUs not in use. Defaults to the sum of nominal quotas, which holds when
    quotas add up to the hardware (they do in the capstone: 12 + 4 = 16)."""
    total = pool if pool is not None else sum(c.nominal for c in cohort.values())
    return total - sum(c.used for c in cohort.values())


# --------------------------------------------------------------------------- day-2 arithmetic
def blast_radius(nodes_affected: int, gpus_per_node: int, fleet_nodes: int) -> Dict[str, float]:
    if fleet_nodes <= 0 or gpus_per_node <= 0:
        raise ValueError("fleet_nodes and gpus_per_node must be positive")
    if not 0 <= nodes_affected <= fleet_nodes:
        raise ValueError("nodes_affected must be between 0 and fleet_nodes")
    return {
        "gpus_unavailable": nodes_affected * gpus_per_node,
        "fleet_gpus": fleet_nodes * gpus_per_node,
        "percent": 100.0 * nodes_affected / fleet_nodes,
    }


def max_parallel_drain(fleet_nodes: int, gpus_per_node: int, protected_gpus: int) -> int:
    """Most nodes that can be offline at once while `protected_gpus` stay schedulable."""
    spare = fleet_nodes * gpus_per_node - protected_gpus
    if spare < 0:
        raise ValueError("protected_gpus exceeds the fleet")
    return spare // gpus_per_node


def partial_placement(nodes: int, job_nodes: List[int], gang: bool) -> Dict[str, object]:
    """Jobs that need `job_nodes[i]` whole nodes each, submitted together onto `nodes` free nodes.

    Without gang scheduling pods are placed one at a time in round-robin order, so every job holds
    some nodes. A job runs only when it holds all of its nodes. With gang scheduling a job is placed
    only if all its nodes fit, in submission order.
    """
    free = nodes
    held = [0] * len(job_nodes)
    if gang:
        for i, n in enumerate(job_nodes):
            if n <= free:
                held[i] = n
                free -= n
    else:
        progress = True
        while free > 0 and progress:
            progress = False
            for i, n in enumerate(job_nodes):
                if held[i] < n and free > 0:
                    held[i] += 1
                    free -= 1
                    progress = True
    running = [i for i, n in enumerate(job_nodes) if held[i] == n]
    stranded = sum(h for i, h in enumerate(held) if i not in running)
    return {"held": held, "running_jobs": running, "stranded_nodes": stranded, "deadlock": not running and stranded > 0}


def report() -> str:
    lines = []
    tree = [KaiQueue("ml-platform", quota=12, weight=1, children=[
        KaiQueue("team-data-science", quota=8, request=16),
        KaiQueue("team-research", quota=4, request=0)])]
    fs = kai_fair_share(16, tree)
    lines.append(f"KAI fair share, pool 16, data-science wants 16, research idle: {fs}")
    tree = [KaiQueue("ml-platform", quota=12, children=[
        KaiQueue("team-data-science", quota=8, request=16),
        KaiQueue("team-research", quota=4, request=16)])]
    fs = kai_fair_share(12, tree)
    lines.append(f"KAI fair share, pool 12, both teams want 16: {fs}")
    co = {"cq-training": ClusterQueue("cq-training", 12), "cq-serving": ClusterQueue("cq-serving", 4)}
    lines.append(f"Kueue: 16-GPU gang admitted to cq-training with serving idle: {admit(co, 'cq-training', 16)}")
    lines.append(f"Kueue: serving then asks for 4, free GPUs {free_now_for(co, 'cq-serving')}, "
                 f"reclaimable {reclaimable(co, 'cq-serving', 4)}")
    co2 = {"cq-training": ClusterQueue("cq-training", 12), "cq-serving": ClusterQueue("cq-serving", 4, lending_limit=0)}
    lines.append(f"Kueue with lendingLimit 0 on serving: 16-GPU gang admitted: {can_admit(co2, 'cq-training', 16)}")
    lines.append(f"blast radius 35 of 60 nodes: {blast_radius(35, 8, 60)}")
    lines.append(f"blast radius 3 of 60 nodes: {blast_radius(3, 8, 60)}")
    lines.append(f"blast radius 24 of 120 nodes: {blast_radius(24, 8, 120)}")
    lines.append(f"max parallel drain, 2 nodes x 8 GPUs, 4 protected: {max_parallel_drain(2, 8, 4)}")
    lines.append(f"12 nodes, two 8-node jobs, default scheduler: {partial_placement(12, [8, 8], gang=False)}")
    lines.append(f"12 nodes, two 8-node jobs, gang: {partial_placement(12, [8, 8], gang=True)}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(report())
