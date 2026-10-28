"""Chapter 5.34 model: GKE GPU node pool configuration & MIG/time-sharing
resource calculator (`GAK` Ch. 3), GKE GPU capacity error classifier
(`QUOTA_EXCEEDED` vs `ZONE_RESOURCE_POOL_EXHAUSTED` stockout), and GPU node
pool upgrade surge/unavailable validator.

Sources modeled:
- Google Cloud SDK (`gcloud` 584.0.0) `container clusters create` &
  `container node-pools create` flag specifications.
- Roland Huss, Courtney Pacheco & Bryanoster, Generative AI on Kubernetes
  (generative-ai-on-kubernetes, GAK), Chapter 3 ("Kubernetes and GPUs":
  decimal GB vs binary GiB `80 GB ~ 74.5 GiB`, GFD labels `nvidia.com/gpu.product`,
  `nvidia.com/gpu.memory`, `nvidia.com/mig.strategy=single|mixed`, time-slicing
  `renameByDefault: true` `nvidia.com/gpu.shared`, and DRA `ResourceClaimTemplate`).
- Scalable Kubernetes Infrastructure for AI Platforms (scalable-kubernetes-
  infrastructure-for-ai-platforms, SKI) & Kubernetes for Generative AI Solutions
  (kubernetes-for-generative-ai-solutions, K8GS).
"""
from typing import Any, Dict, List, Mapping, Tuple


def evaluate_gke_gpu_node_pool_config(cfg: Mapping[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
    """Model Section 4, 7, & 8 GKE GPU node-pool configuration and GAK Ch. 3
    MIG / time-sharing resource calculations.
    """
    errors: List[str] = []
    image_type = str(cfg.get("image_type", "COS_CONTAINERD"))
    driver_ver = str(cfg.get("gpu_driver_version", "default"))
    if driver_ver not in {"default", "latest", "disabled"}:
        errors.append(f"invalid gpu_driver_version {driver_ver!r}")
    if driver_ver == "latest" and not image_type.startswith("COS"):
        errors.append("gpu-driver-version=latest is only supported on Container-Optimized OS (COS)")

    if cfg.get("gpu_operator_manages_driver", False) and driver_ver != "disabled":
        errors.append("when GPU Operator manages drivers on GKE, gpu-driver-version must be 'disabled'")

    add_nets = int(cfg.get("additional_node_networks", 0))
    if add_nets > 7:
        errors.append(f"--additional-node-network supports at most 7 networks, got {add_nets}")

    if cfg.get("reservation_affinity") == "specific" and not cfg.get("reservation_name"):
        errors.append("--reservation-affinity=specific requires --reservation=<name>")

    physical_gpus = int(cfg.get("gpu_count", 8))
    sharing_strategy = cfg.get("gpu_sharing_strategy")
    mig_slices_per_gpu = int(cfg.get("mig_slices_per_gpu", 1))

    if sharing_strategy == "time-sharing":
        clients = int(cfg.get("max_shared_clients_per_gpu", 2))
        allocatable_units = physical_gpus * clients
        isolation = "weak (shared HBM memory and fault fate)"
    elif mig_slices_per_gpu > 1:
        allocatable_units = physical_gpus * mig_slices_per_gpu
        isolation = "strong (hardware-isolated SMs, HBM memory, and page tables)"
    else:
        allocatable_units = physical_gpus
        isolation = "dedicated whole physical GPUs"

    return (
        len(errors) == 0,
        {"allocatable_gpu_units_per_node": allocatable_units, "isolation": isolation},
        errors,
    )


def classify_gke_gpu_capacity_error(error_msg: str) -> Dict[str, str]:
    """Model Section 5 & 12 GKE GPU capacity failure classification."""
    if "QUOTA_EXCEEDED" in error_msg:
        return {
            "category": "project_quota",
            "remediation": "Request regional/global GPU quota increase (Plus accompanying CPU/RAM/SSD quota for the machine shape)",
        }
    if "ZONE_RESOURCE_POOL_EXHAUSTED" in error_msg:
        return {
            "category": "zone_stockout",
            "remediation": "Cloud zone has no free physical hardware; use another zone (--location-policy=ANY), a Reservation, or Flex-start (DWS)",
        }
    return {
        "category": "scheduler_or_autoscaler_constraint",
        "remediation": "Inspect Pod tolerations (nvidia.com/gpu=present:NoSchedule), nodeSelector, and node-pool max-nodes limit",
    }


def validate_gpu_pool_upgrade_surge(
    *,
    pool_nodes: int,
    spare_quota_or_reservation_nodes: int,
    max_surge_upgrade: int,
    max_unavailable_upgrade: int,
) -> Tuple[bool, str]:
    """Model Section 9 GPU node pool upgrade settings when spare quota/reservation is 0."""
    if max_surge_upgrade > spare_quota_or_reservation_nodes:
        return (
            False,
            f"max-surge-upgrade={max_surge_upgrade} will stall because only {spare_quota_or_reservation_nodes} spare GPU nodes exist in quota/reservation; set max-surge-upgrade=0 and max-unavailable-upgrade>=1",
        )
    if max_surge_upgrade == 0 and max_unavailable_upgrade == 0:
        return False, "both max-surge-upgrade and max-unavailable-upgrade cannot be 0"
    return True, f"upgrade can proceed across {pool_nodes} nodes"
