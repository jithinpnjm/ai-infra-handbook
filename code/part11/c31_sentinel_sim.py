"""Staged-adoption and circuit-breaker model of an NVSentinel-style pipeline (11.31).

Behaviour modelled, each from the NVSentinel docs read on 2026-11-11:
  * monitoring only by default: conditions are published, nothing is cordoned;
  * stages are enabled one at a time: quarantine (cordon), drain, remediate;
  * a dry run logs the action and changes nothing;
  * a circuit breaker trips when cordons in the window reach
    ceil(gpu_nodes * percentage / 100); a tripped breaker halts every event,
    healthy events included, and only a human reset clears it;
  * CONTACT_SUPPORT events are never remediated automatically.
Time is a plain number of seconds. This is a teaching model, not the Go code.
"""
import math
from dataclasses import dataclass, field


@dataclass
class Config:
    gpu_nodes: int
    quarantine: bool = False
    drain: bool = False
    remediate: bool = False
    dry_run: bool = False
    breaker_enabled: bool = True
    breaker_percentage: int = 50
    breaker_window_s: int = 300


@dataclass
class Sentinel:
    cfg: Config
    cordoned: set = field(default_factory=set)
    conditions: dict = field(default_factory=dict)
    actions: list = field(default_factory=list)
    tripped: bool = False
    _cordon_times: list = field(default_factory=list)

    def trip_threshold(self):
        return math.ceil(self.cfg.gpu_nodes * self.cfg.breaker_percentage / 100)

    def reset_breaker(self):
        self.tripped = False
        self._cordon_times.clear()

    def handle(self, t, node, healthy, fatal=True, action="NONE"):
        """Process one health event at time t and return the actions taken."""
        # Conditions keep updating even while the breaker is tripped.
        self.conditions[node] = "healthy" if healthy else "unhealthy"
        if self.tripped:
            return self._log(t, node, "halted_by_breaker")
        if healthy:
            if node in self.cordoned and self.cfg.quarantine and not self.cfg.dry_run:
                self.cordoned.discard(node)
                return self._log(t, node, "uncordon")
            return []
        if not (self.cfg.quarantine and fatal):
            return self._log(t, node, "report_only")
        if self.cfg.dry_run:
            return self._log(t, node, "would_cordon")
        if node in self.cordoned:
            return []
        if self.cfg.breaker_enabled and self._would_trip(t):
            self.tripped = True
            return self._log(t, node, "breaker_tripped")
        self.cordoned.add(node)
        self._cordon_times.append(t)
        out = self._log(t, node, "cordon")
        if self.cfg.drain:
            out += self._log(t, node, "drain")
        if action == "CONTACT_SUPPORT":
            out += self._log(t, node, "page_human")
        elif self.cfg.remediate and self.cfg.drain:
            out += self._log(t, node, "remediate")
        return out

    def _would_trip(self, t):
        recent = [x for x in self._cordon_times if t - x < self.cfg.breaker_window_s]
        return len(recent) + 1 >= self.trip_threshold()

    def _log(self, t, node, kind):
        self.actions.append((t, node, kind))
        return [(t, node, kind)]
