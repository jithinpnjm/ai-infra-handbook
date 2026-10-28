"""Chapter 5.20 model: Kubernetes version skew & upgrade step validator,
`etcdutl snapshot restore` cluster topology & `PK` Ch. 2 etcd upgrade risk
evaluator, and AI training/inference RPO/RTO evaluator.

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 2 ("Deployment Models": in-place vs
  subtractive vs additive dedicated etcd node upgrades, and blue-green cluster
  upgrades).
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 3.
- NVIDIA Base Command Manager 11 Containerization Manual (bcm11-containerization,
  Appendix C: "Kubernetes Upgrade On An Air-gapped BCM Cluster").
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def parse_minor(ver: str) -> int:
    """Parse '1.30.4' or 'v1.30' into integer minor version `30`."""
    clean = ver.lstrip("v").split(".")
    if int(clean[0]) != 1:
        raise ValueError(f"expected major version 1, got {ver!r}")
    return int(clean[1])


def validate_k8s_version_skew(
    *,
    apiserver_versions: Sequence[str],
    controller_manager_version: str,
    scheduler_version: str,
    kubelet_versions: Sequence[str],
    kubectl_version: str,
) -> Tuple[bool, List[str]]:
    """Model Section 1 Kubernetes Version Skew Policy:
    - HA `kube-apiserver` instances: max skew <= 1 minor version.
    - `kube-controller-manager` and `kube-scheduler`: must not be newer than the
      highest `kube-apiserver`, and at most 1 minor older than the lowest `kube-apiserver`.
    - `kubelet`: must not be newer than `kube-apiserver`, and at most 3 minors older.
    - `kubectl`: within +/- 1 minor of `kube-apiserver`.
    """
    errors: List[str] = []
    api_minors = [parse_minor(v) for v in apiserver_versions]
    max_api, min_api = max(api_minors), min(api_minors)

    if (max_api - min_api) > 1:
        errors.append(f"kube-apiserver instances skew by >1 minor: {min_api}..{max_api}")

    for name, ver in (("kube-controller-manager", controller_manager_version), ("kube-scheduler", scheduler_version)):
        m = parse_minor(ver)
        if m > max_api:
            errors.append(f"{name} (1.{m}) cannot be newer than kube-apiserver (1.{max_api})")
        if (min_api - m) > 1:
            errors.append(f"{name} (1.{m}) is >1 minor older than kube-apiserver (1.{min_api})")

    for idx, kv in enumerate(kubelet_versions):
        km = parse_minor(kv)
        if km > min_api:
            errors.append(f"kubelet[{idx}] (1.{km}) cannot be newer than kube-apiserver (1.{min_api})")
        if (max_api - km) > 3:
            errors.append(f"kubelet[{idx}] (1.{km}) is >3 minors older than kube-apiserver (1.{max_api})")

    kctl = parse_minor(kubectl_version)
    if kctl > (max_api + 1) or kctl < (min_api - 1):
        errors.append(f"kubectl (1.{kctl}) outside +/-1 minor skew of kube-apiserver (1.{min_api}..1.{max_api})")

    return (len(errors) == 0), errors


def evaluate_etcd_upgrade_quorum_safety(
    initial_members: int,
    strategy: str,
) -> Dict[str, Any]:
    """Model PK Ch. 2 dedicated etcd upgrade strategies on a 3-node cluster:
    - `subtractive_remove_first`: removes 1 member (`3 -> 2`, quorum = 2). If 1 of
      the remaining 2 members hiccups during the upgrade, quorum is lost (`0`
      remaining failure tolerance during maintenance)!
    - `additive_learner_first` or `in_place_rolling`: maintains 3 members (adding
      a 4th learner before promoting/removing, or upgrading 1 member in place),
      keeping quorum = 2 with 2 healthy voting members throughout.
    """
    if strategy == "subtractive_remove_first":
        active_voting = initial_members - 1
        quorum = (active_voting // 2) + 1
        fault_tolerance_during_maint = active_voting - quorum
        return {
            "active_voting_during_step": active_voting,
            "quorum_during_step": quorum,
            "fault_tolerance_during_step": fault_tolerance_during_maint,
            "safe": (fault_tolerance_during_maint >= 1 and active_voting >= 3),
        }
    if strategy in {"additive_learner_first", "in_place_rolling"}:
        quorum = (initial_members // 2) + 1
        return {
            "active_voting_during_step": initial_members,
            "quorum_during_step": quorum,
            "fault_tolerance_during_step": initial_members - quorum,
            "safe": True,
        }
    raise ValueError(f"unknown strategy {strategy!r}")


def evaluate_dr_rpo_rto(
    *,
    checkpoint_interval_min: float,
    offsite_sync_lag_min: float,
    target_rpo_min: float,
    cluster_restore_min: float,
    job_reload_min: float,
    target_rto_min: float,
) -> Dict[str, Any]:
    """Model Section 7 training/inference DR RPO and RTO compliance."""
    worst_case_rpo = round(checkpoint_interval_min + offsite_sync_lag_min, 2)
    total_rto = round(cluster_restore_min + job_reload_min, 2)
    return {
        "achieved_rpo_min": worst_case_rpo,
        "achieved_rto_min": total_rto,
        "rpo_met": (worst_case_rpo <= target_rpo_min),
        "rto_met": (total_rto <= target_rto_min),
    }
