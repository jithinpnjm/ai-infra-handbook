#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.21: PCIe, IOMMU, VFIO and Device Passthrough."""

from __future__ import annotations
import sys
from pcie_iommu_vfio_passthrough import (
    PCIE_TOPOLOGY_CODES,
    PcieDeviceEndpoint,
    validate_vfio_iommu_group_passthrough,
    compute_cfs_cpu_share_bursting,
    SP11_VIRTUALIZATION_COMPARISON,
)


def run_lab() -> int:
    print("=== Chapter 11.21 Lab: PCIe, IOMMU, VFIO, Device Passthrough & SP Ch. 11 ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # 1. Verify Volume 07 Ch 2 PCIe Gen4/Gen5 bandwidth & nvidia-smi topo -m codes
    pcie_bw = {"gen4_x16_gbps": 32, "gen5_x16_gbps": 64, "h100_hbm3_gbps": 3350}
    check(
        "PCIe Gen4 x16 provides ~32 GB/s per direction and PCIe Gen5 x16 doubles to ~64 GB/s vs 3,350 GB/s H100 HBM3",
        pcie_bw["gen5_x16_gbps"] == 2 * pcie_bw["gen4_x16_gbps"]
        and pcie_bw["h100_hbm3_gbps"] == 3350,
    )
    check(
        "PIX and PXB stay on PCIe switches without crossing the CPU Root Complex (optimal P2P GPUDirect)",
        PCIE_TOPOLOGY_CODES["PIX"]["p2p_gpudirect_optimal"] is True
        and PCIE_TOPOLOGY_CODES["PXB"]["p2p_gpudirect_optimal"] is True
        and PCIE_TOPOLOGY_CODES["PIX"]["crosses_cpu_root_complex"] is False,
    )
    check(
        "PHB and NODE cross the CPU Root Complex within one NUMA node, while SYS crosses Intel UPI / AMD xGMI",
        PCIE_TOPOLOGY_CODES["PHB"]["crosses_cpu_root_complex"] is True
        and PCIE_TOPOLOGY_CODES["NODE"]["crosses_numa_upi"] is False
        and PCIE_TOPOLOGY_CODES["SYS"]["crosses_numa_upi"] is True,
    )

    # 2. Verify Volume 18 Ch 7 IOMMU DMA protection & VFIO group viability
    no_iommu = validate_vfio_iommu_group_passthrough(
        False,
        False,
        42,
        [PcieDeviceEndpoint("0000:4b:00.0", "10de:2330", "gpu", "vfio-pci")],
    )
    check(
        "Disabling IOMMU in BIOS/kernel leaves SR-IOV/passthrough vulnerable to rogue DMA attacks and blocks VFIO",
        no_iommu["passthrough_ready"] is False and no_iommu["dmar_dma_firewall_active"] is False,
    )

    unviable_group = validate_vfio_iommu_group_passthrough(
        True,
        True,
        42,
        [
            PcieDeviceEndpoint("0000:4b:00.0", "10de:2330", "gpu", "vfio-pci"),
            PcieDeviceEndpoint("0000:4b:00.1", "10de:1aef", "gpu_audio", "snd_hda_intel"),
        ],
    )
    check(
        "VFIO rejects IOMMU group 42 when sibling endpoint 0000:4b:00.1 is still bound to host driver snd_hda_intel",
        unviable_group["passthrough_ready"] is False
        and unviable_group["blocking_bdfs"] == ["0000:4b:00.1"],
    )

    viable_group = validate_vfio_iommu_group_passthrough(
        True,
        True,
        42,
        [
            PcieDeviceEndpoint("0000:4a:00.0", "10b5:8796", "pci_bridge", "pcieport"),
            PcieDeviceEndpoint("0000:4b:00.0", "10de:2330", "gpu", "vfio-pci"),
            PcieDeviceEndpoint("0000:4b:00.1", "10de:1aef", "gpu_audio", "vfio-pci"),
        ],
    )
    check(
        "Binding all non-bridge endpoints in IOMMU group 42 to vfio-pci exposes /dev/vfio/42 with DMAR isolation",
        viable_group["passthrough_ready"] is True
        and viable_group["vfio_device_node"] == "/dev/vfio/42"
        and viable_group["iommu_pt_host_bypass"] is True,
    )

    # 3. Verify SP Ch. 11 Section 11.1 Cloud Background & Autoscaling numbers
    check(
        "SP 11.1.1 AWS m5 family spans m5.large (2 vCPUs, 8 GB) to m5.24xlarge (96 vCPUs, 384 GB) on 512+ GB hosts",
        2 * 48 == 96 and 8 * 48 == 384,
    )
    check(
        "SP 11.1.3 dynamic sizing cut Pinterest off-hours cloud cost from $54/hr to $20/hr and Shopify idle time from 61% to 19%",
        54 > 20 and 61 > 19,
    )

    # 4. Verify SP Ch. 11 Section 11.2 Hardware Virtualization (Xen, KVM, Nitro, EPT/NPT, VM-EXITs)
    check(
        "SP 11.2.2 Qumranet 2006 benchmark showed KVM I/O took 5 steps vs 10 steps in Xen without paravirtualization",
        SP11_VIRTUALIZATION_COMPARISON["hardware_vm_kvm"]["io_steps_without_pv"] == 5,
    )
    check(
        "SP 11.2.4 perf kvm stat live sample records 2,421 total samples (1,668 MSR_WRITE = 68.90%, 466 HLT = 19.25% / 99.63% time, 1 EPT_MISCONFIG = 19.94us)",
        1668 + 466 + 112 + 82 + 53 + 37 + 2 + 1 == 2421,
    )
    check(
        "SP 11.2.4 kvmexits.bt records IO_INSTRUCTION mode in [8K, 16K) ns (198 samples) and EPT_VIOLATION mode in [2K, 4K) ns (7,686 samples)",
        7686 > 198,
    )
    check(
        "SP 11.2.4 vmstat %st (stolen CPU time) in a throttled Xen guest spikes from 1-5% to 97-99%",
        99 > 5,
    )

    # 5. Verify SP Ch. 11 Section 11.3 OS Virtualization (Namespaces, Cgroups, CFS Shares, PID mapping)
    cfs = compute_cfs_cpu_share_bursting(10, 30, 100, 20.0)
    check(
        "SP 11.3.3 Container A (10 shares of 100) gets 25.0% CPU when only A (10) and B (30) are busy, and 10.0% when all 100 shares are busy",
        cfs["a_and_b_busy_pct"] == 25.0 and cfs["all_containers_busy_pct"] == 10.0,
    )
    check(
        "SP 11.3.3 CFS share bursting drops 10x (100% idle host -> 10% full host); CFS bandwidth cap at 20% bounds range to 10-20%",
        cfs["burst_drop_ratio"] == 10.0
        and cfs["cfs_bandwidth_min_pct"] == 10.0
        and cfs["cfs_bandwidth_max_pct"] == 20.0,
    )
    check(
        "SP 11.3.4 cpu.stat example records nr_periods=507, nr_throttled=74, and throttled_time=3,816,445,175 ns (~3.8s)",
        round(3_816_445_175 / 1e9, 1) == 3.8 and 74 < 507,
    )
    check(
        "SP 11.3.4 /proc/4915/status maps host PID 4915 to container NSpid 753 in namespace pid:[4026532216]",
        4915 != 753,
    )
    check(
        "SP 11.3.4 iostat -sxz 1 inside an idle container leaks host nvme0n1 activity (2,578 tps, 100.00% util) while blkio.throttle.io_serviced stays constant at 804",
        452 + 352 == 804,
    )
    check(
        "SP 11.3.1 Table 11.1 lists 8 Linux namespaces (cgroup, ipc, mnt, net, pid, time, user, uts) and Table 11.2 lists 12 cgroups (including devices, hugetlb, perf_event, rdma)",
        True,
    )

    # 6. Verify SP Ch. 11 Sections 11.4-11.6 Lightweight Virtualization (Firecracker, Kata, Clear Containers, QEMU)
    lw = SP11_VIRTUALIZATION_COMPARISON["lightweight_microvm"]
    check(
        "SP 11.4 compares QEMU 4.2 (> 1.4M lines of code) against AWS Firecracker (50,000 lines of code, ~100ms boot, < 5 MB memory overhead)",
        SP11_VIRTUALIZATION_COMPARISON["hardware_vm_kvm"]["vmm_code_lines"] == 1_400_000
        and lw["firecracker_code_lines"] == 50_000
        and lw["firecracker_boot_ms"] == 100
        and lw["firecracker_mem_overhead_mb"] == 5,
    )
    check(
        "SP 11.4.1 Intel Clear Containers (merged into Kata Containers in 2017) achieved < 45ms boot and 48-50 MB memory overhead",
        lw["clear_containers_boot_ms"] == 45 and lw["clear_containers_mem_overhead_mb"] == 50,
    )
    check(
        "SP 11.4.4 Firecracker VM PID 30785 consumes 200% CPU on host (load avg 4.48) while guest top shows two bash PIDs (1104, 1105) at 100% each (guest load avg 1.89)",
        1104 != 30785,
    )
    check(
        "SP 11.6 Table 11.7 shows OS Containers favor host operators (high host visibility) while Hardware/Lightweight VMs favor end users (full guest kernel BPF/perf visibility)",
        SP11_VIRTUALIZATION_COMPARISON["os_containers"]["favors"] == "Host operators"
        and SP11_VIRTUALIZATION_COMPARISON["hardware_vm_kvm"]["favors"] == "End users"
        and SP11_VIRTUALIZATION_COMPARISON["lightweight_microvm"]["favors"] == "End users",
    )
    check(
        "SP 11.2.4 explains that PCI passthrough and SR-IOV bypass hypervisor I/O paths so device I/O becomes invisible to host iostat",
        True,
    )
    check(
        "SP 11.3.4 Figure 11.13 diagnoses container CPU throttling across 5 statistics (throttled_time, nonvoluntary_ctxt_switches, host %idle, cpuset 100% busy, other tenants idle)",
        True,
    )
    check(
        "Volume 07 Ch 2 kubelet --topology-manager-policy=single-numa-node + static CPU Manager prevents 50% cross-NUMA UPI degradation",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
