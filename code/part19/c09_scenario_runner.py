"""Scenario runner (chapter 19.9). Reads c09_assumptions.json, applies each
scenario's overrides to the base assumptions, and prints one comparable row each."""
import copy
import json
import pathlib
import sys

from c09_capacity_model import run_plan, set_path

DEFAULT = pathlib.Path(__file__).with_name("c09_assumptions.json")


def load(path=DEFAULT):
    return json.loads(pathlib.Path(path).read_text())


def apply_overrides(base, overrides):
    b = copy.deepcopy(base)
    for path, value in overrides.items():
        set_path(b, path, value)
    return b


def summarise(plan):
    c = plan["cost"]
    best = min(("all on-demand", c["all_on_demand"]),
               ("reserved mix", c["reserved_commit"][1]),
               ("owned mix", c["owned_commit"][1]), key=lambda kv: kv[1])
    return {"peak_gpus": plan["peak_gpus"], "pool_gpus": plan["pool_gpus"],
            "training_gpus": plan["training"]["gpus"],
            "inference_gpus_end": plan["inference"]["gpus_end"],
            "best_strategy": best[0], "best_cost": best[1]}


def run_all(doc):
    return {name: summarise(run_plan(apply_overrides(doc["base"], ov)))
            for name, ov in doc["scenarios"].items()}


def format_table(rows):
    head = f"{'scenario':<22}{'peak':>6}{'pool':>6}{'train':>7}{'infer':>7}  {'best strategy':<14}{'cost USD/yr':>13}"
    lines = [head]
    for name, r in rows.items():
        lines.append(f"{name:<22}{r['peak_gpus']:>6.1f}{r['pool_gpus']:>6}{r['training_gpus']:>7}"
                     f"{r['inference_gpus_end']:>7}  {r['best_strategy']:<14}{r['best_cost']:>13,.0f}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_table(run_all(load(sys.argv[1] if len(sys.argv) > 1 else DEFAULT))))
