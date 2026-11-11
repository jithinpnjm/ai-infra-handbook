"""Reference model of the node-health policy in chapter 19.6.

It mirrors the GPUHealthPolicy fields in c06_gpu_health_policy.yaml (windows, budget,
mode, dry run) and adds the parts the Go operator in code/gpuhealth does not have:
a cordon rate limit, a fleet-wide circuit breaker, a taint path, an RMA ticket and a
return-to-service gate. Time is a plain number of seconds so tests need no clock.

Detection and action are separate. ConditionAgent turns Xid events into the node
condition. NodeHealthController only reads the condition. A missing condition is
treated as healthy for the purpose of cordoning, so a detector outage cannot cordon.
"""
import math
import re
from dataclasses import dataclass, field
from enum import Enum

import c06_xid_classes as xc

OWNER_KEY = "platform.example.com/cordoned-by"
TAINT_KEY = "platform.example.com/gpu-unhealthy"


class Mode(str, Enum):
    IGNORE = "Ignore"
    CORDON = "Cordon"
    CORDON_AND_DRAIN = "CordonAndDrain"


class State(str, Enum):
    HEALTHY = "healthy"
    PENDING = "pending"
    CORDONED = "cordoned"
    DRAINING = "draining"
    REPAIR = "repair"
    VALIDATING = "validating"


class Kind(str, Enum):
    CORDON = "cordon"
    WOULD_CORDON = "would_cordon"
    TAINT = "taint"
    EVICT = "evict"
    OPEN_TICKET = "open_ticket"
    LABEL = "label"
    UNCORDON = "uncordon"
    HOLD = "hold"
    PAGE = "page"


LEGAL = {
    State.HEALTHY: {State.PENDING, State.CORDONED},
    State.PENDING: {State.HEALTHY, State.CORDONED},
    State.CORDONED: {State.DRAINING, State.REPAIR, State.HEALTHY},
    State.DRAINING: {State.CORDONED, State.REPAIR, State.HEALTHY},
    State.REPAIR: {State.VALIDATING},
    State.VALIDATING: {State.REPAIR, State.HEALTHY},
}


@dataclass(frozen=True)
class Action:
    kind: Kind
    node: str
    detail: str = ""


def parse_duration(text):
    """Parse '2m', '300s' or '1h' into seconds, the forms the CRD fields use."""
    m = re.fullmatch(r"(\d+)([smh])", str(text).strip())
    if not m:
        raise ValueError(f"bad duration: {text!r}")
    return int(m.group(1)) * {"s": 1, "m": 60, "h": 3600}[m.group(2)]


def budget(max_unavailable, matched):
    """Nodes this policy may hold unschedulable. An invalid budget means zero."""
    if max_unavailable is None:
        return matched
    text = str(max_unavailable).strip()
    try:
        if text.endswith("%"):
            value = math.ceil(int(text[:-1]) * matched / 100)
        else:
            value = int(text)
    except ValueError:
        return 0
    return max(0, min(value, matched))


@dataclass
class Policy:
    unhealthy_for: int = 120
    healthy_for: int = 300
    action: Mode = Mode.CORDON
    max_unavailable: object = None
    dry_run: bool = False
    drain_method: str = "evict"        # "evict" or "taint"
    max_new_per_hour: int = 3
    breaker_nodes: int = 3             # distinct nodes flagged inside the window
    breaker_window: int = 600
    name: str = "training-pool"

    def __post_init__(self):
        if self.action is Mode.CORDON_AND_DRAIN and self.max_unavailable is None:
            raise ValueError("maxUnavailableNodes is required when action is CordonAndDrain")
        if self.drain_method not in ("evict", "taint"):
            raise ValueError("drain_method must be evict or taint")

    @classmethod
    def from_yaml_text(cls, text, **extra):
        import yaml
        spec = yaml.safe_load(text)["spec"]
        name = yaml.safe_load(text)["metadata"]["name"]
        return cls(
            unhealthy_for=parse_duration(spec.get("unhealthyFor", "2m")),
            healthy_for=parse_duration(spec.get("healthyFor", "5m")),
            action=Mode(spec.get("action", "Cordon")),
            max_unavailable=spec.get("maxUnavailableNodes"),
            dry_run=bool(spec.get("dryRun", False)),
            name=name,
            **extra,
        )


@dataclass
class Node:
    name: str
    condition: object = None           # True, False, or None when no signal exists
    since: float = 0.0                 # last transition time of the condition
    unschedulable: bool = False
    owner: object = None
    reason: str = ""
    pods: int = 0
    pdb_blocked: int = 0               # pods a disruption budget refuses to evict right now
    tainted: bool = False
    labels: dict = field(default_factory=dict)
    ticket: object = None
    ticket_open: bool = False
    diag_passed: bool = False
    needs_rma: bool = False
    state: State = State.HEALTHY


class ConditionAgent:
    """Detection half: turns events into the GPUHealthy condition. It never acts."""

    def on_xid(self, node, xid, now):
        cls = xc.classify_xid(xid)
        if cls == xc.UNRECOVERABLE:
            if node.condition is not False:
                node.condition, node.since = False, now
            node.needs_rma = True
        elif cls == xc.INTERCONNECT:
            node.labels["platform.example.com/nvlink-suspect"] = "true"
        return cls

    def on_signal_restored(self, node, now):
        if node.condition is not True:
            node.condition, node.since = True, now

    def on_signal_lost(self, node):
        node.condition = None


class NodeHealthController:
    def __init__(self, policy, nodes, open_ticket=None):
        self.policy = policy
        self.nodes = {n.name: n for n in nodes}
        self._open_ticket = open_ticket or self._sequential_tickets()
        self._cordon_times = []
        self._flagged = {}             # node -> time it was first seen unhealthy
        self._acked = set()
        self._held = set()             # nodes held while frozen; a human releases them
        self.frozen = False
        self._paged_outage = False

    @staticmethod
    def _sequential_tickets():
        counter = iter(range(1, 10**6))
        return lambda node, evidence: f"RMA-{next(counter):04d}"

    def _move(self, node, to):
        if to is node.state:
            return
        if to not in LEGAL[node.state]:
            raise ValueError(f"illegal move {node.state.value} -> {to.value}")
        node.state = to

    def unfreeze(self, acknowledged):
        """A human confirms these nodes are really broken and releases the breaker."""
        self._acked.update(acknowledged)
        self._flagged.clear()
        self.frozen = False

    def mark_repaired(self, name):
        node = self.nodes[name]
        self._move(node, State.VALIDATING)
        node.diag_passed = False

    def record_diag(self, name, passed):
        node = self.nodes[name]
        if node.state is not State.VALIDATING:
            raise ValueError("a diagnostic result only counts for a node in validation")
        if passed:
            node.diag_passed = True
        else:
            node.diag_passed = False
            self._move(node, State.REPAIR)

    def close_ticket(self, name):
        self.nodes[name].ticket_open = False

    def _verdict(self, node, now):
        if node.condition is False:
            if now - node.since >= self.policy.unhealthy_for:
                return "unhealthy"
            return "pending"
        if node.condition is True:
            return "healthy" if now - node.since >= self.policy.healthy_for else "recovering"
        return "no_signal"

    def reconcile(self, now):
        p = self.policy
        actions = []
        names = sorted(self.nodes)
        verdicts = {n: self._verdict(self.nodes[n], now) for n in names}

        # A detector outage is reported once and never acted on.
        lost = [n for n in names if verdicts[n] == "no_signal"]
        if lost and len(lost) * 2 >= len(names):
            if not self._paged_outage:
                actions.append(Action(Kind.PAGE, "*", f"no health signal from {len(lost)} of {len(names)} nodes"))
                self._paged_outage = True
        else:
            self._paged_outage = False

        for n in names:
            node = self.nodes[n]
            if verdicts[n] == "pending" and node.state is State.HEALTHY:
                self._move(node, State.PENDING)
            elif verdicts[n] in ("healthy", "recovering", "no_signal") and node.state is State.PENDING:
                self._move(node, State.HEALTHY)

        # Circuit breaker: many distinct nodes flagged together point at a shared cause.
        self._flagged = {n: t for n, t in self._flagged.items() if now - t < p.breaker_window}
        for n in names:
            if (verdicts[n] == "unhealthy" and not self.nodes[n].unschedulable
                    and n not in self._flagged and n not in self._acked):
                self._flagged[n] = now
        if not self.frozen and len(self._flagged) >= p.breaker_nodes:
            self.frozen = True
            actions.append(Action(Kind.PAGE, "*", f"{len(self._flagged)} nodes flagged within {p.breaker_window}s: automation frozen"))

        self._held = {n for n in self._held if verdicts[n] == "unhealthy"}
        if p.action is Mode.IGNORE:
            return actions

        # Plan new cordons: budget counts every unschedulable node, human cordons included.
        total = len(names)
        limit = budget(p.max_unavailable, total)
        out = sum(1 for n in names if self.nodes[n].unschedulable)
        self._cordon_times = [t for t in self._cordon_times if now - t < 3600]
        for n in names:
            node = self.nodes[n]
            if verdicts[n] != "unhealthy" or node.unschedulable:
                continue
            if self.frozen and n not in self._acked:
                self._held.add(n)
                actions.append(Action(Kind.HOLD, n, "frozen"))
                continue
            if n in self._held and n not in self._acked:
                actions.append(Action(Kind.HOLD, n, "awaiting human"))
                continue
            if out >= limit:
                actions.append(Action(Kind.HOLD, n, "budget"))
                continue
            if len(self._cordon_times) >= p.max_new_per_hour:
                actions.append(Action(Kind.HOLD, n, "rate"))
                continue
            if p.dry_run:
                actions.append(Action(Kind.WOULD_CORDON, n, node.reason))
                continue
            actions.extend(self._cordon(node, now))
            out += 1

        actions.extend(self._drain_and_ticket(names))
        actions.extend(self._recover(names, verdicts, now))
        return actions

    def _cordon(self, node, now):
        node.unschedulable, node.owner = True, self.policy.name
        node.reason = f"{self.policy.name}: condition False"
        self._cordon_times.append(now)
        self._move(node, State.CORDONED)
        acts = [Action(Kind.CORDON, node.name, node.reason)]
        if node.needs_rma and node.ticket is None:
            node.ticket = self._open_ticket(node.name, "xid history, ecc counters, dcgmi diag")
            node.ticket_open = True
            acts.append(Action(Kind.OPEN_TICKET, node.name, node.ticket))
        return acts

    def _drain_and_ticket(self, names):
        acts = []
        p = self.policy
        for n in names:
            node = self.nodes[n]
            if node.owner != p.name or not node.unschedulable or p.dry_run:
                continue
            if p.action is Mode.CORDON_AND_DRAIN:
                if p.drain_method == "taint":
                    if not node.tainted:
                        node.tainted = True
                        acts.append(Action(Kind.TAINT, n, f"{TAINT_KEY}:NoExecute"))
                else:
                    evictable = node.pods - node.pdb_blocked
                    if evictable > 0:
                        node.pods -= evictable
                        acts.append(Action(Kind.EVICT, n, f"{evictable} pods"))
                    if node.pods > 0 and node.state is State.CORDONED:
                        self._move(node, State.DRAINING)
                if node.state in (State.CORDONED, State.DRAINING) and node.pods == 0:
                    if node.ticket_open:
                        self._move(node, State.REPAIR)
                    elif node.state is State.DRAINING:
                        self._move(node, State.CORDONED)
            elif node.ticket_open and node.state is State.CORDONED:
                self._move(node, State.REPAIR)
        return acts

    def _recover(self, names, verdicts, now):
        acts = []
        p = self.policy
        for n in names:
            node = self.nodes[n]
            # Only nodes this policy cordoned. A human's cordon is the human's to release.
            if node.owner != p.name or not node.unschedulable or p.dry_run:
                continue
            if verdicts[n] != "healthy":
                continue
            if node.ticket is not None and (node.ticket_open or not node.diag_passed):
                continue
            node.unschedulable, node.owner, node.reason = False, None, ""
            node.tainted, node.ticket, node.needs_rma, node.diag_passed = False, None, False, False
            self._flagged.pop(n, None)
            self._move(node, State.HEALTHY)
            acts.append(Action(Kind.UNCORDON, n, "healthy long enough and gate passed"))
        return acts
