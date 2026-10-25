"""Chapter 11.5 — GPU Operator installation, configuration and upgrades.

Deterministic models for:
1. 7-criterion production installation acceptance gate (`volume-10/chapter-10`),
   including UUID correlation between validation Pod (`GPU-3a91...`) and
   DCGM Exporter (`DCGM_FI_DEV_GPU_UTIL` on port `9400`).
2. Canary & progressive batch sizing model for a `120`-node fleet (`4` hardware
   batches of `30` nodes, `8` GPUs/node = `960` GPUs: `8`-node canary -> `12` -> `24`
   -> `76`, with `24 * 8 = 192 / 960 = 20.0%` blast radius on batch failure).
3. Controlled upgrade and `Recheck` rollback state machine (`Lab 04`: `24.6.0` rev 1
   -> `24.9.1` rev 2 -> `helm rollback` rev 1, catching host-state divergence where
   `helm rollback` succeeds but `allocatable` stays `0`).
4. 6-layer post-upgrade troubleshooting classifier (`volume-10/chapter-11` & `12`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class PoolAcceptanceEvidence:
    """Evidence collected across the 7 acceptance criteria of Volume 10 Chapter 10."""

    helm_status: str
    cluster_policy_state: str
    total_canary_nodes: int
    driver_ready_nodes: int
    capacity_gpus: int
    allocatable_gpus: int
    labels_and_taints_verified: bool
    validation_pod_marker: str
    validation_pod_uuid: str
    dcgm_metric_series_count: int
    dcgm_metric_uuid: str
    drain_reboot_return_passed: bool


def evaluate_pool_acceptance(ev: PoolAcceptanceEvidence) -> Dict[str, object]:
    """Evaluate all 7 production installation acceptance criteria."""
    c1_driver = (
        ev.cluster_policy_state == "ready"
        and ev.driver_ready_nodes == ev.total_canary_nodes
    )
    c2_runtime = ev.validation_pod_marker in (
        "CUDA_VALIDATED",
        "GPU_OPERATOR_VALIDATED",
        "GPU_UPGRADE_VALIDATED",
    )
    c3_allocatable = (
        ev.capacity_gpus > 0 and ev.allocatable_gpus == ev.capacity_gpus
    )
    c4_labels_taints = ev.labels_and_taints_verified
    c5_workload = c2_runtime and bool(ev.validation_pod_uuid)
    c6_telemetry = (
        ev.dcgm_metric_series_count > 0
        and ev.dcgm_metric_uuid == ev.validation_pod_uuid
    )
    c7_lifecycle = ev.drain_reboot_return_passed

    criteria = {
        "1_driver_and_operands_ready": c1_driver,
        "2_runtime_creates_cuda_container": c2_runtime,
        "3_allocatable_matches_capacity": c3_allocatable,
        "4_labels_and_taints_verified": c4_labels_taints,
        "5_workload_functional_test": c5_workload,
        "6_dcgm_telemetry_uuid_matched": c6_telemetry,
        "7_drain_reboot_return_verified": c7_lifecycle,
    }
    failed_gates = [k for k, v in criteria.items() if not v]
    return {
        "helm_deployed": ev.helm_status == "deployed",
        "criteria": criteria,
        "failed_gates": failed_gates,
        "pool_accepted": len(failed_gates) == 0,
    }


def plan_canary_and_progressive_batches(
    total_nodes: int = 120,
    hardware_batches: int = 4,
    canary_nodes_per_hw_batch: int = 2,
    first_rollout_pct: float = 10.0,
    gpus_per_node: int = 8,
) -> Dict[str, object]:
    """Compute the V10 Ch 11 canary and doubling rollout plan for a 120-node fleet."""
    nodes_per_hw_batch = total_nodes // hardware_batches
    canary_nodes = hardware_batches * canary_nodes_per_hw_batch
    canary_pct = round((canary_nodes / total_nodes) * 100.0, 2)
    canary_pct_rounded = round(canary_pct)

    batch1_nodes = int(round(total_nodes * (first_rollout_pct / 100.0)))
    batch2_nodes = batch1_nodes * 2
    remaining_nodes = total_nodes - (canary_nodes + batch1_nodes + batch2_nodes)

    total_fleet_gpus = total_nodes * gpus_per_node
    batch2_gpus_at_risk = batch2_nodes * gpus_per_node
    batch2_blast_radius_pct = round((batch2_gpus_at_risk / total_fleet_gpus) * 100.0, 2)

    return {
        "nodes_per_hw_batch": nodes_per_hw_batch,
        "canary_nodes": canary_nodes,
        "canary_pct": canary_pct,
        "canary_pct_rounded": canary_pct_rounded,
        "wave_schedule_nodes": [canary_nodes, batch1_nodes, batch2_nodes, remaining_nodes],
        "batch1_remaining_serving_pct": round(
            ((total_nodes - batch1_nodes) / total_nodes) * 100.0, 2
        ),
        "total_fleet_gpus": total_fleet_gpus,
        "batch2_gpus_at_risk": batch2_gpus_at_risk,
        "batch2_blast_radius_pct": batch2_blast_radius_pct,
    }


@dataclass(frozen=True)
class UpgradeAndRollbackState:
    """State of a canary node during Lab 04 upgrade and rollback verification."""

    prior_revision: int = 1
    prior_chart: str = "gpu-operator-24.6.0"
    target_revision: int = 2
    target_chart: str = "gpu-operator-24.9.1"
    baseline_allocatable: int = 8
    post_upgrade_allocatable: int = 8
    post_upgrade_workload_ok: bool = True
    post_upgrade_dcgm_ok: bool = True
    new_xid_or_kernel_errors: bool = False
    helm_rollback_succeeded: bool = False
    post_rollback_allocatable: int = 8
    post_rollback_workload_ok: bool = True


def evaluate_upgrade_or_rollback_gate(state: UpgradeAndRollbackState) -> Dict[str, object]:
    """Evaluate Lab 04 upgrade gate (`G`) and rollback verification gate (`Recheck`)."""
    upgrade_passed = (
        state.post_upgrade_allocatable == state.baseline_allocatable
        and state.post_upgrade_workload_ok
        and state.post_upgrade_dcgm_ok
        and (not state.new_xid_or_kernel_errors)
    )
    if upgrade_passed:
        return {
            "upgrade_gate": "pass",
            "action": "uncordon_canary_and_proceed_to_staged_rollout",
            "rollback_recheck_gate": "not_needed",
        }

    # Upgrade failed -> check whether helm rollback restored host + Kubernetes state
    if not state.helm_rollback_succeeded:
        return {
            "upgrade_gate": "fail",
            "action": "trigger_helm_rollback_to_revision_1",
            "rollback_recheck_gate": "pending",
        }

    recheck_passed = (
        state.post_rollback_allocatable == state.baseline_allocatable
        and state.post_rollback_workload_ok
    )
    if recheck_passed:
        return {
            "upgrade_gate": "fail",
            "action": "rollback_verified_healthy_uncordon_after_review",
            "rollback_recheck_gate": "pass",
        }
    return {
        "upgrade_gate": "fail",
        "action": "keep_node_cordoned_revert_host_driver_or_node_image_and_escalate",
        "rollback_recheck_gate": "fail_host_state_diverged",
    }


def diagnose_installation_or_upgrade_symptom(
    driver_pod_log: str,
    pod_start_error: str,
    allocatable_gpus: Optional[int],
    dcgm_series_count: int,
) -> Dict[str, str]:
    """Classify the concrete troubleshooting scenarios from V10 Ch 10 & Ch 11."""
    if "Key was rejected by service" in driver_pod_log:
        return {
            "boundary": "secure_boot_mok_signing",
            "fix": "Enroll driver signing key in MOK on gpu-node-04 or use signed precompiled driver",
        }
    if "open /run/nvidia/driver/dev/nvidia0: no such file or directory" in pod_start_error:
        return {
            "boundary": "pod_start_runtime_injection",
            "fix": "Inspect toolkit/CDI mount path (/run/nvidia/driver/dev/nvidia0 missing before entrypoint)",
        }
    if allocatable_gpus is None or allocatable_gpus == 0:
        return {
            "boundary": "device_plugin_or_kubelet_registration",
            "fix": "Compare per-node allocatable (e.g. gpu-node-11=0 vs gpu-node-12=8) and inspect plugin registration",
        }
    if dcgm_series_count == 0:
        return {
            "boundary": "observability_dcgm_scrape_path",
            "fix": "Check dcgm-exporter access to driver/NVML socket and Prometheus target health on port 9400",
        }
    return {
        "boundary": "healthy",
        "fix": "All installation and telemetry checks passed",
    }
