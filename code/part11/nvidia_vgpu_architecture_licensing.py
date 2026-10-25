#!/usr/bin/env python3
"""Chapter 11.23 model: NVIDIA vGPU Architecture, Profiles, Licensing & Volume 11 Validation.

Models:
1. Volume 11 Chapter 1 Deceptive Utilization & Contention Analyzer:
   - H100 80GB HBM3 showing 14-18% (15%) average SM utilization while holding
     72,000-72,100 MiB out of 81,559 MiB (burst overlap 1-in-20 spikes SM to 85%),
   - Scenario 1 contention jump: alone (p99=42ms, 48GB, 35% peak SM) -> with 2nd
     tenant (p99=180ms, 76GB, 92% peak SM).
2. Volume 11 Chapter 5 NVIDIA vGPU Two-Path Architecture, 6-State Device Lifecycle
   (Eligible -> Attached -> Enumerated -> DriverReady -> Entitled -> ApplicationReady -> Drained),
   Host vs Guest diagnostic view (NVIDIA GRID A100-20Q: 45C, 18W/400W, 2000MiB/20000MiB),
   Time-Sliced vGPU vs MIG-Backed vGPU, and 8-Step Maintenance Runbook.
3. Volume 11 Labs 01-04 & Chapter 12 Summary verification markers:
   - Lab 01 H100 6 MIG profiles (0:1g.10gb x7, 1:1g.20gb x4, 2:2g.20gb x3, 3:3g.40gb x2,
     4:4g.40gb x1, 5:7g.80gb x1) and MIG_VALIDATION_COMPLETE,
   - Lab 02 Time-Slicing (1 allocatable -> 4 allocatable after 30s) and TIME_SLICE_A_COMPLETE,
   - Lab 03 Comparative Probe (SHARING_RUNTIME_PROBE_COMPLETE & SHARING_NEIGHBOR_PROBE_COMPLETE),
   - Lab 04 Multi-Tenant Incident Triage (DIAGNOSTIC_GPU_OK & QUOTA_DENIAL_RECOVERY_CHECK).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


VGPU_LIFECYCLE_STATES: List[str] = [
    "Eligible",
    "Attached",
    "Enumerated",
    "DriverReady",
    "Entitled",
    "ApplicationReady",
    "Drained",
]

VGPU_FIVE_RESPONSIBILITY_LAYERS: List[str] = [
    "Physical host",
    "Hypervisor",
    "Guest",
    "License path",
    "Operations plane",
]

LAB01_H100_MIG_CATALOG: List[Dict[str, object]] = [
    {"id": 0, "name": "1g.10gb", "instances": 7, "memory_gb": 10},
    {"id": 1, "name": "1g.20gb", "instances": 4, "memory_gb": 20},
    {"id": 2, "name": "2g.20gb", "instances": 3, "memory_gb": 20},
    {"id": 3, "name": "3g.40gb", "instances": 2, "memory_gb": 40},
    {"id": 4, "name": "4g.40gb", "instances": 1, "memory_gb": 40},
    {"id": 5, "name": "7g.80gb", "instances": 1, "memory_gb": 80},
]


@dataclass(frozen=True)
class VgpuLifecycleContext:
    host_gpu_healthy: bool
    vgpu_manager_version: str
    guest_driver_version: str
    matrix_compatible: bool
    vm_profile_attached: bool
    guest_pci_enumerated: bool
    nls_license_acquired: bool
    smoke_test_passed: bool


def evaluate_vgpu_state_machine(ctx: VgpuLifecycleContext) -> Dict[str, str]:
    """Evaluates Volume 11 Chapter 5 Figure 11.5.3 vGPU state transitions and failure layer."""
    if not ctx.host_gpu_healthy:
        return {
            "current_state": "UnhealthyHost",
            "failed_layer": "Physical host",
            "diagnostic_cmd": "nvidia-smi && nvidia-smi vgpu -s",
            "remediation": "Cordon/evacuate host and repair physical GPU or Virtual GPU Manager before guest debugging",
        }
    if not ctx.vm_profile_attached:
        return {
            "current_state": "Eligible",
            "failed_layer": "Hypervisor",
            "diagnostic_cmd": "nvidia-smi vgpu && virsh dumpxml <vm-name> | grep vgpu",
            "remediation": "Verify profile slot capacity (nvidia-smi vgpu -c) and attach valid vGPU profile to VM",
        }
    if not ctx.guest_pci_enumerated:
        return {
            "current_state": "Attached",
            "failed_layer": "Hypervisor / Guest PCI",
            "diagnostic_cmd": "lspci | grep NVIDIA",
            "remediation": "Inspect VM hardware configuration, IOMMU/VFIO attachment, and guest PCIe bus enumeration",
        }
    if not ctx.matrix_compatible:
        return {
            "current_state": "Enumerated",
            "failed_layer": "Guest (Incompatible Host/Guest Driver Matrix)",
            "diagnostic_cmd": "nvidia-smi --query-gpu=driver_version,vbios_version --format=csv",
            "remediation": f"Restore tested pairing: host manager {ctx.vgpu_manager_version} and guest {ctx.guest_driver_version} conflict",
        }
    if not ctx.nls_license_acquired:
        return {
            "current_state": "DriverReady",
            "failed_layer": "License path (NVIDIA License System NLS)",
            "diagnostic_cmd": "nvidia-smi -q | grep -A 5 'vGPU Software Licensed Product'",
            "remediation": "Repair guest DNS/network/TLS path to NLS/DLS license server and verify profile entitlement",
        }
    if not ctx.smoke_test_passed:
        return {
            "current_state": "Entitled",
            "failed_layer": "Application workload",
            "diagnostic_cmd": "kubectl logs / guest application smoke test",
            "remediation": "Inspect application CUDA initialization and framebuffer headroom",
        }
    return {
        "current_state": "ApplicationReady",
        "failed_layer": "None (Healthy)",
        "diagnostic_cmd": "nvidia-smi vgpu -q",
        "remediation": "vGPU service contract verified end-to-end",
    }


def analyze_volume11_ch1_deceptive_utilization(
    sampled_util_pct: List[int] = [15, 18, 14],
    sampled_mem_used_mib: List[int] = [72000, 72100, 72050],
    total_mem_mib: int = 81559,
    overlap_probability: float = 0.05,  # 1-in-20 request overlap
    overlap_sm_pct: int = 85,
    alone_p99_ms: int = 42,
    alone_mem_gb: int = 48,
    alone_peak_sm_pct: int = 35,
    co_tenant_p99_ms: int = 180,
    co_tenant_mem_gb: int = 76,
    co_tenant_peak_sm_pct: int = 92,
) -> Dict[str, object]:
    """Models Volume 11 Chapter 1 deceptive utilization report and Scenario 1 latency jump."""
    avg_util = round(sum(sampled_util_pct) / len(sampled_util_pct), 2)
    max_mem_mib = max(sampled_mem_used_mib)
    mem_used_pct = round((max_mem_mib / total_mem_mib) * 100.0, 1)
    p99_degradation_ratio = round(co_tenant_p99_ms / alone_p99_ms, 2)

    return {
        "avg_sampled_util_pct": avg_util,
        "max_mem_used_mib": max_mem_mib,
        "total_mem_mib": total_mem_mib,
        "mem_used_pct": mem_used_pct,
        "overlap_event_rate": overlap_probability,
        "overlap_sm_spike_pct": overlap_sm_pct,
        "alone_p99_ms": alone_p99_ms,
        "alone_mem_gb": alone_mem_gb,
        "alone_peak_sm_pct": alone_peak_sm_pct,
        "co_tenant_p99_ms": co_tenant_p99_ms,
        "co_tenant_mem_gb": co_tenant_mem_gb,
        "co_tenant_peak_sm_pct": co_tenant_peak_sm_pct,
        "p99_degradation_ratio": p99_degradation_ratio,
        "safe_to_time_slice_without_load_test": False,
    }
