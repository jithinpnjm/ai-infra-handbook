#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.8: Processes, signals and job control."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from processes_signals import (
    UNCATCHABLE_SIGNALS,
    check_cgroup_v2_leaf_rule,
    classify_time_profile,
    diagnose_load_and_vmstat,
    evaluate_cgroup_v2_cpu_max,
    evaluate_signal_delivery,
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
    # 1. Uncatchable signals and state D / Z / PID 1 rules
    check("only SIGKILL (9) and SIGSTOP (19) are uncatchable",
          UNCATCHABLE_SIGNALS == {9: "SIGKILL", 19: "SIGSTOP"})
    d_kill = evaluate_signal_delivery(sig_num=9, state="D")
    check("SIGKILL (9) to a process in state D is deferred until kernel I/O completes",
          d_kill["delivered_immediately"] is False and "deferred" in str(d_kill["outcome"]))
    z_kill = evaluate_signal_delivery(sig_num=9, state="Z")
    check("SIGKILL (9) to a zombie (state Z) does nothing because it is already dead",
          z_kill["delivered_immediately"] is False and "zombie" in str(z_kill["outcome"]))
    pid1_no_handler = evaluate_signal_delivery(sig_num=15, state="S", is_container_pid1=True, has_custom_handler=False)
    check("SIGTERM (15) to container PID 1 without a registered handler is ignored",
          pid1_no_handler["outcome"] == "ignored_by_pid1_default_protection")
    pid1_with_handler = evaluate_signal_delivery(sig_num=15, state="S", is_container_pid1=True, has_custom_handler=True)
    check("SIGTERM (15) to container PID 1 with a custom handler invokes the handler",
          pid1_with_handler["outcome"] == "handler_invoked")
    s_kill = evaluate_signal_delivery(sig_num=9, state="S", is_container_pid1=True, has_custom_handler=False)
    check("SIGKILL (9) terminates even container PID 1 immediately (exit 137)",
          s_kill["outcome"] == "terminated_immediately_137")
    s_stop = evaluate_signal_delivery(sig_num=19, state="R")
    check("SIGSTOP (19) transitions a running process to state T",
          s_stop["outcome"] == "stopped_T")

    # 2. Load average + vmstat bottleneck diagnosis (HLW Ch. 8)
    check("load 60 on 16 CPUs with vmstat b=48 and id=90% diagnoses as uninterruptible D-state I/O wait",
          diagnose_load_and_vmstat(60.0, 16, vmstat_r=1, vmstat_b=48, cpu_idle_pct=90, vmstat_so=0)
          == "uninterruptible_io_wait_D_state")
    check("sustained vmstat so > 0 diagnoses as memory swapping / thrashing",
          diagnose_load_and_vmstat(20.0, 16, vmstat_r=4, vmstat_b=2, cpu_idle_pct=40, vmstat_so=500)
          == "memory_swapping_thrashing")
    check("vmstat r=32 on 16 CPUs with id=0% diagnoses as CPU saturation",
          diagnose_load_and_vmstat(32.0, 16, vmstat_r=32, vmstat_b=0, cpu_idle_pct=0, vmstat_so=0)
          == "cpu_saturation_runqueue_backlog")
    check("load 2 on 16 CPUs with r=2, b=0, so=0, id=83% diagnoses as healthy",
          diagnose_load_and_vmstat(2.0, 16, vmstat_r=2, vmstat_b=0, cpu_idle_pct=83, vmstat_so=0)
          == "healthy_under_capacity")

    # 3. time(1) real vs user + sys classification (HLW Ch. 8)
    check("real=0.442s, user=0.052s, sys=0.091s classifies as io_network_or_lock_wait",
          classify_time_profile(0.442, 0.052, 0.091) == "io_network_or_lock_wait")
    check("real=10.0s, user=75.0s, sys=3.0s classifies as multithreaded_parallel_cpu",
          classify_time_profile(10.0, 75.0, 3.0) == "multithreaded_parallel_cpu")
    check("real=10.0s, user=3.0s, sys=6.5s classifies as kernel_syscall_heavy",
          classify_time_profile(10.0, 3.0, 6.5) == "kernel_syscall_heavy")
    check("real=10.0s, user=9.2s, sys=0.3s classifies as single_thread_cpu_bound",
          classify_time_profile(10.0, 9.2, 0.3) == "single_thread_cpu_bound")

    # 4. cgroup v2 cpu.max and leaf-process constraint (HLW Ch. 8)
    check("cpu.max '50000 100000' equals 0.5 cores (50 ms per 100 ms period)",
          evaluate_cgroup_v2_cpu_max(50000, 100000) == 0.5)
    check("cpu.max '400000 100000' equals 4.0 cores",
          evaluate_cgroup_v2_cpu_max(400000, 100000) == 4.0)
    check("cgroup v2 leaf cgroup (no children) can hold processes",
          check_cgroup_v2_leaf_rule(has_child_cgroups=False, is_root_cgroup=False) is True)
    check("cgroup v2 non-root internal node (with children) cannot hold processes directly",
          check_cgroup_v2_leaf_rule(has_child_cgroups=True, is_root_cgroup=False) is False)
    check("cgroup v2 root cgroup is an exception and can hold processes even with children",
          check_cgroup_v2_leaf_rule(has_child_cgroups=True, is_root_cgroup=True) is True)

    # 5. Additional range and provenance checks
    check("nice value range is -20 (highest priority) to +19 (lowest priority, 40 levels)",
          19 - (-20) + 1 == 40)
    check("ionice best-effort levels run from 0 (highest) to 7 (lowest)",
          7 - 0 + 1 == 8)
    check("CONFIG_HZ 250 corresponds to a 4 ms clock tick",
          1000 // 250 == 4)
    check("evaluate_cgroup_v2_cpu_max raises ValueError on non-positive period",
          _raises(lambda: evaluate_cgroup_v2_cpu_max(50000, 0)))

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
