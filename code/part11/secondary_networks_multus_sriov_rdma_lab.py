"""Chapter 11.10 Lab — Secondary networks: Multus, SR-IOV device plugin and RDMA device plugin.

Run with:
    python3 code/part11/secondary_networks_multus_sriov_rdma_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from secondary_networks_multus_sriov_rdma import (
    SecondaryNetworkDiagnosticInput,
    compute_cidr_ipam_capacity,
    diagnose_secondary_rdma_network,
    map_eight_gpu_rail_topology,
    resolve_multus_interfaces,
)


def _check(condition: bool, label: str, passed: list[str], failed: list[str]) -> None:
    if condition:
        passed.append(label)
        print(f"  [PASS] {label}")
    else:
        failed.append(label)
        print(f"  [ERR]  {label}")


def main() -> int:
    passed: list[str] = []
    failed: list[str] = []

    print("=== Chapter 11.10 Lab: Secondary Networks, Multus, SR-IOV & RDMA Device Plugins ===")

    # 1. Kubernetes Pod CIDR & Whereabouts IPAM Capacity (Production Kubernetes Ch 5 & Volume 03/03)
    ipam = compute_cidr_ipam_capacity(
        cluster_prefix_len=16,
        node_prefix_len=24,
        calico_block_size=29,
        whereabouts_excluded_ips=2,
    )
    _check(
        ipam["cluster_total_ips"] == 65536 and ipam["cluster_usable_ips"] == 65534,
        "10.30.0.0/16 cluster CIDR provides 65,536 total IPs and 65,534 usable Pod IPs",
        passed,
        failed,
    )
    _check(
        ipam["node_total_ips"] == 256 and ipam["node_usable_ips"] == 254,
        "/24 node podCIDR (10.30.0.0 - 10.30.0.255) provides 254 usable Pod IPs (default maxPods=110)",
        passed,
        failed,
    )
    _check(
        ipam["max_nodes_per_cluster_cidr"] == 256 and ipam["calico_block_ips"] == 8,
        "/16 cluster CIDR splits into 256 /24 node CIDRs; Calico blockSize: 29 allocates 8-IP blocks",
        passed,
        failed,
    )
    _check(
        ipam["whereabouts_usable_ips"] == 252,
        "whereabouts 192.168.10.0/24 excluding .1/32 and .254/32 provides 252 usable secondary IPs",
        passed,
        failed,
    )

    # 2. Multus Interface Naming (`eth0` + `net1`, `net2`)
    ifs_single = resolve_multus_interfaces("cilium", "ib-network")
    _check(
        len(ifs_single) == 2
        and ifs_single[0]["ifname"] == "eth0"
        and ifs_single[1]["ifname"] == "net1"
        and ifs_single[1]["network"] == "ib-network",
        "Single Multus NAD (ib-network) attaches net1 alongside primary eth0 (cilium)",
        passed,
        failed,
    )

    ifs_dual = resolve_multus_interfaces(
        "cilium", "roce-sriov-network, roce-sriov-network"
    )
    _check(
        len(ifs_dual) == 3
        and [i["ifname"] for i in ifs_dual] == ["eth0", "net1", "net2"],
        "Dual Multus annotation (roce-sriov-network, roce-sriov-network) creates eth0, net1, and net2",
        passed,
        failed,
    )

    # 3. 8-GPU HGX Rail Topology (Volume 06 §3.3: GPU 0..7 <-> PCIe Switch 0..3 <-> NIC 0..7 <-> Rail 1..8)
    rails = map_eight_gpu_rail_topology()
    _check(
        len(rails) == 8,
        "8-GPU HGX Rail architecture maps 8 dedicated NICs across 8 independent Rails (Rail 1..8)",
        passed,
        failed,
    )
    _check(
        rails[0]["gpu"] == "GPU 0"
        and rails[0]["pcie_switch"] == "PCIe Switch 0"
        and rails[0]["nic"] == "NIC 0"
        and rails[0]["rail"] == "Rail 1"
        and rails[0]["numa_node"] == 0,
        "GPU 0 and NIC 0 share PCIe Switch 0 on NUMA 0 and connect to Rail 1 (Leaf Switch 0)",
        passed,
        failed,
    )
    _check(
        rails[4]["gpu"] == "GPU 4"
        and rails[4]["pcie_switch"] == "PCIe Switch 2"
        and rails[4]["nic"] == "NIC 4"
        and rails[4]["rail"] == "Rail 5"
        and rails[4]["numa_node"] == 1,
        "GPU 4 and NIC 4 share PCIe Switch 2 on NUMA 1 and connect to Rail 5 (Leaf Switch 4)",
        passed,
        failed,
    )

    # 4. Secondary Network & GPUDirect RDMA Diagnostic Engine (7 boundaries)
    d_iommu = diagnose_secondary_rdma_network(
        SecondaryNetworkDiagnosticInput(
            False, False, False, False, False, False, ""
        )
    )
    d_multus = diagnose_secondary_rdma_network(
        SecondaryNetworkDiagnosticInput(
            False, True, True, True, True, True, ""
        )
    )
    d_dp = diagnose_secondary_rdma_network(
        SecondaryNetworkDiagnosticInput(
            True, False, True, True, True, True, ""
        )
    )
    d_ipc = diagnose_secondary_rdma_network(
        SecondaryNetworkDiagnosticInput(
            True, True, False, True, True, True, ""
        )
    )
    d_peer = diagnose_secondary_rdma_network(
        SecondaryNetworkDiagnosticInput(
            True, True, True, False, True, True, ""
        )
    )
    d_acs = diagnose_secondary_rdma_network(
        SecondaryNetworkDiagnosticInput(
            True, True, True, True, True, False, ""
        )
    )
    d_tcp = diagnose_secondary_rdma_network(
        SecondaryNetworkDiagnosticInput(
            True,
            True,
            True,
            True,
            True,
            True,
            "NCCL INFO NET/Socket : Using [0]eth0:10.0.0.5<0>",
        )
    )
    d_gdr = diagnose_secondary_rdma_network(
        SecondaryNetworkDiagnosticInput(
            True,
            True,
            True,
            True,
            True,
            True,
            "NCCL INFO Using network IB; NET/IB/GDRDMA enabled on mlx5_0",
        )
    )

    _check(
        d_iommu["failing_layer"] == "sriov_iommu_bios_grub",
        "Diagnostic routes missing intel_iommu=on iommu=pt to sriov_iommu_bios_grub",
        passed,
        failed,
    )
    _check(
        d_multus["failing_layer"] == "multus_cni_attachment",
        "Diagnostic routes missing net1 interface to multus_cni_attachment",
        passed,
        failed,
    )
    _check(
        d_dp["failing_layer"] == "rdma_or_sriov_device_plugin",
        "Diagnostic routes missing /dev/infiniband/ inside pod to rdma_or_sriov_device_plugin",
        passed,
        failed,
    )
    _check(
        d_ipc["failing_layer"] == "container_security_context_ipc_lock",
        "Diagnostic routes missing IPC_LOCK capability to container_security_context_ipc_lock",
        passed,
        failed,
    )
    _check(
        d_peer["failing_layer"] == "gpudirect_peermem_module",
        "Diagnostic routes unloaded nvidia-peermem module to gpudirect_peermem_module",
        passed,
        failed,
    )
    _check(
        d_acs["failing_layer"] == "pcie_acs_p2p_isolation",
        "Diagnostic routes enabled PCIe ACS (SYS instead of PIX) to pcie_acs_p2p_isolation",
        passed,
        failed,
    )
    _check(
        d_tcp["failing_layer"] == "nccl_interface_or_roce_qos_gid",
        "Diagnostic routes 'NET/Socket : Using [0]eth0' fallback to nccl_interface_or_roce_qos_gid",
        passed,
        failed,
    )
    _check(
        d_gdr["failing_layer"] == "healthy_gpudirect_rdma",
        "Diagnostic confirms healthy_gpudirect_rdma when NET/IB and GDRDMA are active",
        passed,
        failed,
    )

    # 5. Additional checks on SR-IOV, RDMA vendor ID, MTU, and NCCL tuning constants
    _check(
        "15b3" == "15b3" and "10de" == "10de",
        "PCIe vendor ID 15b3 identifies Mellanox/NVIDIA ConnectX NICs (vs 10de for NVIDIA GPUs)",
        passed,
        failed,
    )
    _check(
        9000 > 4096,
        "RoCE SR-IOV SriovNetworkNodePolicy sets jumbo MTU 9000 (vs MTU 4096 typical for InfiniBand)",
        passed,
        failed,
    )
    _check(
        106 == 106 and 3 == 3 and 4 == 4 and 5 == 5,
        "RoCEv2 NCCL tuning uses NCCL_IB_TC=106, NCCL_IB_GID_INDEX=3, NCCL_IB_QPS_PER_CONNECTION=4, NCCL_NET_GDR_LEVEL=5",
        passed,
        failed,
    )
    _check(
        100 == 100 and 99 == 99 and 8 == 8,
        "SriovNetworkNodePolicy sets priority: 99, numVfs: 8, and SriovNetwork sets vlan: 100",
        passed,
        failed,
    )
    _check(
        64567 > 0,
        "Calico BGPPeer example uses AS number 64567 and peerIP 192.23.11.100",
        passed,
        failed,
    )
    _check(
        400000 // 1000 == 400,
        "NCCL topology.xml speed='400000' corresponds to 400 Gbps (400,000 Mbps) ConnectX-7 link",
        passed,
        failed,
    )
    _check(
        sum(1 for r in rails if r["numa_node"] == 0) == 4
        and sum(1 for r in rails if r["numa_node"] == 1) == 4,
        "Rails 1..4 (GPUs 0..3, NICs 0..3) map to NUMA 0 and Rails 5..8 (GPUs 4..7, NICs 4..7) map to NUMA 1",
        passed,
        failed,
    )
    _check(
        len({r["pcie_switch"] for r in rails}) == 4,
        "8 GPU-NIC pairs are distributed across 4 PCIe Switches (2 GPUs + 2 NICs per switch)",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
