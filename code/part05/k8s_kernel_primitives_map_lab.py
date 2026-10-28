#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.26: How Kubernetes uses the Linux kernel: a complete map."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from k8s_kernel_primitives_map import (
    audit_gpu_node_kernel_sysctls,
    check_kernel_version_features,
    simulate_cgroup_v2_cpu_and_memory,
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
    # 1. Section 3 & PK Ch. 12: 8 threads on a 2-CPU limit burn 200ms quota in 25ms and throttle for 75ms!
    cg = simulate_cgroup_v2_cpu_and_memory(
        cpu_limit_cores=2.0,
        active_threads=8,
        period_ms=100.0,
        anon_rss_mi=40000,
        tmpfs_shm_mi=32000,
        active_file_cache_mi=10000,
        inactive_file_cache_mi=18000,
        kernel_slab_mi=2000,
        memory_max_mi=80000,
    )
    check(
        "8 threads on 2-CPU limit run for 25.0ms and stall for 75.0ms; working_set (84000 MiB = current 102000 - inactive 18000) triggers OOM (>80000 MiB)",
        cg["wall_active_ms"] == 25.0
        and cg["throttled_wall_ms"] == 75.0
        and cg["memory_current_mi"] == 102000
        and cg["working_set_mi"] == 84000
        and cg["oom_triggered"] is True,
    )

    # 2. Section 9: GPU node sysctl & protectKernelDefaults auditor
    good_sysctls = {
        "vm.overcommit_memory": 1,
        "kernel.panic": 10,
        "kernel.panic_on_oops": 1,
        "net.ipv4.ip_forward": 1,
        "net.bridge.bridge-nf-call-iptables": 1,
        "kernel.numa_balancing": 0,
        "net.ipv4.conf.all.rp_filter": 0,
    }
    bad_sysctls = {
        "vm.overcommit_memory": 0,
        "kernel.panic": 0,
        "kernel.panic_on_oops": 0,
        "net.ipv4.ip_forward": 0,
        "net.bridge.bridge-nf-call-iptables": 0,
        "kernel.numa_balancing": 1,
        "net.ipv4.conf.all.rp_filter": 1,
    }
    ok_sys, _ = audit_gpu_node_kernel_sysctls(good_sysctls)
    bad_sys, errs_sys = audit_gpu_node_kernel_sysctls(bad_sysctls)
    check(
        "audit_gpu_node_kernel_sysctls passes compliant GPU node and flags 7 sysctl / protectKernelDefaults violations",
        ok_sys is True and bad_sys is False and len(errs_sys) == 7,
    )

    # 3. Section 2, 6, 9: Kernel version capability matrix (5.15 vs 6.8)
    k515 = check_kernel_version_features(5, 15)
    k68 = check_kernel_version_features(6, 8)
    check(
        "Kernel 5.15 lacks idmapped_overlay_userns_pods (5.19+) and netkit (6.7+), whereas 6.8 supports all 6 features",
        k515["idmapped_mounts"] is True
        and k515["idmapped_overlay_userns_pods"] is False
        and all(k68.values()),
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
