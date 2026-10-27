#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.8: The life of a pod end to end, including what the kernel does."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pod_lifecycle_kernel_trace import (
    compute_pod_startup_intervals,
    verify_gpu_cgroup_device_isolation,
    verify_pod_namespace_inodes,
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
    # 1. Section 8: Pod startup latency breakdown and SLI duration (excluding image pull)
    metrics = compute_pod_startup_intervals(
        created_sec=0.0,
        scheduled_sec=0.2,
        initialized_sec=1.5,
        containers_ready_sec=42.2,
        ready_sec=45.0,
        image_pull_duration_sec=39.0,
    )
    check(
        "compute_pod_startup_intervals calculates total_to_ready_sec=45.0s and pod_start_sli_sec=3.0s (42.0s - 39.0s pull)",
        metrics["total_to_ready_sec"] == 45.0
        and metrics["pod_start_sli_sec"] == 3.0
        and metrics["readiness_probe_sec"] == 2.8,
    )

    # 2. Section 4 & 5: /proc/<pid>/ns inode sharing between pause and app container
    pause_ns = {"net": 4026532500, "ipc": 4026532501, "uts": 4026532502, "cgroup": 4026531835, "mnt": 4026532503, "pid": 4026532504}
    app_ns = {"net": 4026532500, "ipc": 4026532501, "uts": 4026532502, "cgroup": 4026531835, "mnt": 4026532610, "pid": 4026532611}
    ok_ns, _ = verify_pod_namespace_inodes(pause_ns, app_ns, share_process_namespace=False)
    bad_ns, errs_ns = verify_pod_namespace_inodes(pause_ns, pause_ns, share_process_namespace=False)
    check(
        "verify_pod_namespace_inodes confirms shared net/ipc/uts/cgroup and isolated mnt/pid vs pause container",
        ok_ns is True and bad_ns is False and len(errs_ns) == 2,
    )

    # 3. Section 5: GPU device plugin allocation and cgroup v2 eBPF device allow-list isolation
    devs_pod_a = {"/dev/nvidia0", "/dev/nvidia1", "/dev/nvidiactl", "/dev/nvidia-uvm"}
    ok_gpu, _ = verify_gpu_cgroup_device_isolation([0, 1], devs_pod_a, devs_pod_a)
    leaked_gpu, errs_gpu = verify_gpu_cgroup_device_isolation(
        [0, 1],
        devs_pod_a | {"/dev/nvidia2"},
        devs_pod_a,
    )
    check(
        "verify_gpu_cgroup_device_isolation passes 2-GPU pod and flags unallocated /dev/nvidia2 exposure",
        ok_gpu is True and leaked_gpu is False and len(errs_gpu) == 1,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
