"""Chapter 5.17 model: `StorageClass` `volumeBindingMode` (`Immediate` vs
`WaitForFirstConsumer`) zonal GPU placement evaluator (`PK` Ch. 4), CSI
`VolumeAttachment` RWO/RWOP/RWX `Multi-Attach` checker, and AI checkpoint /
weight-loading throughput calculator (`KUR` Ch. 16, `PK` Ch. 4, `volume-03/02`).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 16
  ("Integrating Storage Solutions and Kubernetes"): external databases via
  `ExternalName` and selector-less Services + `Endpoints`, singleton MySQL with
  PVC, and MongoDB 3-replica `StatefulSet` + Headless Service (`mongo-0.mongo`
  through `mongo-2.mongo`) + `volumeClaimTemplates` + `init-mongo` ConfigMap.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 4 ("Container Storage"): Block vs File vs
  Object storage, in-tree to out-of-tree CSI migration, `CSIDriver` & `CSINode`,
  `StorageClass` `Immediate` vs `WaitForFirstConsumer` (`blkid` & `ResizeFS`),
  and `VolumeSnapshot` / `VolumeSnapshotClass`.
- nvidia-devops (`volume-03/02-k8s-node-storage-masterclass.md`).
"""
from typing import Dict, List, Mapping, Set, Tuple


def evaluate_zonal_pvc_binding(
    *,
    binding_mode: str,
    Immediate_default_zone: str,
    gpu_available_zones: Set[str],
) -> Tuple[bool, str, str]:
    """Model Section 2 & PK Ch. 4 `Immediate` vs `WaitForFirstConsumer` (`WFFC`)
    for zonal block storage when GPU capacity only exists in specific zones:
    - Under `Immediate`, the CSI provisioner creates the volume immediately in
      `Immediate_default_zone` before any Pod is scheduled; if that zone has no
      free GPUs (`Immediate_default_zone not in gpu_available_zones`), the GPU
      Pod is unschedulable (`node(s) had volume node affinity conflict`)!
    - Under `WaitForFirstConsumer`, provisioning waits until `kube-scheduler`
      picks a node in `gpu_available_zones` and sets `volume.kubernetes.io/selected-node`.
    """
    if binding_mode == "Immediate":
        if Immediate_default_zone not in gpu_available_zones:
            return (
                False,
                Immediate_default_zone,
                f"Unschedulable: PVC provisioned in {Immediate_default_zone!r}, but GPUs only in {sorted(gpu_available_zones)}",
            )
        return True, Immediate_default_zone, "scheduled"

    if binding_mode == "WaitForFirstConsumer":
        if not gpu_available_zones:
            return False, "", "Unschedulable: no GPU zones available"
        chosen_zone = sorted(gpu_available_zones)[0]
        return True, chosen_zone, f"provisioned in {chosen_zone!r} after scheduler selected GPU node"

    raise ValueError(f"unknown volumeBindingMode {binding_mode!r}")


def check_csi_volume_attachment(
    *,
    access_mode: str,
    currently_attached_nodes: Set[str],
    currently_mounted_pods: Set[str],
    requesting_node: str,
    requesting_pod: str,
) -> Tuple[bool, str]:
    """Model Section 2 & 3 access-mode attachment rules:
    - `ReadWriteOnce` (`RWO`): allows multiple pods on the SAME node, but
      rejects attaching to a second node with `Multi-Attach error`!
    - `ReadWriteOncePod` (`RWOP`): allows only a SINGLE pod on a single node!
    - `ReadWriteMany` (`RWX`) / `ReadOnlyMany` (`ROX`): allows multiple nodes
      and multiple pods concurrently.
    """
    if access_mode == "ReadWriteOnce":
        other_nodes = currently_attached_nodes - {requesting_node}
        if other_nodes:
            return False, f"Multi-Attach error: RWO volume already exclusively attached to {sorted(other_nodes)}"
        return True, "attached (RWO)"

    if access_mode == "ReadWriteOncePod":
        other_pods = currently_mounted_pods - {requesting_pod}
        if other_pods:
            return False, f"RWOP conflict: volume already mounted by pod {sorted(other_pods)}"
        return True, "attached (RWOP)"

    if access_mode in {"ReadWriteMany", "ReadOnlyMany"}:
        return True, f"attached ({access_mode})"

    raise ValueError(f"unknown access_mode {access_mode!r}")


def compute_checkpoint_and_weight_timings(
    *,
    checkpoint_size_gb: float,
    aggregate_write_gb_per_sec: float,
    model_weights_size_gb: float,
    per_pod_read_gb_per_sec: float,
) -> Dict[str, float]:
    """Model Section 5 checkpoint stall time and inference cold-start weight load time."""
    return {
        "checkpoint_stall_sec": round(checkpoint_size_gb / aggregate_write_gb_per_sec, 2),
        "weight_load_cold_start_sec": round(model_weights_size_gb / per_pod_read_gb_per_sec, 2),
    }
