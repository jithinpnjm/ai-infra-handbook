"""Chapter 1.24 model: Tracing overhead estimation by event rate (tracepoints vs
kprobes vs uprobes vs ptrace), Ftrace function_graph duration annotation symbols
(+, !, #, *, @, $), bpftrace power-of-2 hist() bucket mapping, and entry/return
tid timestamp delta calculation.

Sources modeled:
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 4 ("Observability Tools": counters, profiling, tracing, sar, /proc,
  /sys, delay accounting, netlink, tracepoints, kprobes, uprobes, USDT, PMCs),
  Chapter 13 ("perf"), Chapter 14 ("Ftrace"), and Chapter 15 ("BPF": BCC and
  bpftrace).
"""
import math
from typing import Dict, List, Tuple


FTRACE_DURATION_MARKS: List[Tuple[int, str]] = [
    (1_000_000, "$"),  # > 1 s
    (100_000, "@"),    # > 100 ms
    (10_000, "*"),     # > 10 ms
    (1_000, "#"),      # > 1 ms
    (100, "!"),        # > 100 us
    (10, "+"),         # > 10 us
]


def classify_event_rate_overhead(events_per_sec: int, mechanism: str = "tracepoint") -> Dict[str, object]:
    """Estimate CPU overhead and safety regime for tracing an event at events_per_sec (SP Ch. 4 & 15)."""
    if events_per_sec < 0:
        raise ValueError("events_per_sec must be non-negative")
    per_event_ns_map = {
        "tracepoint": 100,
        "kprobe": 150,
        "uprobe": 1200,
        "ptrace": 15000,
    }
    if mechanism not in per_event_ns_map:
        raise ValueError(f"Unknown mechanism: {mechanism}")
    cost_ns = per_event_ns_map[mechanism]
    cpu_fraction_pct = round(100.0 * (events_per_sec * cost_ns) / 1e9, 2)
    if events_per_sec < 10_000 and mechanism in {"tracepoint", "kprobe"}:
        regime = "negligible"
    elif events_per_sec >= 100_000 or cpu_fraction_pct >= 5.0:
        regime = "measurable_or_high_caution"
    else:
        regime = "moderate"
    return {
        "events_per_sec": events_per_sec,
        "mechanism": mechanism,
        "estimated_one_core_pct": cpu_fraction_pct,
        "regime": regime,
    }


def ftrace_function_graph_mark(duration_us: float) -> str:
    """Return the Ftrace function_graph overhead symbol (+, !, #, *, @, $ or ' ') for a given duration in us."""
    if duration_us < 0:
        raise ValueError("duration_us must be non-negative")
    for thresh_us, sym in FTRACE_DURATION_MARKS:
        if duration_us > thresh_us:
            return sym
    return " "


def bpftrace_hist_bucket_range(value: int) -> Tuple[int, int]:
    """Return the [low, high) power-of-2 bucket used by bpftrace hist() for a positive integer."""
    if value <= 0:
        return (0, 1)
    k = int(math.floor(math.log2(value)))
    low = 1 << k
    high = 1 << (k + 1)
    return (low, high)


def simulate_bpftrace_latency_map(
    events: List[Tuple[str, int, int]],
) -> List[int]:
    """Simulate bpftrace entry/return pattern: ('enter'|'ret', tid, nsecs) with /@start[tid]/ guard.
    Returns recorded durations in microseconds ((nsecs - @start[tid]) // 1000).
    """
    start_map: Dict[int, int] = {}
    durations_us: List[int] = []
    for kind, tid, nsecs in events:
        if kind == "enter":
            start_map[tid] = nsecs
        elif kind == "ret":
            if tid in start_map:
                durations_us.append((nsecs - start_map[tid]) // 1000)
                del start_map[tid]
        else:
            raise ValueError(f"Unknown event kind: {kind}")
    return durations_us
