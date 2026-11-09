# code/part20/failure_model.py
"""Scoring engine for the LLM serving failure-signature classifier.

Reading keys are either a vLLM metric name with a derivation after "@",
for example "vllm:time_to_first_token_seconds@p99", or a "sig:" signal that
does not come from vLLM (probe restarts, Xid codes, replica counts).
"@rate" means rate() over the exported "_total" counter series.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

FINISH_REASONS = ("stop", "length", "abort", "error", "repetition")


class Readings:
    """Current readings plus an optional baseline taken from a calm period."""

    def __init__(self, current: dict, baseline: Optional[dict] = None):
        self.current = dict(current)
        self.baseline = dict(baseline or {})
        self.missing: set = set()

    def get(self, key: str) -> Any:
        if key not in self.current:
            self.missing.add(key)
            return None
        return self.current[key]

    def up(self, key: str, factor: float) -> Optional[bool]:
        """True when current >= factor * baseline. None if either is unknown."""
        now, base = self.get(key), self.baseline.get(key)
        if now is None or not base:
            return None
        return now >= factor * base

    def finish_share(self, reason: str, baseline: bool = False) -> Optional[float]:
        src = self.baseline if baseline else self.current
        rates = {r: src.get(f"vllm:request_success@rate:{r}") for r in FINISH_REASONS}
        if all(v is None for v in rates.values()):
            return None
        total = sum(v or 0.0 for v in rates.values())
        return (rates[reason] or 0.0) / total if total else None


Check = tuple  # (weight, description, fn(Readings) -> Optional[bool])


@dataclass(frozen=True)
class Rule:
    cause: str
    confirm: str
    mitigate_now: str
    fix_later: str
    checks: tuple = field(default_factory=tuple)  # first check is the anchor


@dataclass
class Hypothesis:
    cause: str
    score: float
    evidence: list
    unknown: list
    confirm: str
    mitigate_now: str
    fix_later: str


def evaluate(rule: Rule, r: Readings) -> Optional[Hypothesis]:
    total = sum(w for w, _, _ in rule.checks)
    hit, evidence, unknown = 0.0, [], []
    for i, (weight, text, fn) in enumerate(rule.checks):
        ok = fn(r)
        if i == 0 and not ok:
            return None  # the anchor symptom must be present
        if ok is None:
            unknown.append(text)
        elif ok:
            hit += weight
            evidence.append(text)
    if not evidence:
        return None
    return Hypothesis(rule.cause, round(hit / total, 3), evidence, unknown,
                      rule.confirm, rule.mitigate_now, rule.fix_later)


def rank(rules: list, current: dict, baseline: Optional[dict] = None) -> list:
    """Return hypotheses sorted by score, best first. Ties break on cause name."""
    r = Readings(current, baseline)
    found = [h for h in (evaluate(rule, r) for rule in rules) if h]
    return sorted(found, key=lambda h: (-h.score, h.cause))
