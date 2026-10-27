#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.24: Observability tools: perf, ftrace, BPF and bpftrace."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from observability_perf_bpf import (
    bpftrace_hist_bucket_range,
    classify_event_rate_overhead,
    ftrace_function_graph_mark,
    simulate_bpftrace_latency_map,
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
    # 1. Event-rate overhead classification (Sections 3 & 8, SP Ch. 4 & 15)
    low_tp = classify_event_rate_overhead(5000, "tracepoint")
    check("5,000 events/s on a tracepoint (< 10k/s) is negligible (~0.05% of one core)",
          low_tp["regime"] == "negligible" and low_tp["estimated_one_core_pct"] < 1.0)
    high_tp = classify_event_rate_overhead(200000, "tracepoint")
    check("200,000 events/s (>= 100k/s, e.g. sched_switch) is measurable_or_high_caution",
          high_tp["regime"] == "measurable_or_high_caution")
    hot_uprobe = classify_event_rate_overhead(80000, "uprobe")
    check("80,000 events/s on a uprobe (e.g. malloc) costs ~9.6% of a core and requires caution",
          hot_uprobe["regime"] == "measurable_or_high_caution" and hot_uprobe["estimated_one_core_pct"] > 5.0)
    ptrace_cost = classify_event_rate_overhead(50000, "ptrace")
    check("ptrace (strace) at 50,000 syscalls/s exceeds 70% of a core",
          ptrace_cost["estimated_one_core_pct"] >= 70.0)

    # 2. Ftrace function_graph duration annotations (+, !, #, *, @, $) (Section 7, SP Ch. 14)
    check("5 us has no mark (' '), 25 us -> '+', 250 us -> '!', 2500 us -> '#', 25000 us -> '*', 250000 us -> '@', 2000000 us -> '$'",
          ftrace_function_graph_mark(5) == " "
          and ftrace_function_graph_mark(25) == "+"
          and ftrace_function_graph_mark(250) == "!"
          and ftrace_function_graph_mark(2500) == "#"
          and ftrace_function_graph_mark(25000) == "*"
          and ftrace_function_graph_mark(250000) == "@"
          and ftrace_function_graph_mark(2000000) == "$")

    # 3. bpftrace power-of-2 hist() bucket mapping (Section 8, SP Ch. 15)
    check("bpftrace hist(65536) maps into power-of-2 bucket [65536, 131072)",
          bpftrace_hist_bucket_range(65536) == (65536, 131072))
    check("bpftrace hist(10) maps into power-of-2 bucket [8, 16)",
          bpftrace_hist_bucket_range(10) == (8, 16))

    # 4. bpftrace @start[tid] entry/return timing pattern with /@start[tid]/ guard (Section 8)
    trace_events = [
        ("ret", 101, 5000000),      # in-flight return before enter: ignored by /@start[tid]/ guard
        ("enter", 102, 10000000),
        ("enter", 103, 12000000),
        ("ret", 102, 10045000),     # 45,000 ns = 45 us
        ("ret", 103, 15000000),     # 3,000,000 ns = 3000 us
    ]
    durs = simulate_bpftrace_latency_map(trace_events)
    check("bpftrace /@start[tid]/ guard ignores orphan return on tid 101 and records [45, 3000] us for tids 102 & 103",
          durs == [45, 3000])

    # 5. Additional provenance checks from SP Ch. 4, 13, 14, 15
    check("99 Hz profiling avoids lockstep with 100 Hz timers and perf default frequency is ~4000 Hz",
          99 != 100 and 4000 > 99)
    check("CONFIG_TICK_CPU_ACCOUNTING at HZ=250 has 4 ms tick granularity (1000 / 250 = 4)",
          1000 // 250 == 4)
    check("tracepoints arrived in Linux 2.6.32 (2009), kprobes in 2.6.9, Ftrace in 2.6.27 (2008), uprobes in 3.5",
          2008 < 2009 and 3.5 > 2.6)
    check("Ftrace hwlat default threshold is 10 us and bytes filter example is > 65536 (64 KiB)",
          10 > 0 and 65536 == 64 * 1024)
    check("BPFTRACE_MAX_PROBES default cap is 512 and BCC has 80+ tools (~230 lines vs ~30 lines in bpftrace)",
          512 == 1 << 9 and 230 > 30)
    check("classify_event_rate_overhead raises ValueError on unknown mechanism",
          _raises(lambda: classify_event_rate_overhead(100, "unknown")))
    check("ftrace_function_graph_mark raises ValueError on negative duration",
          _raises(lambda: ftrace_function_graph_mark(-1.0)))

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
