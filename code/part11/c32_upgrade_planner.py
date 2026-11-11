#!/usr/bin/env python3
"""Plan an NVKE control-plane upgrade and worker recycle, using the rules in the controller source.

Rules (nvke commit 487f511, controller/internal/server/clusters.go):
  * the control plane moves up only: no downgrade, no same version
  * one minor version per request, any patch bump is allowed
  * every worker pool must stay within 3 minor versions behind the new control plane
  * the cluster needs a controlPlaneVIP
The API does NOT check a pool version against the control plane when you update a
pool (observed live, node_pools.go sets the field without a check), so this planner
adds the upstream rule that a pool must not be newer than the control plane.
That extra rule is the author's recommendation, tagged inference in the chapter.
"""
import math
import sys
from dataclasses import dataclass


class SkewError(ValueError):
    pass


def parse(v):
    parts = v.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts) or v.startswith("v"):
        raise SkewError(f"invalid version {v!r}: expected X.Y.Z with no leading v")
    return tuple(int(p) for p in parts)


def check_cp_step(current, new):
    """Mirror ValidateKubernetesVersionSkewWithControlPlane."""
    c, n = parse(current), parse(new)
    if n < c:
        raise SkewError(f"downgrade not supported ({current} -> {new})")
    if n == c:
        raise SkewError(f"requested version must be greater than {current}")
    if n[0] == c[0] and n[1] - c[1] > 1:
        raise SkewError("control plane can only be upgraded 1 minor version at a time")


def check_worker_skew(pools, new_cp):
    """Mirror ValidateKubernetesVersionSkewWithWorkerNodes: pool minor >= cp minor - 3."""
    n = parse(new_cp)
    for name, version in pools.items():
        p = parse(version)
        if p[0] != n[0]:
            raise SkewError(f"pool {name} major version differs from the control plane")
        if p[1] < n[1] - 3:
            raise SkewError(f"pool {name} at {version} is more than 3 minor versions behind {new_cp}")


def cp_path(current, target, available=None):
    """Return the control-plane versions to request, one minor at a time, ending at target.

    available lists the versions your node images carry. Without it an intermediate hop uses
    patch 0 as a placeholder, which a real site must replace with a version it has an image for.
    """
    c, t = parse(current), parse(target)
    if t <= c:
        raise SkewError("target must be newer than current")
    if c[0] != t[0]:
        raise SkewError("major version changes are not planned")
    steps = []
    minor = c[1]
    while minor < t[1]:
        minor += 1
        if minor == t[1]:
            steps.append(target)
            continue
        have = sorted((parse(a) for a in (available or []) if parse(a)[:2] == (c[0], minor)), reverse=True)
        steps.append(".".join(map(str, have[0])) if have else f"{c[0]}.{minor}.0")
    if t[1] == c[1]:
        steps = [target]
    return steps


def plan(current_cp, target_cp, pools, available=None):
    """Return an ordered list of actions. pools maps pool name to its Kubernetes version."""
    pools = dict(pools)
    actions = []
    cur = current_cp
    for step in cp_path(current_cp, target_cp, available):
        check_cp_step(cur, step)
        check_worker_skew(pools, step)
        actions.append(("patch-cluster", step))
        cur = step
    # pools follow the final control-plane version, oldest first
    final = parse(target_cp)
    for name, version in sorted(pools.items(), key=lambda kv: parse(kv[1])):
        if parse(version) < final:
            actions.append(("patch-nodepool", name, target_cp))
            pools[name] = target_cp
    return actions


def recycle_marks(desired, available, budget):
    """How many outdated nodes auto mode may mark now.

    marks = budget - shortfall, never below 0. shortfall = desired - available, where a node
    that is not Ready, is cordoned, is deleting or is already marked is not available.
    """
    shortfall = max(0, desired - available)
    return max(0, budget - shortfall)


def recycle_rounds(desired, outdated, budget):
    """Rounds needed when every round completes before the next. Zero budget never finishes."""
    if outdated == 0:
        return 0
    if budget <= 0:
        raise SkewError("recycleBudget 0: auto mode marks nothing, delete outdated nodes by hand")
    return math.ceil(outdated / budget)


@dataclass
class ControlPlane:
    count: int
    max_surge: int = 0

    def quorum(self):
        return self.count // 2 + 1

    def survivable_failures(self):
        return self.count - self.quorum()

    def replace_one_at_a_time_is_safe(self):
        """With maxSurge 0 a node leaves before its replacement joins: voters drop by one."""
        if self.max_surge >= 1:
            return self.count >= 1
        return self.count - 1 >= self.quorum()


def main(argv):
    if len(argv) < 4:
        print("usage: c32_upgrade_planner.py CURRENT TARGET POOL=VERSION ...", file=sys.stderr)
        return 2
    pools = dict(a.split("=", 1) for a in argv[3:])
    try:
        for a in plan(argv[1], argv[2], pools):
            print(*a)
    except SkewError as exc:
        print("REFUSED:", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
