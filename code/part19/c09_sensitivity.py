"""One-at-a-time sensitivity table (chapter 19.9): move each parameter by plus and
minus the swing in c09_assumptions.json, record the pool size and best annual cost."""
import sys

from c09_capacity_model import get_path, set_path
from c09_scenario_runner import DEFAULT, apply_overrides, load, summarise
from c09_capacity_model import run_plan


def sensitivity(doc):
    base = doc["base"]
    swing = doc["sensitivity"]["swing"]
    b0 = summarise(run_plan(base))
    rows = []
    for path in doc["sensitivity"]["params"]:
        v = get_path(base, path)
        lo = summarise(run_plan(apply_overrides(base, {path: v * (1 - swing)})))
        hi = summarise(run_plan(apply_overrides(base, {path: v * (1 + swing)})))
        rows.append({"param": path, "pool_lo": lo["pool_gpus"], "pool_hi": hi["pool_gpus"],
                     "cost_lo": lo["best_cost"], "cost_hi": hi["best_cost"],
                     "cost_swing": abs(hi["best_cost"] - lo["best_cost"])})
    rows.sort(key=lambda r: r["cost_swing"], reverse=True)
    return b0, rows


def format_table(b0, rows, swing):
    out = [f"base: pool {b0['pool_gpus']} GPUs, best cost {b0['best_cost']:,.0f} USD/yr, "
           f"each parameter moved -{swing:.0%} and +{swing:.0%}",
           f"{'parameter':<30}{'pool -':>8}{'pool +':>8}{'cost -':>13}{'cost +':>13}{'swing':>12}"]
    for r in rows:
        out.append(f"{r['param']:<30}{r['pool_lo']:>8}{r['pool_hi']:>8}{r['cost_lo']:>13,.0f}"
                   f"{r['cost_hi']:>13,.0f}{r['cost_swing']:>12,.0f}")
    return "\n".join(out)


if __name__ == "__main__":
    d = load(sys.argv[1] if len(sys.argv) > 1 else DEFAULT)
    b, r = sensitivity(d)
    print(format_table(b, r, d["sensitivity"]["swing"]))
