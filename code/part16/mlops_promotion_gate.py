from dataclasses import dataclass
from typing import Callable

@dataclass
class Run:
    run_id: str
    metrics: dict[str, float]
    data_snapshot_id: str
    code_commit: str
    seed: int

@dataclass
class GateResult:
    passed: bool
    reasons: list[str]

def promotion_gate(
    candidate: Run,
    baseline: Run,
    rules: dict,
) -> GateResult:
    reasons = []
    # 1. Did the candidate beat the baseline on the primary metric?
    primary = rules["primary_metric"]
    if candidate.metrics[primary] < baseline.metrics[primary]:
        reasons.append(
            f"primary metric regressed: {candidate.metrics[primary]} < {baseline.metrics[primary]}"
        )
    # 2. Did any guardrail metric violate a threshold?
    for metric, threshold in rules["min_metrics"].items():
        if candidate.metrics[metric] < threshold:
            reasons.append(
                f"guardrail {metric} below floor: {candidate.metrics[metric]} < {threshold}"
            )
    # 3. Did the seed reproduce?
    if candidate.seed != rules.get("required_seed"):
        reasons.append("seed not pinned to required value")
    return GateResult(passed=not reasons, reasons=reasons)

def load_artifacts(candidate_path, baseline_path, policy_path):
    import json
    return (Run(**json.load(open(candidate_path))), Run(**json.load(open(baseline_path))), json.load(open(policy_path)))

def write_audit_log(candidate, baseline, result):
    import mlplat_local as P
    P.audit("gate_passed", candidate=candidate.run_id, baseline=baseline.run_id)

def write_registry(candidate, stage):
    import mlplat_local as P
    P.register("churn-model", len(P.load("registry.json", {}).get("churn-model", {})) + 1, candidate.run_id, candidate.metrics, stage=stage)

def promote(candidate_path: str, baseline_path: str, policy_path: str) -> int:
    candidate, baseline, rules = load_artifacts(candidate_path, baseline_path, policy_path)
    result = promotion_gate(candidate, baseline, rules)
    if not result.passed:
        print("PROMOTION BLOCKED:")
        for r in result.reasons:
            print(f"  - {r}")
        return 1
    # Log the decision to an immutable audit trail before writing to the registry
    write_audit_log(candidate, baseline, result)
    write_registry(candidate, stage="staging")
    return 0
