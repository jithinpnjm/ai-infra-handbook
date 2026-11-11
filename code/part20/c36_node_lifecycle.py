#!/usr/bin/env python3
"""A state model of worker-node replacement in a Soperator-style cluster.

Mechanisms come from nebius/soperator at commit f10392e1264a (2026-11-10):
  docs/passive-checks.md, internal/controller/soperatorchecks/slurm_nodes_controller.go,
  internal/controller/soperatorchecks/k8s_nodes_controller.go, docs/worker-node-rollout.md.
The numbers (budget, report limit, replacement time) are parameters you choose.
Nebius has not published the platform's real limits. Time is in whole minutes.

Run: python3 c36_node_lifecycle.py   (prints a demo with five failing nodes)
"""
from dataclasses import dataclass

# Order matters: the first substring that matches wins (consts.SlurmNodeReasonsList).
REASONS = [
    ("Kill task failed", "reboot"),
    ("[compute_maintenance] node replacement process", "maintenance"),
    ("[compute_maintenance] node reboot process", "reboot"),
    ("[node_problem]", "replace"),
    ("[user_problem]", "none"),
    ("[hardware_problem]", "replace"),
]


def classify(reason):
    """Return what the automation does for a Slurm drain reason."""
    for needle, action in REASONS:
        if needle in (reason or ""):
            return action
    return "none"  # unknown reasons, for example "Prolog error" or [software_problem]


@dataclass
class Node:
    name: str
    instance: int = 1
    instance_created_at: int = 0
    jobs_end_at: int = 0          # minute when its last job ends; 0 means idle
    drain_reason: str = ""
    drained_at: int = 0
    cordoned: bool = False
    hw_suspected: bool = False
    state: str = "ready"          # ready, replacing, joining
    ready_at: int = 0             # when replacing or joining ends
    not_ready_since: int = -1

    def running_jobs(self, now):
        return self.jobs_end_at > now

    def schedulable(self, now):
        return self.state == "ready" and not self.drain_reason and not self.cordoned


class Cluster:
    def __init__(self, names, max_unavailable=1, reports_per_window=2, report_window=30,
                 replace_minutes=10, join_minutes=5, not_ready_timeout=15):
        self.now = 0
        self.nodes = {n: Node(n) for n in names}
        self.max_unavailable = max_unavailable
        self.reports_per_window = reports_per_window
        self.report_window = report_window
        self.replace_minutes = replace_minutes
        self.join_minutes = join_minutes
        self.not_ready_timeout = not_ready_timeout
        self.reports = []            # minutes at which SetUnhealthy was accepted
        self.log = []
        self.max_concurrent = 0

    # -- inputs -----------------------------------------------------------
    def run_job(self, name, minutes):
        self.nodes[name].jobs_end_at = self.now + minutes

    def drain(self, name, reason):
        n = self.nodes[name]
        n.drain_reason = reason
        n.drained_at = self.now

    def go_not_ready(self, name):
        self.nodes[name].not_ready_since = self.now

    # -- accounting -------------------------------------------------------
    def in_flight(self):
        return sum(1 for n in self.nodes.values() if n.state != "ready" or n.hw_suspected)

    def report_slot_free(self):
        recent = [t for t in self.reports if t > self.now - self.report_window]
        return len(recent) < self.reports_per_window

    def capacity(self):
        return sum(1 for n in self.nodes.values() if n.schedulable(self.now))

    # -- one minute -------------------------------------------------------
    def tick(self):
        self.now += 1
        for n in self.nodes.values():
            if n.state != "ready" and self.now >= n.ready_at:
                if n.state == "replacing":
                    n.state, n.ready_at = "joining", self.now + self.join_minutes
                    n.instance += 1
                    n.instance_created_at = self.now
                    n.hw_suspected = False
                    n.cordoned = False
                    n.jobs_end_at = 0
                    n.not_ready_since = -1
                else:
                    n.state = "ready"
        self._reconcile()
        self.max_concurrent = max(self.max_concurrent, self.in_flight())

    def _fully_drained(self, n):
        return bool(n.drain_reason) and not n.running_jobs(self.now)

    def _start_replacement(self, n, why):
        n.state, n.ready_at = "replacing", self.now + self.replace_minutes
        n.cordoned = True
        self.log.append((self.now, n.name, why))

    def _reconcile(self):
        # NotReady nodes are deleted after the timeout (k8s_nodes_controller).
        for n in self.nodes.values():
            if n.state == "ready" and 0 <= n.not_ready_since <= self.now - self.not_ready_timeout:
                self._start_replacement(n, "not-ready-timeout")
        candidates = []
        for n in self.nodes.values():
            if n.state == "joining" or not n.drain_reason:
                continue
            action = classify(n.drain_reason)
            if action != "replace":
                continue
            if n.state == "ready" and n.drained_at < n.instance_created_at:
                n.drain_reason, n.drained_at = "", 0  # stale drain on a fresh instance
                self.log.append((self.now, n.name, "undrain-stale"))
                continue
            if n.hw_suspected or n.state != "ready":
                continue
            if not self._fully_drained(n):
                continue  # wait for jobs: never replace under a running job
            candidates.append(n)
        # Drain order: oldest failure first, name breaks ties.
        for n in sorted(candidates, key=lambda x: (x.drained_at, x.name)):
            if self.in_flight() >= self.max_unavailable:
                break
            if not self.report_slot_free():
                break  # node stays cordoned-free but drained, waiting for a report slot
            self.reports.append(self.now)
            n.hw_suspected = True
            self._start_replacement(n, "hardware-issues-suspected")


def demo():
    c = Cluster([f"worker-{i}" for i in range(6)], max_unavailable=2, reports_per_window=2,
                report_window=20)
    for i in range(5):
        c.drain(f"worker-{i}", "[node_problem] gpu_health_check: xid")
    c.run_job("worker-0", 12)
    for _ in range(80):
        c.tick()
    for t, name, why in c.log:
        print(f"t={t:3d} {name} {why}")
    print("max concurrent in flight:", c.max_concurrent, "capacity at end:", c.capacity())


if __name__ == "__main__":
    demo()
