# code/part20/c16_fleet_health.py
"""Node health state machine with a blast-radius limiter (chapter 20.16).

Xid actions come from the NVIDIA Xid catalog. The thresholds, dwell times and
limits are starting values chosen for this chapter, not vendor figures.
"""
from collections import deque
from dataclasses import dataclass, field
from enum import Enum


class State(str, Enum):
    HEALTHY = "healthy"
    SUSPECT = "suspect"
    CORDONED = "cordoned"
    DRAINING = "draining"
    QUARANTINED = "quarantined"
    REPAIRING = "repairing"
    RMA = "rma"
    VALIDATING = "validating"


S = State
LEGAL = {
    S.HEALTHY: {S.SUSPECT, S.CORDONED},
    S.SUSPECT: {S.HEALTHY, S.CORDONED},
    S.CORDONED: {S.DRAINING},
    S.DRAINING: {S.QUARANTINED},
    S.QUARANTINED: {S.REPAIRING},
    S.REPAIRING: {S.VALIDATING, S.RMA},
    S.RMA: {S.VALIDATING},
    S.VALIDATING: {S.HEALTHY, S.QUARANTINED},
}

# Xid -> catalog "immediate action" (NVIDIA Xid catalog, fetched 2026-11-09).
XID_ACTION = {
    13: "RESTART_APP", 31: "RESTART_APP", 43: "IGNORE", 45: "RESTART_FM",
    48: "RESET_GPU", 63: "IGNORE", 64: "RESET_GPU", 74: "NVLINK",
    79: "RESTART_BM", 94: "RESTART_APP", 95: "RESET_GPU",
    119: "RESET_GPU", 120: "RESET_GPU", 121: "IGNORE",
}
REPEAT_LIMIT = 3  # app-level Xids repeating this often on one node look like hardware


def classify_xid(xid, recent_count=0):
    """Return 'ignore', 'suspect' or 'drain'. Unknown codes are never ignored."""
    action = XID_ACTION.get(xid)
    if action == "IGNORE":
        return "ignore"
    if action in ("RESET_GPU", "RESTART_BM", "NVLINK"):
        return "drain"
    if action == "RESTART_APP":
        return "drain" if recent_count + 1 >= REPEAT_LIMIT else "suspect"
    return "suspect"


@dataclass
class Decision:
    allowed: bool
    reason: str


class DrainLimiter:
    """Caps how much of the fleet automation may take out of service.

    A node holds its slot from the moment it is granted until release(), so a
    node that never returns keeps counting against the budget.
    """

    def __init__(self, fleet_size, max_fraction=0.05, max_per_hour=4,
                 max_per_domain=1, trip_flags=6, window_s=600):
        self.budget = max(1, int(fleet_size * max_fraction))
        self.max_per_hour = max_per_hour
        self.max_per_domain = max_per_domain
        self.trip_flags = trip_flags
        self.window_s = window_s
        self.out = {}          # node -> failure domain
        self.grants = deque()  # grant timestamps
        self.flags = deque()   # (time, node) of verdicts that wanted a drain
        self.frozen = False

    def _trim(self, now):
        while self.grants and now - self.grants[0] >= 3600:
            self.grants.popleft()
        while self.flags and now - self.flags[0][0] >= self.window_s:
            self.flags.popleft()

    def request(self, now, node, domain):
        self._trim(now)
        if node in self.out:
            return Decision(True, "already out")
        self.flags.append((now, node))
        if len({n for _, n in self.flags}) >= self.trip_flags:
            self.frozen = True
        if self.frozen:
            return Decision(False, "frozen: many nodes flagged, suspect a fleet-wide cause")
        if len(self.out) >= self.budget:
            return Decision(False, "fleet budget exhausted")
        if sum(1 for d in self.out.values() if d == domain) >= self.max_per_domain:
            return Decision(False, "failure domain budget exhausted")
        if len(self.grants) >= self.max_per_hour:
            return Decision(False, "hourly rate exhausted")
        self.out[node] = domain
        self.grants.append(now)
        return Decision(True, "granted")

    def release(self, node):
        self.out.pop(node, None)

    def unfreeze(self):
        self.frozen = False
        self.flags.clear()


@dataclass
class Node:
    name: str
    domain: str
    state: State = State.HEALTHY
    since: float = 0.0
    reason: str = ""
    recent_xids: deque = field(default_factory=deque)


DEFAULT_MAX_DWELL_S = {
    State.SUSPECT: 3600, State.CORDONED: 600, State.DRAINING: 1800,
    State.QUARANTINED: 4 * 3600, State.REPAIRING: 24 * 3600,
    State.RMA: 14 * 24 * 3600, State.VALIDATING: 4 * 3600,
}


class Fleet:
    def __init__(self, nodes, limiter, xid_window_s=3600):
        self.nodes = {n.name: n for n in nodes}
        self.limiter = limiter
        self.xid_window_s = xid_window_s
        self.held = {}  # node -> reason, for a human to look at

    def _move(self, node, to, now, reason=""):
        if to not in LEGAL[node.state]:
            raise ValueError(f"illegal move {node.state.value} -> {to.value}")
        node.state, node.since, node.reason = to, now, reason
        if to is S.HEALTHY:
            self.limiter.release(node.name)
            self.held.pop(node.name, None)

    def report_xid(self, name, now, xid):
        node = self.nodes[name]
        while node.recent_xids and now - node.recent_xids[0] >= self.xid_window_s:
            node.recent_xids.popleft()
        verdict = classify_xid(xid, len(node.recent_xids))
        node.recent_xids.append(now)
        if verdict == "ignore" or node.state not in (S.HEALTHY, S.SUSPECT):
            return node.state
        if verdict == "suspect":
            if node.state is S.HEALTHY:
                self._move(node, S.SUSPECT, now, f"xid {xid}")
            return node.state
        decision = self.limiter.request(now, name, node.domain)
        if decision.allowed:
            self._move(node, S.CORDONED, now, f"xid {xid}")
            self.held.pop(name, None)
        else:
            if node.state is S.HEALTHY:
                self._move(node, S.SUSPECT, now, f"xid {xid}")
            self.held[name] = decision.reason
        return node.state

    def advance(self, name, now, to, reason=""):
        self._move(self.nodes[name], to, now, reason)

    def stuck(self, now, max_dwell=None):
        """Nodes that sit in a state longer than allowed: silent capacity loss."""
        limits = max_dwell or DEFAULT_MAX_DWELL_S
        return sorted(n.name for n in self.nodes.values()
                      if n.state in limits and now - n.since > limits[n.state])

    def serving(self):
        return sum(1 for n in self.nodes.values() if n.state in (S.HEALTHY, S.SUSPECT))
