#!/usr/bin/env python3
"""Chapter 11.21 model: PCIe, IOMMU, VFIO, Device Passthrough & Cloud Virtualization Internals.

Models:
1. Volume 07 Chapter 2 PCIe Gen4/Gen5 bandwidth, Root Complex vs PCIe Switch P2P,
   nvidia-smi topo -m distance codes (PIX, PXB, PHB, NODE, SYS), and NUMA alignment.
2. Volume 18 Chapter 7 DMA attack threat model, IOMMU (Intel VT-d / AMD-Vi) DMAR
   access table, and Linux VFIO group isolation rules (all endpoints in an IOMMU group
   must bind to vfio-pci or a bridge before passthrough).
3. Brendan Gregg, Systems Performance 2nd Ed., Chapter 11 (SP 11):
   - 11.1 Autoscaling savings (Pinterest $54/hr -> $20/hr, Shopify 61% -> 19% idle),
     AWS m5.large (2 vCPU, 8 GB) to m5.24xlarge (96 vCPU, 384 GB).
   - 11.2 Hardware Virtualization (Config A Xen vs Config B KVM+QEMU vs AWS Nitro;
     perf kvm stat live MSR_WRITE=1668/68.90%, HLT=466/19.25%/99.63% time,
     EPT_MISCONFIG=19.94us; kvmexits.bt EPT_VIOLATION [2K, 4K)=7686; KVM 5 steps vs Xen 10).
   - 11.3 OS Virtualization (8 namespaces in Table 11.1, 12 cgroups in Table 11.2,
     CFS shares formula 10/(10+30)=25% vs 10/100=10%, cpu.stat 74/507 throttled = 3.8s,
     NSpid: 4915 -> 753 in pid:[4026532216]).
   - 11.4-11.6 Lightweight Virtualization (QEMU 1.4M LoC vs Firecracker 50K LoC / ~100ms / <5MB
     vs Clear Containers <45ms / 48-50MB) and Table 11.7 comparison matrix.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


PCIE_TOPOLOGY_CODES: Dict[str, Dict[str, object]] = {
    "PIX": {
        "meaning": "Connection traversing at most a single PCIe switch",
        "crosses_cpu_root_complex": False,
        "crosses_numa_upi": False,
        "p2p_gpudirect_optimal": True,
    },
    "PXB": {
        "meaning": "Connection traversing multiple cascaded PCIe switches without crossing Host Bridge",
        "crosses_cpu_root_complex": False,
        "crosses_numa_upi": False,
        "p2p_gpudirect_optimal": True,
    },
    "PHB": {
        "meaning": "Connection traversing a PCIe Host Bridge (CPU Root Complex) within one NUMA node",
        "crosses_cpu_root_complex": True,
        "crosses_numa_upi": False,
        "p2p_gpudirect_optimal": False,
    },
    "NODE": {
        "meaning": "Connection traversing PCIe Host Bridges within a single NUMA node",
        "crosses_cpu_root_complex": True,
        "crosses_numa_upi": False,
        "p2p_gpudirect_optimal": False,
    },
    "SYS": {
        "meaning": "Connection crossing the inter-socket NUMA interconnect (Intel UPI / AMD xGMI)",
        "crosses_cpu_root_complex": True,
        "crosses_numa_upi": True,
        "p2p_gpudirect_optimal": False,
    },
}


@dataclass(frozen=True)
class PcieDeviceEndpoint:
    bdf: str
    vendor_device_id: str
    device_class: str  # "gpu", "gpu_audio", "pci_bridge", "nic", "nvme"
    current_driver: str


def validate_vfio_iommu_group_passthrough(
    iommu_enabled_in_bios_and_kernel: bool,
    iommu_pt_passthrough_mode_for_host: bool,
    group_id: int,
    group_devices: List[PcieDeviceEndpoint],
) -> Dict[str, object]:
    """Validates whether an IOMMU group can be safely opened via /dev/vfio/<group_id>."""
    if not iommu_enabled_in_bios_and_kernel:
        return {
            "passthrough_ready": False,
            "dmar_dma_firewall_active": False,
            "reason": "IOMMU disabled in BIOS or kernel (missing intel_iommu=on / amd_iommu=on): vulnerable to rogue DMA and VFIO unavailable",
        }

    non_isolated_endpoints = [
        d.bdf
        for d in group_devices
        if d.device_class != "pci_bridge" and d.current_driver not in ("vfio-pci", "pci-stub", "none")
    ]
    if non_isolated_endpoints:
        return {
            "passthrough_ready": False,
            "dmar_dma_firewall_active": True,
            "blocking_bdfs": non_isolated_endpoints,
            "reason": f"IOMMU group {group_id} is not viable: sibling endpoints {non_isolated_endpoints} are still bound to host drivers",
        }

    return {
        "passthrough_ready": True,
        "dmar_dma_firewall_active": True,
        "iommu_pt_host_bypass": iommu_pt_passthrough_mode_for_host,
        "vfio_device_node": f"/dev/vfio/{group_id}",
        "reason": "All non-bridge endpoints in IOMMU group bound to vfio-pci; DMA remapping isolated to guest VM domain",
    }


def compute_cfs_cpu_share_bursting(
    container_a_shares: int = 10,
    container_b_shares: int = 30,
    total_system_shares: int = 100,
    cfs_bandwidth_cap_pct: float = 20.0,
) -> Dict[str, float]:
    """Computes SP 11 Section 11.3.3 CFS CPU share bursting vs busy allocation."""
    only_a_busy_pct = 100.0
    a_and_b_busy_pct = round((container_a_shares / (container_a_shares + container_b_shares)) * 100.0, 1)
    all_containers_busy_pct = round((container_a_shares / total_system_shares) * 100.0, 1)
    burst_drop_ratio = round(only_a_busy_pct / all_containers_busy_pct, 1)

    return {
        "only_a_busy_pct": only_a_busy_pct,
        "a_and_b_busy_pct": a_and_b_busy_pct,
        "all_containers_busy_pct": all_containers_busy_pct,
        "burst_drop_ratio": burst_drop_ratio,
        "cfs_bandwidth_min_pct": all_containers_busy_pct,
        "cfs_bandwidth_max_pct": cfs_bandwidth_cap_pct,
    }


SP11_VIRTUALIZATION_COMPARISON: Dict[str, Dict[str, object]] = {
    "hardware_vm_kvm": {
        "example": "KVM + QEMU (or AWS Nitro without QEMU proxy)",
        "vmm_code_lines": 1_400_000,  # QEMU 4.2 > 1.4M LoC
        "memory_translation": "Two-stage (Guest Virtual -> Guest Physical -> Host Physical via Intel EPT / AMD NPT)",
        "io_steps_without_pv": 5,     # Qumranet 06: 5 steps in KVM vs 10 in Xen
        "host_observability": "Medium (sees qemu-system-x86 / vCPU threads & perf kvm stat live; guest internals opaque)",
        "guest_observability": "High (dedicated kernel; perf, Ftrace, BPF biosnoop, and vmstat %st work)",
        "favors": "End users",
    },
    "os_containers": {
        "example": "Linux Containers (namespaces + cgroups + seccomp-bpf)",
        "vmm_code_lines": 0,
        "memory_translation": "Single-stage host MMU (zero EPT/NPT overhead, shared page cache via OverlayFS)",
        "io_steps_without_pv": 1,
        "host_observability": "High (sees all container PIDs via NSpid, cgroups, nsenter, and bpftrace uts_ns nodename)",
        "guest_observability": "Medium (kernel tracing restricted; top/uptime/mpstat/vmstat/free/iostat leak host stats)",
        "favors": "Host operators",
    },
    "lightweight_microvm": {
        "example": "AWS Firecracker / Kata Containers (Intel Clear Containers)",
        "firecracker_code_lines": 50_000,
        "firecracker_boot_ms": 100,
        "firecracker_mem_overhead_mb": 5,
        "clear_containers_boot_ms": 45,
        "clear_containers_mem_overhead_mb": 50,
        "memory_translation": "Two-stage EPT/NPT with minimal emulated device surface",
        "host_observability": "Medium (VM appears as a single firecracker process on host)",
        "guest_observability": "High (dedicated guest kernel; BPF/perf/mpstat work cleanly inside guest)",
        "favors": "End users",
    },
}
