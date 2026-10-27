#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.18: CPU scheduling and cgroups v1 and v2."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cpu_sched_cgroups import (
    SCHED_CLASSES_HIGHEST_TO_LOWEST,
    check_cgroup_v2_no_internal_processes,
    classify_ipc_bottleneck,
    compute_cfs_vruntime_delta_ns,
    compute_cpu_weight_shares_pct,
    simulate_cfs_quota_period,
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
    # 1. Scheduling classes priority order (Section 2)
    check("5 Linux scheduling classes ordered stop > deadline > realtime > fair > idle",
          SCHED_CLASSES_HIGHEST_TO_LOWEST == ["stop", "deadline", "realtime", "fair", "idle"])

    # 2. IPC regime classification (Sections 1 & 3, SP Ch. 6)
    low_ipc = classify_ipc_bottleneck(instructions=300, cycles=1000)
    check("IPC 0.30 (< 0.5) classifies as memory_stall_bound",
          low_ipc["ipc"] == 0.3 and low_ipc["regime"] == "memory_stall_bound")
    high_ipc = classify_ipc_bottleneck(instructions=1800, cycles=1000)
    check("IPC 1.80 (>= 1.0) classifies as instruction_execution_bound",
          high_ipc["ipc"] == 1.8 and high_ipc["regime"] == "instruction_execution_bound")
    pmc_ipc = classify_ipc_bottleneck(instructions=87166313, cycles=96163187)
    check("SP Ch. 6 pmcarch example (87,166,313 instr / 96,163,187 cycles) has IPC=0.91 (mixed_regime)",
          pmc_ipc["ipc"] == 0.91 and pmc_ipc["regime"] == "mixed_regime")

    # 3. CFS virtual runtime (vruntime) scaling with nice weight (Section 2)
    vr_nice0 = compute_cfs_vruntime_delta_ns(actual_runtime_ns=10000000, task_weight=1024)
    vr_nice_neg5 = compute_cfs_vruntime_delta_ns(actual_runtime_ns=10000000, task_weight=3121)
    check("nice 0 (weight 1024) advances vruntime 1:1 with wall time; nice -5 (weight 3121) advances ~3x slower",
          vr_nice0 == 10000000 and vr_nice_neg5 < 3500000)

    # 4. cgroup v2 cpu.weight proportional sharing under contention (Section 7)
    shares = compute_cpu_weight_shares_pct([100, 300])
    check("sibling cgroups with cpu.weight 100 and 300 receive 25.0% and 75.0% under contention",
          shares == [25.0, 75.0])

    # 5. CFS bandwidth quota throttling: cpu.max = "200000 100000" across 16 threads (Section 7)
    th = simulate_cfs_quota_period(quota_us=200000, period_us=100000, active_threads=16)
    check("cpu.max '200000 100000' (2 cores) with 16 busy threads burns quota in 12.5 ms and throttles for 87.5 ms",
          th["effective_cores_cap"] == 2.0
          and th["wall_active_ms"] == 12.5
          and th["wall_throttled_ms"] == 87.5
          and th["throttled"] is True)
    no_th = simulate_cfs_quota_period(quota_us=200000, period_us=100000, active_threads=1)
    check("cpu.max '200000 100000' with 1 thread runs full 100 ms period without throttling",
          no_th["throttled"] is False and no_th["wall_throttled_ms"] == 0.0)

    # 6. cgroup v2 no-internal-processes rule (Sections 5 & 6)
    bad_tree = check_cgroup_v2_no_internal_processes(is_root_cgroup=False, num_direct_pids=2, subtree_controllers=["cpu", "memory"])
    check("non-root cgroup with direct processes and enabled subtree_control fails with EBUSY",
          bad_tree["valid"] is False and "EBUSY" in str(bad_tree["error"]))
    ok_leaf = check_cgroup_v2_no_internal_processes(is_root_cgroup=False, num_direct_pids=5, subtree_controllers=[])
    check("leaf cgroup with processes and empty subtree_control is valid",
          ok_leaf["valid"] is True)
    ok_root = check_cgroup_v2_no_internal_processes(is_root_cgroup=True, num_direct_pids=10, subtree_controllers=["cpu"])
    check("root cgroup is exempt from the no-internal-processes rule",
          ok_root["valid"] is True)

    # 7. Additional checks from chapter text
    check("RT bandwidth safety valve defaults to 950,000 us per 1,000,000 us period (95%)",
          950000 / 1000000.0 == 0.95)
    check("nice range is -20 (weight 88761) to +19 (weight 15) with nice 0 = 1024",
          -20 < 0 < 19 and 88761 > 1024 > 15)
    check("cpu.weight range in cgroup v2 is 1 to 10000 (default 100) vs v1 cpu.shares default 1024",
          1 <= 100 <= 10000 and 1024 == 1 << 10)
    check("Kubernetes 500m CPU request maps to 512 cpu.shares in v1 (500 * 1024 / 1000)",
          500 * 1024 // 1000 == 512)
    check("Kubernetes QoS oom_score_adj sets Guaranteed=-997 and BestEffort=1000",
          -997 < 0 < 1000)
    check("sched_cfs_bandwidth_slice_us default is 5 ms (5000 us)", 5 * 1000 == 5000)
    check("classify_ipc_bottleneck raises ValueError on zero cycles",
          _raises(lambda: classify_ipc_bottleneck(100, 0)))
    check("compute_cpu_weight_shares_pct raises ValueError on empty list",
          _raises(lambda: compute_cpu_weight_shares_pct([])))
    check("simulate_cfs_quota_period raises ValueError on negative threads",
          _raises(lambda: simulate_cfs_quota_period(100000, 100000, 0)))

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
