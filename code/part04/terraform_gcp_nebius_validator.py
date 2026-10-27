"""Chapter 4.24 model: GCP GPU VM & GKE node-pool validator (`TERMINATE`
host maintenance, jumbo `mtu = 8896`, `max_surge = 0` / `max_unavailable = 1`
for reserved GPU pools, `reservation_affinity`), multi-NIC GPU VPC subnet
planner, and Nebius InfiniBand `gpu_cluster` fabric membership verifier.

Sources modeled:
- Yevgeniy Brikman, Terraform: Up and Running, 3rd ed. (terraform-up-and-running-
  3rd-edition, TUR).
- volume-10/05-terraform-for-infrastructure-as-code.md.
- GCP Compute Engine / GKE GPU documentation & Nebius Terraform provider model.
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def validate_gcp_gpu_node_pool(cfg: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    """Validate Section 3 & 4 GCP GPU VM / GKE node-pool invariants:
    1. `on_host_maintenance` must be `"TERMINATE"` (live migration unsupported for GPUs).
    2. VPC `mtu` should be `8896` (or `8244`) for high-throughput training fabrics.
    3. For reserved/scarce GPU pools, `max_surge` must be `0` and `max_unavailable >= 1`
       so upgrades do not deadlock waiting for extra nonexistent GPU quota.
    4. GPU pools must carry `nvidia.com/gpu=present:NO_SCHEDULE` taint.
    5. When `reservation_name` is set, `consume_reservation_type` must be
       `"SPECIFIC_RESERVATION"`.
    """
    errors: List[str] = []
    if cfg.get("on_host_maintenance") != "TERMINATE":
        errors.append("GPU instances require scheduling.on_host_maintenance = 'TERMINATE'")
    if int(cfg.get("vpc_mtu", 1460)) not in {8244, 8896}:
        errors.append("Training VPC MTU should be 8896 (or 8244) for jumbo frames")
    if cfg.get("has_reservation", False):
        if int(cfg.get("max_surge", 1)) != 0 or int(cfg.get("max_unavailable", 0)) < 1:
            errors.append("Reserved GPU pools should set max_surge=0 and max_unavailable>=1")
        if cfg.get("consume_reservation_type") != "SPECIFIC_RESERVATION":
            errors.append("Reserved GPU pools must set consume_reservation_type='SPECIFIC_RESERVATION'")
    taints = cfg.get("taints", [])
    if not any(t.get("key") == "nvidia.com/gpu" and t.get("effect") == "NO_SCHEDULE" for t in taints):
        errors.append("GPU node pool missing nvidia.com/gpu:NO_SCHEDULE taint")
    return (len(errors) == 0), errors


def generate_multi_nic_gpu_subnets(base_second_octet: int = 40, gpu_nic_count: int = 4) -> List[Dict[str, object]]:
    """Model Section 2 multi-NIC GPU VPC layout (e.g., 4 or 8 dedicated GPU-to-GPU
    VPCs alongside the primary management VPC, each with non-overlapping /20 CIDR
    and MTU 8896).
    """
    vpcs: List[Dict[str, object]] = []
    for idx in range(gpu_nic_count):
        vpcs.append(
            {
                "vpc_name": f"gpu-rail-{idx}",
                "subnet_cidr": f"10.{base_second_octet + idx}.0.0/20",
                "mtu": 8896,
            }
        )
    return vpcs


def validate_nebius_gpu_fabric_membership(
    instances: Sequence[Mapping[str, Any]],
    expected_fabric_id: str,
) -> List[str]:
    """Model Section 7 Nebius `nebius_compute_v1_gpu_cluster` rule: all instances
    in a multi-node training pool must belong to the same InfiniBand `gpu_cluster`
    fabric ID so NCCL can communicate over InfiniBand RDMA.
    """
    mismatches: List[str] = []
    for inst in instances:
        name = str(inst.get("name"))
        fab_id = (inst.get("gpu_cluster") or {}).get("id")
        if fab_id != expected_fabric_id:
            mismatches.append(f"{name}: gpu_cluster.id={fab_id!r} != {expected_fabric_id!r}")
    return mismatches
