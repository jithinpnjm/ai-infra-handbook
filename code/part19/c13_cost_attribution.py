#!/usr/bin/env python3
"""Cost attribution for a shared research GPU pool (chapter 19.13). Standard library only.

Method (my design, one reasonable choice, not a standard):
  1. Direct GPU cost  = allocated GPU-hours * price. Allocated, not busy: a held GPU costs the same.
  2. Idle capacity    = (GPUs * hours in month - allocated hours) * price. Nobody asked for it.
                        It is spread over teams either `pro_rata` (by direct cost) or by `quota`
                        (by the share of nominal quota each team owns).
  3. Storage          = TB * price per TB-month, charged to the team that owns the data.
  4. Platform fixed   = spread by each team's share of direct GPU cost.
Invariant: the sum of all team bills equals total cost of the pool plus storage plus platform.
Money uses Decimal and cents are rounded so that bills add up exactly (largest remainder).
"""
from __future__ import annotations

import csv
import json
import pathlib
from collections import defaultdict
from decimal import Decimal, ROUND_FLOOR

HERE = pathlib.Path(__file__).resolve().parent
CENT = Decimal("0.01")


class UsageError(ValueError):
    pass


def load_usage(path):
    rows = []
    with open(path, newline="") as fh:
        for i, r in enumerate(csv.DictReader(fh), start=2):
            try:
                row = {
                    "team": r["team"].strip(),
                    "project": r["project"].strip(),
                    "pool": r["pool"].strip(),
                    "alloc": Decimal(r["gpu_hours_allocated"]),
                    "busy": Decimal(r["gpu_hours_busy"]),
                    "tb": Decimal(r["storage_tb"]),
                }
            except (KeyError, ArithmeticError) as e:
                raise UsageError(f"line {i}: bad row ({e})") from e
            if not row["team"]:
                raise UsageError(f"line {i}: empty team")
            if min(row["alloc"], row["busy"], row["tb"]) < 0:
                raise UsageError(f"line {i}: negative value")
            if row["busy"] > row["alloc"]:
                raise UsageError(f"line {i}: busy hours exceed allocated hours")
            rows.append(row)
    return rows


def load_params(path):
    p = json.loads(pathlib.Path(path).read_text())
    for k in ("gpu_hour_price", "storage_price_per_tb_month", "platform_fixed_per_month"):
        p[k] = Decimal(p[k])
    p["quota_share"] = {t: Decimal(v) for t, v in p["quota_share"].items()}
    return p


def _split(total: Decimal, weights: dict[str, Decimal]) -> dict[str, Decimal]:
    """Split total across keys in proportion to weights, in whole cents, summing exactly to total."""
    wsum = sum(weights.values())
    if wsum <= 0:
        raise UsageError("cannot split cost: weights sum to zero")
    cents = (total / CENT).to_integral_value(ROUND_FLOOR)
    raw = {k: cents * w / wsum for k, w in weights.items()}
    base = {k: int(v.to_integral_value(ROUND_FLOOR)) for k, v in raw.items()}
    left = int(cents) - sum(base.values())
    order = sorted(weights, key=lambda k: (-(raw[k] - base[k]), k))
    for k in order[:left]:
        base[k] += 1
    return {k: Decimal(v) * CENT for k, v in base.items()}


def attribute(rows, params, idle_mode: str = "pro_rata"):
    if idle_mode not in ("pro_rata", "quota"):
        raise UsageError(f"unknown idle_mode {idle_mode!r}")
    capacity_hours = Decimal(params["gpus"]) * Decimal(params["hours_in_month"])
    alloc_total = sum(r["alloc"] for r in rows)
    if alloc_total > capacity_hours:
        raise UsageError(f"allocated {alloc_total} GPU-hours exceeds capacity {capacity_hours}")
    teams = sorted({r["team"] for r in rows})
    unknown = [t for t in teams if t not in params["quota_share"]]
    if unknown:
        raise UsageError(f"teams without a quota share: {unknown}")
    price = params["gpu_hour_price"]
    direct_h = defaultdict(Decimal)
    busy_h = defaultdict(Decimal)
    tb = defaultdict(Decimal)
    for r in rows:
        direct_h[r["team"]] += r["alloc"]
        busy_h[r["team"]] += r["busy"]
        tb[r["team"]] += r["tb"]
    direct = {t: direct_h[t] * price for t in teams}
    idle_cost = (capacity_hours - alloc_total) * price
    weights = direct if idle_mode == "pro_rata" else {t: params["quota_share"][t] for t in teams}
    idle = _split(idle_cost, weights)
    storage_total = sum(tb.values()) * params["storage_price_per_tb_month"]
    storage = {t: tb[t] * params["storage_price_per_tb_month"] for t in teams}
    platform = _split(params["platform_fixed_per_month"], direct)
    bills = {}
    for t in teams:
        d = direct[t].quantize(CENT)
        bills[t] = {
            "alloc_hours": direct_h[t],
            "busy_hours": busy_h[t],
            "idle_held_hours": direct_h[t] - busy_h[t],
            "direct_gpu": d,
            "idle_share": idle[t],
            "storage": storage[t].quantize(CENT),
            "platform": platform[t],
        }
        bills[t]["total"] = d + idle[t] + bills[t]["storage"] + platform[t]
    total_pool = (capacity_hours * price + storage_total + params["platform_fixed_per_month"]).quantize(CENT)
    return {"bills": bills, "pool_total": total_pool, "idle_cost": idle_cost.quantize(CENT)}


def by_project(rows, params):
    """Direct GPU cost per team and project, for the showback report researchers see."""
    out = defaultdict(Decimal)
    for r in rows:
        out[(r["team"], r["project"])] += r["alloc"] * params["gpu_hour_price"]
    return {k: v.quantize(CENT) for k, v in sorted(out.items())}


def main():
    rows = load_usage(HERE / "c13_usage_sample.csv")
    params = load_params(HERE / "c13_cost_params.json")
    for mode in ("pro_rata", "quota"):
        res = attribute(rows, params, mode)
        print(f"idle mode: {mode}   pool total {res['pool_total']}   idle capacity {res['idle_cost']}")
        print(f"{'team':<8}{'alloc h':>9}{'busy h':>9}{'direct':>11}{'idle':>11}{'storage':>10}{'platform':>10}{'total':>11}")
        for t, b in res["bills"].items():
            print(f"{t:<8}{b['alloc_hours']:>9}{b['busy_hours']:>9}{b['direct_gpu']:>11}{b['idle_share']:>11}{b['storage']:>10}{b['platform']:>10}{b['total']:>11}")
        print()


if __name__ == "__main__":
    main()
