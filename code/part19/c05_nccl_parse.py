#!/usr/bin/env python3
"""Parse nccl-tests output and flag the classic failure signatures.

Usage:
  c05_nccl_parse.py FILE --ranks 16 [--link-gbps 400] [--collective all_reduce]
                    [--min-eff 0.8] [--max-small-us 500] [--baseline FILE]
                    [--column oop|inplace] [--json]
Exit status: 0 when no flag is raised, 1 when any flag is raised, 2 on bad input.

The table layout handled is: size count type redop [root] time algbw busbw wrong,
then the same four numbers again for the in-place half. The root column is
optional, so both the older layout (no root) and the newer layout parse.
Rows are recognised by token shape, not by header text.
"""
import argparse
import json
import re
import statistics
import sys
from dataclasses import dataclass, field
from typing import Optional

GB = 1e9  # nccl-tests reports GB/s with GB = 1e9 bytes (checked against a real table)

BUSBW_FACTORS = {
    "all_reduce": lambda n: 2 * (n - 1) / n,
    "reduce_scatter": lambda n: (n - 1) / n,
    "all_gather": lambda n: (n - 1) / n,
    "alltoall": lambda n: (n - 1) / n,
    "broadcast": lambda n: 1.0,
    "reduce": lambda n: 1.0,
}


def busbw_factor(collective: str, n: int) -> float:
    """Correction factor from nccl-tests doc/PERFORMANCE.md."""
    return BUSBW_FACTORS[collective](n)


def algbw_gbs(size_bytes: int, time_us: float) -> float:
    return size_bytes / (time_us * 1e-6) / GB


@dataclass
class Half:
    time_us: float
    algbw: float
    busbw: float
    wrong: float


@dataclass
class Row:
    size: int
    count: int
    dtype: str
    redop: str
    root: Optional[int]
    oop: Half
    inplace: Half


@dataclass
class Run:
    rows: list = field(default_factory=list)
    transport: Optional[str] = None      # "Socket" if any rank used it, else the last network named
    transports: set = field(default_factory=set)
    ib_disabled_by_env: bool = False
    oob_values: Optional[int] = None     # from "Out of bounds values"
    avg_busbw: Optional[float] = None    # from "Avg bus bandwidth"


_NUM = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")


def _num(tok):
    if tok.upper() == "N/A":
        return float("nan")
    return float(tok) if _NUM.match(tok) else None


def _parse_row(line: str):
    t = line.split()
    if len(t) < 12 or not t[0].isdigit() or not t[1].isdigit():
        return None
    if not (t[2].isalpha() and t[3].isalpha()):
        return None
    nums = [_num(x) for x in t[4:]]
    if any(x is None for x in nums):
        return None
    if len(nums) == 9:
        root, vals = int(nums[0]), nums[1:]
    elif len(nums) == 8:
        root, vals = None, nums
    else:
        return None
    return Row(int(t[0]), int(t[1]), t[2], t[3], root,
               Half(*vals[0:4]), Half(*vals[4:8]))


def parse(text: str) -> Run:
    run = Run()
    for raw in text.splitlines():
        line = raw.strip()
        if "NCCL_IB_DISABLE set by environment to 1" in line:
            run.ib_disabled_by_env = True
        m = re.search(r"Using network (\w+)", line)
        if m:
            run.transports.add(m.group(1))
            run.transport = "Socket" if "Socket" in run.transports else m.group(1)
        m = re.search(r"Out of bounds values\s*:\s*(\d+)", line)
        if m:
            run.oob_values = int(m.group(1))
        m = re.search(r"Avg bus bandwidth\s*:\s*([\d.]+)", line)
        if m:
            run.avg_busbw = float(m.group(1))
        if line.startswith("#"):
            continue
        row = _parse_row(line)
        if row:
            run.rows.append(row)
    return run


def _half(row: Row, column: str) -> Half:
    return row.inplace if column == "inplace" else row.oop


def _bad(w):
    """True for a non-zero count. N/A (check not run) parses to nan and is not counted."""
    return w == w and w != 0


def check_arithmetic(run: Run, ranks: int, collective: str, tol: float = 0.02):
    """Rows whose algbw or busbw disagree with size, time and the factor."""
    bad = []
    f = busbw_factor(collective, ranks)
    for r in run.rows:
        for name, h in (("oop", r.oop), ("inplace", r.inplace)):
            a = algbw_gbs(r.size, h.time_us)
            # nccl-tests prints two decimals, so allow rounding on small values
            if abs(a - h.algbw) > max(0.011, tol * a) or abs(a * f - h.busbw) > max(0.011, tol * a * f):
                bad.append((r.size, name))
    return bad


def analyse(run: Run, ranks: int, link_gbps: Optional[float], collective: str = "all_reduce",
            min_eff: float = 0.8, max_small_us: Optional[float] = None,
            collapse_ratio: float = 0.6, column: str = "oop",
            baseline: Optional[Run] = None):
    """Return (summary dict, list of flag strings)."""
    flags = []
    if not run.rows:
        return {"rows": 0}, ["NO_ROWS"]
    link_gbs = None if link_gbps is None else link_gbps / 8.0
    rows = sorted(run.rows, key=lambda r: r.size)
    bus = [_half(r, column).busbw for r in rows]

    # 1. data corruption: any non-zero #wrong in either half, or the summary line
    wrong = [r.size for r in rows if _bad(r.oop.wrong) or _bad(r.inplace.wrong)]
    if wrong or (run.oob_values or 0) > 0:
        flags.append("WRONG_NONZERO")

    # 2. plateau below the link rate: mean of the three largest sizes
    top = bus[-3:]
    plateau = statistics.mean(top)
    eff = None if link_gbs is None else plateau / link_gbs
    if eff is not None and eff < min_eff:
        flags.append("PLATEAU_BELOW_LINK_RATE")

    # 3. collapse mid-curve: a larger size falls well below the best so far
    best = 0.0
    for b in bus:
        if best and b < collapse_ratio * best:
            flags.append("MID_CURVE_COLLAPSE")
            break
        best = max(best, b)

    # 4. latency at the smallest size
    small_us = _half(rows[0], column).time_us
    if max_small_us is not None and small_us > max_small_us:
        flags.append("HIGH_SMALL_MESSAGE_LATENCY")

    # 5. transport evidence from the log
    if run.transport and run.transport.lower() == "socket":
        flags.append("SOCKET_TRANSPORT")

    # 6. arithmetic does not hold: the table is not what the formulas say
    if check_arithmetic(run, ranks, collective):
        flags.append("ARITHMETIC_MISMATCH")

    # 7. regression against a baseline run of the same shape
    ratio = None
    if baseline is not None and baseline.rows:
        base_bus = [_half(r, column).busbw
                    for r in sorted(baseline.rows, key=lambda r: r.size)][-3:]
        ratio = plateau / statistics.mean(base_bus)
        if ratio < min_eff:
            flags.append("BELOW_BASELINE")

    summary = {
        "rows": len(rows),
        "ranks": ranks,
        "collective": collective,
        "link_gbs": link_gbs,
        "plateau_busbw_gbs": round(plateau, 2),
        "efficiency_vs_link": None if eff is None else round(eff, 3),
        "smallest_size": rows[0].size,
        "smallest_time_us": small_us,
        "transport": run.transport,
        "ib_disabled_by_env": run.ib_disabled_by_env,
        "ratio_vs_baseline": None if ratio is None else round(ratio, 3),
    }
    return summary, flags


def find_slow_members(busbw_by_member: dict, min_ratio: float = 0.7):
    """Slow-rank signature from subset runs.

    One nccl-tests table is an average over ranks and cannot name a slow rank.
    Run the same size on each node, or each node pair, and pass the busbw per
    member here. Members below min_ratio of the median are returned. The default of 0.7 mirrors the
    NCCL 2.31 network diagnostic, which reports ranks more than 30 percent off the median.
    """
    if len(busbw_by_member) < 3:
        raise ValueError("need at least 3 members to take a meaningful median")
    med = statistics.median(busbw_by_member.values())
    return sorted(k for k, v in busbw_by_member.items() if v < min_ratio * med)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--ranks", type=int, required=True)
    ap.add_argument("--link-gbps", type=float, default=None,
                    help="per-rank bottleneck link rate in Gb/s, for example 400 for NDR; "
                         "omit to skip the link-rate check (single-node NVLink runs)")
    ap.add_argument("--collective", default="all_reduce", choices=sorted(BUSBW_FACTORS))
    ap.add_argument("--min-eff", type=float, default=0.8)
    ap.add_argument("--max-small-us", type=float, default=None)
    ap.add_argument("--column", choices=["oop", "inplace"], default="oop")
    ap.add_argument("--baseline")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        run = parse(open(a.file, encoding="utf-8", errors="replace").read())
        base = parse(open(a.baseline, encoding="utf-8", errors="replace").read()) if a.baseline else None
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    summary, flags = analyse(run, a.ranks, a.link_gbps, a.collective, a.min_eff,
                             a.max_small_us, column=a.column, baseline=base)
    if a.json:
        print(json.dumps({"summary": summary, "flags": flags}, indent=2))
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")
        print("flags:", ", ".join(flags) if flags else "none")
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
