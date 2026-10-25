"""Chapter 11.10 — Secondary networks: Multus, SR-IOV device plugin and RDMA device plugin.

Deterministic models for:
1. Kubernetes Pod CIDR & Calico `IPPool` IPAM math (`10.30.0.0/16` = `65,534`
   usable IPs; `/24` node CIDR = `254` usable IPs; Calico `blockSize: 29` = `8`
   addresses per block; `whereabouts` `/24` excluding `.1/32` and `.254/32` =
   `252` usable secondary IPs).
2. Multus CNI secondary interface allocator (`eth0` primary CNI + `net1..netN`
   secondary interfaces from `k8s.v1.cni.cncf.io/networks`).
3. RDMA Shared Device Plugin (`rdma/hca` / `rdma/rdma_shared_device_a`, vendor
   `15b3`) vs SR-IOV Network Device Plugin (`SriovNetworkNodePolicy`, `numVfs: 8`,
   `mtu: 9000`, `vlan: 100`, `nvidia.com/hostdev` / `rdma_vf`) and 8-NIC Rail
   topology mapper (`GPU 0..7 <-> PCIe Switch 0..3 <-> NIC 0..7`).
4. NCCL transport & secondary network health validator (`ip addr show net1`,
   `/dev/infiniband/`, `NET/IB/GDRDMA` vs `NET/Socket : Using [0]eth0`, `IPC_LOCK`,
   IOMMU `intel_iommu=on iommu=pt`, PCIe ACS).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


def compute_cidr_ipam_capacity(
    cluster_prefix_len: int = 16,
    node_prefix_len: int = 24,
    calico_block_size: int = 29,
    whereabouts_excluded_ips: int = 2,
) -> Dict[str, int]:
    """Compute IPAM capacities from Production Kubernetes Ch 5 and Volume 03/03."""
    cluster_total = 2 ** (32 - cluster_prefix_len)
    cluster_usable = cluster_total - 2  # network + broadcast
    node_total = 2 ** (32 - node_prefix_len)
    node_usable = node_total - 2
    max_nodes_in_cluster_cidr = 2 ** (node_prefix_len - cluster_prefix_len)
    calico_block_ips = 2 ** (32 - calico_block_size)
    whereabouts_usable = node_usable - whereabouts_excluded_ips
    return {
        "cluster_total_ips": cluster_total,
        "cluster_usable_ips": cluster_usable,
        "node_total_ips": node_total,
        "node_usable_ips": node_usable,
        "max_nodes_per_cluster_cidr": max_nodes_in_cluster_cidr,
        "calico_block_ips": calico_block_ips,
        "whereabouts_usable_ips": whereabouts_usable,
    }


def resolve_multus_interfaces(
    primary_cni: str,
    networks_annotation: str,
) -> List[Dict[str, str]]:
    """Map primary CNI (`eth0`) and comma-separated Multus NADs (`net1..netN`)."""
    interfaces: List[Dict[str, str]] = [
        {"ifname": "eth0", "network": primary_cni, "role": "primary_cluster_network"}
    ]
    nads = [n.strip() for n in networks_annotation.split(",") if n.strip()]
    for idx, nad_name in enumerate(nads, start=1):
        interfaces.append(
            {
                "ifname": f"net{idx}",
                "network": nad_name,
                "role": "secondary_high_speed_fabric",
            }
        )
    return interfaces


def map_eight_gpu_rail_topology() -> List[Dict[str, object]]:
    """Map the 8-GPU HGX Rail architecture from Volume 06 Section 3.3."""
    rails: List[Dict[str, object]] = []
    for gpu_idx in range(8):
        pcie_switch_idx = gpu_idx // 2
        numa_node = 0 if gpu_idx < 4 else 1
        rails.append(
            {
                "gpu": f"GPU {gpu_idx}",
                "pcie_switch": f"PCIe Switch {pcie_switch_idx}",
                "nic": f"NIC {gpu_idx}",
                "rail": f"Rail {gpu_idx + 1}",
                "leaf_switch": f"Leaf Switch {gpu_idx}",
                "numa_node": numa_node,
            }
        )
    return rails


@dataclass(frozen=True)
class SecondaryNetworkDiagnosticInput:
    """Inputs for diagnosing Multus / SR-IOV / RDMA / NCCL secondary network health."""

    net1_present: bool
    dev_infiniband_present: bool
    ipc_lock_granted: bool
    nvidia_peermem_loaded: bool
    iommu_pt_enabled: bool
    pcie_acs_disabled: bool
    nccl_log_line: str


def diagnose_secondary_rdma_network(
    diag: SecondaryNetworkDiagnosticInput,
) -> Dict[str, str]:
    """Diagnose Multus, SR-IOV VF, RDMA device plugin, and NCCL transport issues."""
    if not diag.iommu_pt_enabled:
        return {
            "failing_layer": "sriov_iommu_bios_grub",
            "remediation": "Enable intel_iommu=on iommu=pt (or AMD-Vi equivalent) in GRUB/BIOS so SR-IOV VFs can be created",
        }
    if not diag.net1_present:
        return {
            "failing_layer": "multus_cni_attachment",
            "remediation": "Check k8s.v1.cni.cncf.io/networks annotation, NetworkAttachmentDefinition, and whereabouts IPAM",
        }
    if not diag.dev_infiniband_present:
        return {
            "failing_layer": "rdma_or_sriov_device_plugin",
            "remediation": "Request rdma/hca, rdma/rdma_shared_device_a, or nvidia.com/hostdev in resources.limits so /dev/infiniband/ is mounted",
        }
    if not diag.ipc_lock_granted:
        return {
            "failing_layer": "container_security_context_ipc_lock",
            "remediation": "Add capabilities.add: ['IPC_LOCK'] to container securityContext for RDMA pinned memory registration",
        }
    if not diag.nvidia_peermem_loaded:
        return {
            "failing_layer": "gpudirect_peermem_module",
            "remediation": "Load nvidia-peermem kernel module (or enable driver.rdma / nvPeerDriver) for GPUDirect RDMA",
        }
    if not diag.pcie_acs_disabled:
        return {
            "failing_layer": "pcie_acs_p2p_isolation",
            "remediation": "Disable PCIe Access Control Services (ACS) in BIOS so GPU-to-NIC traffic stays on PIX instead of bouncing through CPU root complex",
        }
    if "NET/Socket" in diag.nccl_log_line:
        return {
            "failing_layer": "nccl_interface_or_roce_qos_gid",
            "remediation": "Set NCCL_SOCKET_IFNAME=net1, NCCL_IB_HCA=mlx5_0,mlx5_1, NCCL_IB_GID_INDEX=3, and NCCL_IB_TC=106",
        }
    if "NET/IB" in diag.nccl_log_line and "GDRDMA" in diag.nccl_log_line:
        return {
            "failing_layer": "healthy_gpudirect_rdma",
            "remediation": "Secondary network, RDMA device nodes, and GPUDirect RDMA transport verified",
        }
    return {
        "failing_layer": "unknown_nccl_transport",
        "remediation": "Inspect full NCCL_DEBUG=INFO log output",
    }
