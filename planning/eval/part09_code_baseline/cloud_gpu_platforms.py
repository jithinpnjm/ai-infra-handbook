#!/usr/bin/env python3
"""Part 9, Chapter 9.14: Cloud GPU platforms model.

Models BCM Topograph cloud topology generation (AWS p5.48xlarge / DGX Cloud,
OCI dynamic groups, GCP COMPACT placement, and Topograph 3 vs 4 upgrade rules),
GCP GPU machine families (G2, A2, A3, A3 Ultra, A4, A4X) and GKE/VM guardrails,
and Nebius / CoreWeave InfiniBand fabric & Kubernetes/Slurm scheduling rules.

Sources:
- NVIDIA Base Command Manager 11 Administrator Manual Section 7.5 (pp. 408-420)
- Handbook Chapter 4.24 (Terraform on GCP and Nebius: networks, GPU VMs and GKE)
- nvidia-zero-to-hero Volume 01 Chapter 8 (Section 4 vGPU/MIG & Section 6 DGX Cloud)
- nvidia-devops-legacy-v09 ("02 - K8s & Virtualization Gauntlet", Question 2 SR-IOV/IOMMU)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class GCPGPUMachineFamily:
    """Specification for a Google Cloud GPU machine family (Chapter 4.24 §2-3)."""

    family: str
    example_machine_type: str
    gpu_model: str
    gpus_per_vm: int
    inter_node_gpu_transport: str
    requires_multi_nic_vpcs: bool
    recommended_mtu: int


GCP_GPU_CATALOG: Dict[str, GCPGPUMachineFamily] = {
    "G2": GCPGPUMachineFamily(
        family="G2",
        example_machine_type="g2-standard-8",
        gpu_model="NVIDIA L4 (24 GB GDDR6 PCIe)",
        gpus_per_vm=1,
        inter_node_gpu_transport="Standard gVNIC TCP/UDP",
        requires_multi_nic_vpcs=False,
        recommended_mtu=1460,
    ),
    "A2": GCPGPUMachineFamily(
        family="A2",
        example_machine_type="a2-highgpu-8g",
        gpu_model="NVIDIA A100 (40/80 GB SXM4)",
        gpus_per_vm=8,
        inter_node_gpu_transport="Standard gVNIC",
        requires_multi_nic_vpcs=False,
        recommended_mtu=8896,
    ),
    "A3": GCPGPUMachineFamily(
        family="A3",
        example_machine_type="a3-highgpu-8g",
        gpu_model="NVIDIA H100 (80 GB SXM5)",
        gpus_per_vm=8,
        inter_node_gpu_transport="GPUDirect-TCPX",
        requires_multi_nic_vpcs=True,
        recommended_mtu=8896,
    ),
    "A3-Ultra": GCPGPUMachineFamily(
        family="A3-Ultra",
        example_machine_type="a3-ultragpu-8g",
        gpu_model="NVIDIA H200 (141 GB HBM3e SXM)",
        gpus_per_vm=8,
        inter_node_gpu_transport="GPUDirect-RDMA (RoCEv2 VPC)",
        requires_multi_nic_vpcs=True,
        recommended_mtu=8896,
    ),
    "A4": GCPGPUMachineFamily(
        family="A4",
        example_machine_type="a4-highgpu-8g",
        gpu_model="NVIDIA Blackwell B200 (SXM6)",
        gpus_per_vm=8,
        inter_node_gpu_transport="GPUDirect-RDMA (RoCEv2 VPC)",
        requires_multi_nic_vpcs=True,
        recommended_mtu=8896,
    ),
    "A4X": GCPGPUMachineFamily(
        family="A4X",
        example_machine_type="a4x-nvl72",
        gpu_model="NVIDIA GB200 NVL72 (72 B200 + 36 Grace)",
        gpus_per_vm=72,
        inter_node_gpu_transport="Multi-Node NVLink 5 (1.8 TB/s) + GPUDirect-RDMA",
        requires_multi_nic_vpcs=True,
        recommended_mtu=8896,
    ),
}

OCI_TOPOGRAPH_REQUIRED_INSPECT_RESOURCES: Tuple[str, ...] = (
    "compute-capacity-topologies",
    "compute-bare-metal-hosts",
    "compute-hpc-islands",
    "compute-network-blocks",
    "compute-local-blocks",
)


def validate_bcm_topograph_cloud_config(config: Dict[str, object]) -> Dict[str, object]:
    """Validate BCM Topograph configuration for AWS (DGX Cloud), OCI, and GCP (bcm11-admin pp. 413-419).

    Source: NVIDIA Base Command Manager 11 Administrator Manual Section 7.5 (pp. 413-419):
    - Topograph listens on TCP port 49021 by default (`HttpSSL = true`, `Fetch timeout = 20`,
      `Fetch attempts = 12`, `Fetch wait time = 15`).
    - Supports `tree` (`topology/tree`) and `block` (`topology/block`) Slurm plugins.
    - Topograph 4 (`BCM 11.34+`): `topograph` and `topograph4` packages conflict; using Topograph 4
      requires BOTH `package_installed == "topograph4"` AND `version4_setting is True` (plus
      `systemd_daemon_reloaded is True`). Having only one set causes Topograph to fail!
    - If `topograph_node != slurmserver_node`, certificates must be on `/cm/shared` and
      `UPDATE_TOPOLOGY_TOKEN` must be added to the node profile.
    - Cloud provider rules:
      1. AWS (`p5.48xlarge` used by DGX Cloud): nodes must be running (`nodes_running=True`), use a
         supported topology flavor, and have `ec2:DescribeInstanceTopology` (`AmazonEC2ReadOnlyAccess`)
         either via `pass_cloud_credentials=True` or EC2 IMDS Instance Profile Role (`has_imds_role=True`).
      2. OCI: nodes must exist (`nodes_running=True`), and if `pass_cloud_credentials=False`, must grant
         dynamic group `inspect` permissions on all 5 OCI topology resource types.
      3. GCP: VM placement policy must be `COMPACT`.
    """
    errors: List[str] = []

    plugin = str(config.get("topology_plugin", "tree"))
    if plugin not in ("tree", "block"):
        errors.append(f"unsupported_topograph_plugin ({plugin}; Topograph supports only tree or block)")

    pkg = str(config.get("package_installed", "topograph"))
    v4_flag = bool(config.get("version4_setting", False))
    if (pkg == "topograph4" and not v4_flag) or (pkg == "topograph" and v4_flag):
        errors.append(
            "topograph4_mismatch (must BOTH install topograph4 package AND set version4=true in topographsettings)"
        )
    if pkg == "topograph4" and not bool(config.get("systemd_daemon_reloaded", True)):
        errors.append("missing_systemd_daemon_reload (topograph4 replaces systemd unit; run systemctl daemon-reload)")

    if bool(config.get("separate_topograph_and_slurm_nodes", False)):
        if not bool(config.get("shared_certs_and_update_topology_token", False)):
            errors.append(
                "missing_shared_certs_or_token (separate Topograph node requires /cm/shared certs + UPDATE_TOPOLOGY_TOKEN)"
            )

    if not bool(config.get("nodes_running", True)):
        errors.append("cloud_nodes_not_running (nodes must exist/run during topology generation; otherwise placed on fake switch/block)")

    provider = str(config.get("cloud_provider", "AWS"))
    pass_creds = bool(config.get("pass_cloud_credentials", True))

    if provider == "AWS":
        if not bool(config.get("has_ec2_describe_instance_topology", False)):
            errors.append("missing_aws_permission (requires ec2:DescribeInstanceTopology / AmazonEC2ReadOnlyAccess)")
        if not pass_creds and not bool(config.get("has_imds_instance_profile_role", False)):
            errors.append("missing_aws_credentials_source (need Pass cloud credentials=yes or EC2 IMDS profile role)")
    elif provider == "OCI":
        if not pass_creds:
            granted = set(config.get("oci_dynamic_group_resources", ()))
            missing = [r for r in OCI_TOPOGRAPH_REQUIRED_INSPECT_RESOURCES if r not in granted]
            if missing:
                errors.append(f"missing_oci_dynamic_group_permissions ({','.join(missing)})")
    elif provider == "GCP":
        if str(config.get("gcp_placement_policy", "")) != "COMPACT":
            errors.append("missing_gcp_compact_placement (GCP requires COMPACT VM placement policy)")
    else:
        raise ValueError(f"Unsupported cloud_provider: {provider}")

    return {
        "valid_topograph": len(errors) == 0,
        "default_http_port": 49021,
        "errors": errors,
    }


def audit_cloud_gpu_cluster_spec(spec: Dict[str, object]) -> Dict[str, object]:
    """Audit a GCP (A3/A4/GKE) or Nebius/CoreWeave cloud GPU deployment specification.

    Sources:
    - Handbook Chapter 4.24 (§§2-8)
    - nvidia-devops-legacy-v09 ("02 - K8s & Virtualization Gauntlet", Question 2 SR-IOV/IOMMU)
    """
    issues: List[str] = []
    platform = str(spec.get("platform", "GCP"))

    if platform == "GCP":
        fam = str(spec.get("machine_family", "A3"))
        if fam not in GCP_GPU_CATALOG:
            raise KeyError(f"Unknown GCP machine family: {fam}")
        f_spec = GCP_GPU_CATALOG[fam]

        if str(spec.get("on_host_maintenance", "")) != "TERMINATE":
            issues.append("invalid_host_maintenance (GPU VMs cannot live-migrate; must set TERMINATE)")

        if bool(spec.get("multi_node_training", True)):
            if str(spec.get("placement_collocation", "")) != "COLLOCATED":
                issues.append("missing_compact_placement (multi-node training requires COLLOCATED compact policy)")
            if f_spec.requires_multi_nic_vpcs and not bool(spec.get("multi_nic_gpu_vpcs_configured", False)):
                issues.append(f"missing_multi_nic_gpu_vpcs ({fam} requires dedicated GPU NIC VPCs for {f_spec.inter_node_gpu_transport})")
            if int(spec.get("vpc_mtu", 1460)) < 8244 and f_spec.requires_multi_nic_vpcs:
                issues.append("mtu_too_small_for_gpu_vpc (use jumbo MTU 8244 or 8896 on GPU training VPCs)")

        if bool(spec.get("is_gke_node_pool", False)):
            if int(spec.get("max_surge", 1)) > 0 and bool(spec.get("quota_or_reservation_tight", True)):
                issues.append("gke_surge_upgrade_starvation_risk (set max_surge=0, max_unavailable=1 on tight GPU pools)")
            if bool(spec.get("both_gke_driver_installer_and_gpu_operator_driver_enabled", False)):
                issues.append("duplicate_driver_managers (do not enable both GKE driver installer and GPU Operator driver container)")

    elif platform == "Nebius":
        if bool(spec.get("multi_node_training", True)):
            if not bool(spec.get("all_nodes_in_same_gpu_cluster_fabric", False)):
                issues.append("nebius_fabric_mismatch (all multi-node instances must join the same nebius_compute_v1_gpu_cluster IB fabric)")

    elif platform == "CoreWeave":
        if bool(spec.get("uses_virtualized_nics_without_sriov_iommu", False)):
            issues.append("emulated_vswitch_overhead (high-speed cloud RDMA requires bare-metal or SR-IOV VFs with IOMMU passthrough)")

    else:
        raise ValueError(f"Unsupported cloud platform: {platform}")

    return {
        "passes_cloud_audit": len(issues) == 0,
        "issues": issues,
    }
