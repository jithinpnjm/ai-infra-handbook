#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.23: Performance methodology: USE, workload characterisation, drill-down."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from perf_methodology_use import (
    LINUX_60S_CHECKLIST,
    amdahl_relative_capacity,
    extrapolate_cpu_max_request_rate,
    littles_law_in_flight,
    md1_response_time,
    usl_relative_capacity,
    weighted_harmonic_mean_rate,
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
    # 1. Linux 60-second checklist (Section 5, SP Ch. 1)
    check("Linux 60-second checklist has 10 commands starting with uptime and ending with top",
          len(LINUX_60S_CHECKLIST) == 10
          and LINUX_60S_CHECKLIST[0] == "uptime"
          and LINUX_60S_CHECKLIST[-1] == "top")

    # 2. Amdahl's law and Gunther's USL (Section 9, SP Ch. 2.6)
    c64 = amdahl_relative_capacity(n_workers=64, alpha_serial=0.05)
    check("Amdahl's law with alpha=0.05 at N=64 yields 15.42x (~15.4x, asymptotic ceiling 20x)",
          c64 == 15.42 and round(1.0 / 0.05, 1) == 20.0)
    usl_16 = usl_relative_capacity(n_workers=16, alpha_contention=0.04, beta_coherence=0.002)
    usl_64 = usl_relative_capacity(n_workers=64, alpha_contention=0.04, beta_coherence=0.002)
    check("USL with beta=0.002 peaks and then declines at high N (C(64) < C(16))",
          usl_64 < usl_16)

    # 3. Little's law L = lambda * W (Section 9)
    in_flight = littles_law_in_flight(arrival_rate_per_sec=200.0, mean_time_in_system_sec=0.050)
    check("Little's law: 200 req/s with 50 ms (0.050 s) average latency equals 10.0 requests in flight",
          in_flight == 10.0)
    gpu_tput = 32.0 / 4.0
    check("Little's law on GPU batch scheduler: 32 sequences with 4 s residence time sustains 8.0 seq/s",
          littles_law_in_flight(gpu_tput, 4.0) == 32.0)

    # 4. M/D/1 queueing response time curve (Section 9, SP Ch. 2.6.5)
    r0 = md1_response_time(1.0, 0.0)
    r60 = md1_response_time(1.0, 0.60)
    r80 = md1_response_time(1.0, 0.80)
    r90 = md1_response_time(1.0, 0.90)
    check("M/D/1 response time with s=1.0 is 1.0 at rho=0, 1.75 (~1.6-1.8) at 60%, 3.0 at 80%, 5.5 at 90%",
          r0 == 1.0 and r60 == 1.75 and r80 == 3.0 and r90 == 5.5)

    # 5. Harmonic mean of transfer rates (Section 11, SP Ch. 2.8)
    hm = weighted_harmonic_mean_rate([(100.0, 50.0), (700.0, 10.0)])
    check("100 MB at 50 MB/s + 700 MB at 10 MB/s has weighted harmonic mean 11.1 MB/s (not 30 MB/s)",
          hm == 11.1)

    # 6. Resource-limit capacity planning extrapolation (Section 10, SP Ch. 2.7.1)
    cap = extrapolate_cpu_max_request_rate(current_req_per_sec=1000.0, num_cpus=16, avg_cpu_util_pct=40.0)
    check("1,000 req/s at 40% across 16 CPUs uses 0.64% CPU/req and extrapolates to 2,500.0 req/s ceiling",
          cap["cpu_pct_per_req"] == 0.64 and cap["max_req_per_sec"] == 2500.0)

    # 7. Additional checks from chapter text
    check("0.3 ns CPU cycle scaled to 1 s puts 100 ns DRAM at ~333 s (~6 min) and 40 ms WAN at ~4 years",
          0.3 < 1.0 < 3.0 < 10.0 < 100.0)
    check("600 GB flash cache fed at 16 MB/s takes ~37,500 s (~10 hours) to warm",
          (600 * 1000) // 16 == 37500)
    check("10 ms request with 9 ms disk reduced to 10 us (0.01 ms) gives 10 / 1.01 = 9.9x speedup",
          round(10.0 / 1.01, 1) == 9.9)
    check("Case 2 fixed-rate 700 samples/s at 20% vs 30% CPU explains 3,500/s vs 2,300/s ceiling",
          700 * (100 // 20) == 3500)
    check("amdahl_relative_capacity raises ValueError on invalid alpha",
          _raises(lambda: amdahl_relative_capacity(8, 1.5)))
    check("md1_response_time raises ValueError at rho=1.0 (infinite queue)",
          _raises(lambda: md1_response_time(1.0, 1.0)))
    check("weighted_harmonic_mean_rate raises ValueError on empty list",
          _raises(lambda: weighted_harmonic_mean_rate([])))

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
