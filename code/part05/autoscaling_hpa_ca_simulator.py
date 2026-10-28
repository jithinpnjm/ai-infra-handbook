"""Chapter 5.23 model: HPAv2 multi-metric replica calculator (with +/-10%
tolerance band, `scaleUp` rate policies, and `scaleDown` stabilization window),
Cluster Autoscaler node scale-down eligibility & blocker evaluator, and Cluster
Overprovisioning negative-priority pause-pod simulator (`PK` Ch. 13).

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 13 ("Autoscaling"):
  * Why decomposing applications enables independent service scaling; when NOT
    to autoscale.
  * HPA formula `ceil(currentReplicas * (currentMetricValue / desiredMetricValue))`,
    10% tolerance band, custom metrics via `prometheus-adapter`, and why not to
    combine HPA and VPA on CPU/memory.
  * VPA (`Recommender`, `Updater`, `Admission Controller`) in `Off` mode for
    right-sizing vs `Recreate`/`Auto` disruption.
  * Cluster Autoscaler (`--nodes=1:10:worker-auto-scaling-group`), scale-down
    blockers, and Cluster Overprovisioning with negative-priority pause pods
    (`Figures 13-6` & `13-7`) to hide node spin-up latency.
"""
import math
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def compute_hpa_desired_replicas(
    *,
    current_replicas: int,
    metric_ratios: Sequence[float],
    min_replicas: int = 2,
    max_replicas: int = 40,
    tolerance: float = 0.10,
    max_scale_up_percent: int = 100,
    max_scale_up_pods: int = 4,
    recent_scale_down_recommendations: Sequence[int] = (),
) -> int:
    """Model Section 2 & PK Ch. 13 HPAv2 replica calculation:
    1. For each metric ratio (`current_value / target_value`), if
       `abs(ratio - 1.0) <= tolerance`, proposed is `current_replicas`, else
       `ceil(current_replicas * ratio)`.
    2. Across multiple metrics, take the MAXIMUM proposed replica count.
    3. On scale-up: cap by `max(current + max_scale_up_pods, ceil(current * (1 + max_scale_up_percent/100)))`
       (`selectPolicy: Max`).
    4. On scale-down: take the MAXIMUM over `recent_scale_down_recommendations`
       plus current raw recommendation (stabilization window).
    5. Clamp to `[min_replicas, max_replicas]`.
    """
    proposals: List[int] = []
    for ratio in metric_ratios:
        if abs(ratio - 1.0) <= tolerance:
            proposals.append(current_replicas)
        else:
            proposals.append(int(math.ceil(current_replicas * ratio)))

    raw_desired = max(proposals) if proposals else current_replicas

    if raw_desired > current_replicas:
        cap_by_pct = int(math.ceil(current_replicas * (1.0 + max_scale_up_percent / 100.0)))
        cap_by_pods = current_replicas + max_scale_up_pods
        scale_up_cap = max(cap_by_pct, cap_by_pods)
        desired = min(raw_desired, scale_up_cap)
    elif raw_desired < current_replicas:
        window_max = max([raw_desired, *recent_scale_down_recommendations])
        desired = min(current_replicas, window_max)
    else:
        desired = current_replicas

    return max(min_replicas, min(max_replicas, desired))


def evaluate_ca_node_scale_down(
    *,
    node_utilization_ratio: float,
    unneeded_minutes: float,
    pods_on_node: Sequence[Mapping[str, Any]],
    threshold: float = 0.50,
    required_unneeded_minutes: float = 10.0,
) -> Tuple[bool, List[str]]:
    """Model Section 5 Cluster Autoscaler node scale-down eligibility and blockers."""
    blockers: List[str] = []
    if node_utilization_ratio >= threshold:
        blockers.append(f"node utilization {node_utilization_ratio:.2f} >= threshold {threshold:.2f}")
    if unneeded_minutes < required_unneeded_minutes:
        blockers.append(f"unneeded duration {unneeded_minutes}m < required {required_unneeded_minutes}m")

    for pod in pods_on_node:
        name = str(pod["name"])
        if pod.get("is_daemonset", False):
            continue
        if pod.get("safe_to_evict") is False:
            blockers.append(f"{name}: annotated safe-to-evict=false")
        if not pod.get("has_controller", True):
            blockers.append(f"{name}: standalone pod not managed by a controller")
        if pod.get("has_local_storage", False) and pod.get("safe_to_evict") is not True:
            blockers.append(f"{name}: uses local storage (emptyDir/hostPath) without safe-to-evict=true")
        if int(pod.get("pdb_disruptions_allowed", 1)) <= 0:
            blockers.append(f"{name}: PodDisruptionBudget has disruptionsAllowed=0")

    return (len(blockers) == 0), blockers


def simulate_overprovisioning_pause_pods(
    *,
    ready_gpu_nodes: int,
    pause_pods_running: int,
    incoming_high_prio_gpu_pods: int,
) -> Dict[str, int]:
    """Model Section 5 & PK Ch. 13 Figures 13-6 & 13-7 Cluster Overprovisioning:
    - Low-priority (`priority: -10`) pause pods hold warm GPU nodes ready.
    - When `incoming_high_prio_gpu_pods` arrive, they immediately preempt
      `min(pause_pods_running, incoming_high_prio_gpu_pods)` pause pods (`0s`
      node provisioning wait!), and the preempted pause pods become `Pending`,
      triggering Cluster Autoscaler to spin up replacement nodes in the background.
    """
    instantly_scheduled = min(pause_pods_running, incoming_high_prio_gpu_pods)
    waiting_for_cold_node = incoming_high_prio_gpu_pods - instantly_scheduled
    pending_pause_pods_triggering_ca = instantly_scheduled
    return {
        "instantly_scheduled_high_prio": instantly_scheduled,
        "waiting_for_cold_node": waiting_for_cold_node,
        "ca_background_nodes_requested": pending_pause_pods_triggering_ca,
        "target_total_nodes": ready_gpu_nodes + pending_pause_pods_triggering_ca,
    }
