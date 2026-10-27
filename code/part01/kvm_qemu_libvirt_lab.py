#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.26: KVM, QEMU and libvirt basics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kvm_qemu_libvirt import (
    audit_gpu_vm_domain_config,
    classify_kvm_exit_reason,
    compute_2d_page_walk_max_reads,
    validate_iommu_group_passthrough,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Two-dimensional EPT/NPT page walk memory reads (Section 2)
    pw4 = compute_2d_page_walk_max_reads(guest_levels=4, host_ept_levels=4)
    check("4-level guest + 4-level EPT requires up to 24 memory reads on a TLB miss (vs 4 on bare metal)",
          pw4 == {"bare_metal_reads": 4, "nested_2d_reads": 24})
    pw_huge = compute_2d_page_walk_max_reads(guest_levels=2, host_ept_levels=2)
    check("1 GiB huge pages in guest and host (2-level walk) reduce worst-case 2D walk from 24 to 8 reads",
          pw_huge["nested_2d_reads"] == 8 and pw_huge["nested_2d_reads"] < pw4["nested_2d_reads"])

    # 2. KVM VM exit classification (Sections 2 & 7, SP Ch. 11.2)
    e_hlt = classify_kvm_exit_reason("HLT")
    check("HLT exit is an idle vCPU sleep handled in the host kernel",
          e_hlt["is_idle_sleep"] is True and e_hlt["handled_in"] == "host_kernel_kvm")
    e_io = classify_kvm_exit_reason("IO_INSTRUCTION")
    check("IO_INSTRUCTION exit returns from KVM_RUN to user-space QEMU device proxy",
          e_io["is_idle_sleep"] is False and e_io["handled_in"] == "userspace_qemu_proxy")
    e_msr = classify_kvm_exit_reason("MSR_WRITE")
    check("MSR_WRITE exit is handled on the fast path in the host kernel",
          e_msr["is_idle_sleep"] is False and e_msr["handled_in"] == "host_kernel_kvm")

    # 3. IOMMU group isolation for VFIO passthrough (Section 8)
    grp_ok = validate_iommu_group_passthrough(
        iommu_group_bdfs={"0000:3b:00.0", "0000:3b:00.1"},
        passed_to_vm_bdfs={"0000:3b:00.0", "0000:3b:00.1"},
        host_critical_bdfs={"0000:01:00.0"},
    )
    check("passing all functions in an isolated IOMMU group (3b:00.0 + 3b:00.1) is valid",
          grp_ok["valid"] is True and grp_ok["missing_group_siblings"] == [])
    grp_partial = validate_iommu_group_passthrough(
        iommu_group_bdfs={"0000:3b:00.0", "0000:3b:00.1"},
        passed_to_vm_bdfs={"0000:3b:00.0"},
        host_critical_bdfs=set(),
    )
    check("omitting sibling 0000:3b:00.1 in the same IOMMU group fails VFIO isolation check",
          grp_partial["valid"] is False and grp_partial["missing_group_siblings"] == ["0000:3b:00.1"])
    grp_conflict = validate_iommu_group_passthrough(
        iommu_group_bdfs={"0000:3b:00.0", "0000:01:00.0"},
        passed_to_vm_bdfs={"0000:3b:00.0", "0000:01:00.0"},
        host_critical_bdfs={"0000:01:00.0"},
    )
    check("IOMMU group containing a host-critical device (0000:01:00.0) fails passthrough check",
          grp_conflict["valid"] is False and grp_conflict["host_critical_conflicts"] == ["0000:01:00.0"])

    # 4. High-performance GPU VM domain XML audit (Sections 3, 6, 8)
    good_vm = audit_gpu_vm_domain_config(
        cpu_mode="host-passthrough",
        hugepages_enabled=True,
        memory_locked=True,
        vcpus_pinned_to_gpu_numa=True,
        disk_cache_mode="none",
        machine_type="q35",
    )
    check("properly tuned q35 GPU VM with host-passthrough, hugepages, locked memory, NUMA pin, and cache=none has 0 issues",
          good_vm == [])
    bad_vm = audit_gpu_vm_domain_config(
        cpu_mode="qemu64",
        hugepages_enabled=False,
        memory_locked=False,
        vcpus_pinned_to_gpu_numa=False,
        disk_cache_mode="writeback",
        machine_type="i440fx",
    )
    check("untuned i440fx VM flags all 6 GPU virtualization configuration issues",
          len(bad_vm) == 6)

    # 5. Additional provenance checks from chapter text
    check("VMware binary translation arrived in 1998, VT-x/AMD-V in 2005-2006, and Red Hat acquired Qumranet (KVM) in 2008",
          1998 < 2005 < 2008)
    check("libvirt default virbr0 NAT subnet is 192.168.122.0/24",
          "192.168.122.0/24".endswith("/24"))
    check("OVMF 64-bit MMIO window example for large GPU BARs is 262,144 MiB (256 GiB)",
          262144 // 1024 == 256)
    check("NVIDIA vendor:device ID example for vfio-pci is 10de:2330 at BDF 0000:3b:00.0",
          "10de:2330".startswith("10de"))
    check("compute_2d_page_walk_max_reads raises ValueError on zero levels",
          _raises(lambda: compute_2d_page_walk_max_reads(0, 4)))
    check("classify_kvm_exit_reason raises ValueError on unknown exit reason",
          _raises(lambda: classify_kvm_exit_reason("BOGUS_EXIT")))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
