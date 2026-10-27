#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.27: Cloud computing and virtualization internals for Linux engineers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cloud_virt_internals import (
    compute_cloud_gpu_effective_cost,
    compute_shares_burst_vs_contended_drop,
    diagnose_container_cpu_limit_cause,
    parse_proc_status_nspid,
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
    # 1. Container CPU throttling 5-fact decision flow (Section 5, SP Ch. 11.3.4)
    d_quota = diagnose_container_cpu_limit_cause(
        throttled_time_increasing=True,
        involuntary_ctxt_switches_increasing=False,
        host_has_idle_cpus=True,
        cpuset_cpus_100pct_busy=False,
        other_tenants_idle=True,
    )
    check("rising throttled_usec with idle host CPUs diagnoses cfs_bandwidth_quota_cap_binding",
          d_quota == "cfs_bandwidth_quota_cap_binding")

    d_cpuset = diagnose_container_cpu_limit_cause(
        throttled_time_increasing=False,
        involuntary_ctxt_switches_increasing=True,
        host_has_idle_cpus=True,
        cpuset_cpus_100pct_busy=True,
        other_tenants_idle=True,
    )
    check("no quota throttling + 100% busy cpuset cores while host has other idle CPUs diagnoses cpuset_cores_saturated",
          d_cpuset == "cpuset_cores_saturated")

    d_shares = diagnose_container_cpu_limit_cause(
        throttled_time_increasing=False,
        involuntary_ctxt_switches_increasing=True,
        host_has_idle_cpus=False,
        cpuset_cpus_100pct_busy=False,
        other_tenants_idle=False,
    )
    check("no quota throttling + rising involuntary context switches + busy neighbors diagnoses cpu_shares_contention",
          d_shares == "cpu_shares_contention_with_busy_neighbors")

    # 2. CPU shares burst vs contended 'bait-and-switch' drop (Section 2, SP Ch. 11.3.3)
    s_two = compute_shares_burst_vs_contended_drop(container_shares=10, sibling_busy_shares=[30])
    check("10 shares vs 30 busy sibling shares gets 25.0% under contention",
          s_two["contended_share_pct"] == 25.0 and s_two["slowdown_factor_x"] == 4.0)
    s_all = compute_shares_burst_vs_contended_drop(container_shares=10, sibling_busy_shares=[90])
    check("10 shares out of 100 total busy shares drops from 100% burst to 10.0% (10.0x slowdown)",
          s_all["contended_share_pct"] == 10.0 and s_all["slowdown_factor_x"] == 10.0)

    # 3. Host-to-container NSpid mapping (Section 6, SP Ch. 11.3.4)
    ns = parse_proc_status_nspid("NSpid:\t4915\t753")
    check("'NSpid: 4915 753' maps host_pid=4915 to container_pid=753 (depth 1)",
          ns == {"host_pid": 4915, "container_pid": 753, "nesting_depth": 1})

    # 4. Cloud GPU cost and goodput model (Section 4)
    cost_80 = compute_cloud_gpu_effective_cost(
        num_gpus=64,
        useful_gpu_hours_needed=640.0,
        price_per_gpu_hour=3.0,
        goodput_fraction=0.80,
        storage_and_egress_usd=200.0,
    )
    check("640 useful GPU-h at 80% goodput requires 800 paid GPU-h (12.5 wall h on 64 GPUs) = $2,600 total",
          cost_80["paid_gpu_hours"] == 800.0
          and cost_80["wall_clock_hours"] == 12.5
          and cost_80["total_cost_usd"] == 2600.0)

    # 5. Additional provenance checks from SP Ch. 11 and SCL Ch. 17
    check("EC2 hardware VMs launched in 2006, managed containers ~2017, Firecracker microVMs in 2019",
          2006 < 2017 < 2019)
    check("Clear Containers overhead is ~48-50 MB vs Firecracker < 5 MB (~100 ms boot)",
          5 < 48 <= 50 and 100 > 0)
    check("SCL Ch. 17 cloud HPC VM performance drop vs bare metal is 5-15%",
          5 < 10 < 15)
    check("SCL Ch. 17 cloud filesystem test simulates checkpoint dumps every 5 minutes",
          5 * 60 == 300)
    check("compute_shares_burst_vs_contended_drop raises ValueError on zero shares",
          _raises(lambda: compute_shares_burst_vs_contended_drop(0, [10])))
    check("parse_proc_status_nspid raises ValueError on empty string",
          _raises(lambda: parse_proc_status_nspid("NSpid:")))
    check("compute_cloud_gpu_effective_cost raises ValueError on zero goodput",
          _raises(lambda: compute_cloud_gpu_effective_cost(8, 100.0, 2.0, 0.0)))

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
