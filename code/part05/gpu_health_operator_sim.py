"""Chapter 5.32 model: Pure `Judge`, `Budget`, `Plan`, `evictable`, and
`GPUHealthPolicyReconciler` state machine mirroring `code/gpuhealth/internal/controller/`.

Sources modeled:
- `code/gpuhealth/internal/controller/evaluate.go` (`Judge`, `Budget`, `Plan`,
  `AnnotationOwner = "platform.example.com/cordoned-by"`, `FinalizerName = "platform.example.com/release-cordons"`).
- `code/gpuhealth/internal/controller/gpuhealthpolicy_controller.go` (`Reconcile`,
  `cordon`, `uncordon`, `releaseAll`, `drain`, `evictable`, `updateStatus`).
- Philippe Martin / Stefan Schimanski & Michael Hausenblas, Kubernetes
  Programming with Go / Programming Kubernetes (kubernetes-programming-with-go-
  programming-kubernetes-clients-and-operators-using-go-and-the-kuberne, KPG).
- nvidia-devops (`nvidia-zero-to-hero/volume-10/chapter-01..12` & `labs/lab-01..04`).
"""
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence, Tuple

ANNOTATION_OWNER = "platform.example.com/cordoned-by"
FINALIZER_NAME = "platform.example.com/release-cordons"


@dataclass
class NodeVerdict:
    name: str
    unhealthy: bool = False
    pending: bool = False
    wait_for_sec: float = 0.0
    healthy: bool = False
    healthy_wait_for_sec: float = 0.0
    owned_by_policy: bool = False
    unschedulable: bool = False


def judge_node(
    policy: Mapping[str, Any],
    node: Mapping[str, Any],
    now_sec: float,
) -> NodeVerdict:
    """Mirror `Judge(p, n, now)` in `code/gpuhealth/internal/controller/evaluate.go`."""
    v = NodeVerdict(
        name=str(node["name"]),
        unschedulable=bool(node.get("unschedulable", False)),
        owned_by_policy=(node.get("annotations", {}).get(ANNOTATION_OWNER) == policy["name"]),
    )
    cond_type = policy.get("conditionType", "GPUHealthy")
    cond = None
    for c in node.get("conditions", ()):
        if c["type"] == cond_type:
            cond = c
            break

    unhealthy_for = float(policy.get("unhealthyForSec", 120.0))
    healthy_for = float(policy.get("healthyForSec", 300.0))

    if cond is not None and cond["status"] == "False":
        age = now_sec - float(cond["lastTransitionSec"])
        if age >= unhealthy_for:
            v.unhealthy = True
        else:
            v.pending = True
            v.wait_for_sec = round(unhealthy_for - age, 2)
        return v

    if cond is None:
        return v

    if cond["status"] == "True":
        age = now_sec - float(cond["lastTransitionSec"])
        if age >= healthy_for:
            v.healthy = True
        else:
            v.healthy_wait_for_sec = round(healthy_for - age, 2)
    return v


def compute_budget(max_unavailable: int | str | None, matched: int) -> int:
    """Mirror `Budget(maxUnavailable, matched)` in `evaluate.go`."""
    if max_unavailable is None:
        return matched
    if isinstance(max_unavailable, int):
        v = max_unavailable
    else:
        s = str(max_unavailable).strip()
        try:
            if s.endswith("%"):
                v = int(math.ceil(matched * (float(s[:-1]) / 100.0)))
            else:
                v = int(s)
        except ValueError:
            return 0
    if v < 0:
        return 0
    return min(v, matched)


def plan_remediation(verdicts: Sequence[NodeVerdict], budget: int) -> Tuple[List[str], List[str]]:
    """Mirror `Plan(verdicts, budget)` in `evaluate.go`."""
    unavailable = sum(1 for v in verdicts if v.unschedulable)
    candidates = sorted(v.name for v in verdicts if v.unhealthy and not v.unschedulable)
    room = budget - unavailable
    act: List[str] = []
    blocked: List[str] = []
    for name in candidates:
        if room > 0:
            act.append(name)
            room -= 1
        else:
            blocked.append(name)
    return act, blocked


def is_pod_evictable(pod: Mapping[str, Any]) -> bool:
    """Mirror `evictable(pod)` in `gpuhealthpolicy_controller.go`."""
    if pod.get("phase") in {"Succeeded", "Failed"}:
        return False
    if "kubernetes.io/config.mirror" in pod.get("annotations", {}):
        return False
    for owner in pod.get("ownerReferences", ()):
        if owner.get("kind") == "DaemonSet" and owner.get("controller") is True:
            return False
    return True
