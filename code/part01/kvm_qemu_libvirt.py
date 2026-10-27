"""Chapter 1.26 model: Two-dimensional nested paging (EPT/NPT) page-walk memory
accesses, KVM VM-exit classification (in-kernel vs user-space QEMU exits and HLT
idle accounting), IOMMU group isolation validation for VFIO GPU passthrough, and
high-performance libvirt domain XML auditing.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 17
  (section 17.1 virtual machines, hypervisors, CPU modes, uses, and drawbacks).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 11 (section 11.2 hardware virtualization: Config A vs Config B KVM,
  VT-x/AMD-V, VM exits, EPT/NPT 2D page walks, virtio/vhost/VFIO/SR-IOV,
  pidstat -t, perf kvm stat, kvmexits.bt).
"""
from typing import Dict, List, Set


def compute_2d_page_walk_max_reads(guest_levels: int = 4, host_ept_levels: int = 4) -> Dict[str, int]:
    """Compute worst-case memory accesses on a TLB miss under 2D nested paging (EPT/NPT):
    each of guest_levels needs a host_ept_levels walk + 1 read, plus host_ept_levels for the final GPA.
    For 4-level guest + 4-level EPT: 4 * 4 + 4 + 4 = 24 memory accesses (vs 4 on bare metal).
    """
    if guest_levels <= 0 or host_ept_levels <= 0:
        raise ValueError("Page table levels must be positive")
    bare_metal_reads = guest_levels
    nested_reads = guest_levels * (host_ept_levels + 1) + host_ept_levels
    return {
        "bare_metal_reads": bare_metal_reads,
        "nested_2d_reads": nested_reads,
    }


def classify_kvm_exit_reason(exit_reason: str) -> Dict[str, object]:
    """Classify a KVM VM exit reason by whether it is idle (HLT) or active overhead, and where it is handled."""
    idle_exits = {"HLT"}
    userspace_qemu_exits = {"IO_INSTRUCTION", "MMIO"}
    kernel_fastpath_exits = {
        "MSR_WRITE",
        "EXTERNAL_INTERRUPT",
        "PENDING_INTERRUPT",
        "EPT_VIOLATION",
        "CPUID",
        "PREEMPTION_TIMER",
    }
    if exit_reason in idle_exits:
        return {"exit_reason": exit_reason, "is_idle_sleep": True, "handled_in": "host_kernel_kvm"}
    if exit_reason in userspace_qemu_exits:
        return {"exit_reason": exit_reason, "is_idle_sleep": False, "handled_in": "userspace_qemu_proxy"}
    if exit_reason in kernel_fastpath_exits:
        return {"exit_reason": exit_reason, "is_idle_sleep": False, "handled_in": "host_kernel_kvm"}
    raise ValueError(f"Unknown exit reason: {exit_reason}")


def validate_iommu_group_passthrough(
    iommu_group_bdfs: Set[str],
    passed_to_vm_bdfs: Set[str],
    host_critical_bdfs: Set[str],
) -> Dict[str, object]:
    """Verify that all non-bridge devices in an IOMMU group are passed together and none are host-critical."""
    missing_siblings = iommu_group_bdfs - passed_to_vm_bdfs
    host_conflicts = iommu_group_bdfs & host_critical_bdfs
    valid = len(missing_siblings) == 0 and len(host_conflicts) == 0
    return {
        "valid": valid,
        "missing_group_siblings": sorted(missing_siblings),
        "host_critical_conflicts": sorted(host_conflicts),
    }


def audit_gpu_vm_domain_config(
    cpu_mode: str,
    hugepages_enabled: bool,
    memory_locked: bool,
    vcpus_pinned_to_gpu_numa: bool,
    disk_cache_mode: str,
    machine_type: str,
) -> List[str]:
    """Audit a libvirt KVM domain configuration for a GPU-passthrough VM."""
    issues: List[str] = []
    if cpu_mode != "host-passthrough":
        issues.append("cpu_mode_should_be_host_passthrough")
    if not hugepages_enabled:
        issues.append("missing_hugepages_backing")
    if not memory_locked:
        issues.append("missing_locked_memory_for_vfio_dma")
    if not vcpus_pinned_to_gpu_numa:
        issues.append("vcpus_not_pinned_to_gpu_numa_node")
    if disk_cache_mode != "none":
        issues.append("disk_cache_not_none_causes_double_caching")
    if machine_type != "q35":
        issues.append("machine_type_should_be_q35_for_pcie")
    return issues
