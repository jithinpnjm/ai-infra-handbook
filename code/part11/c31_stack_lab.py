#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.31: the install order and the NVSentinel staged-adoption model."""
import sys
from pathlib import Path

import c31_sentinel_sim as ss
import c31_stack_order as so

HERE = Path(__file__).parent


def run_lab() -> int:
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
        print(("PASS " if cond else "FAIL ") + name)

    graph = so.load_components(HERE / "c31_recipe_dynamo_inference.yaml")
    order = so.install_order(graph)
    check("recipe has a valid install order ending in dynamo-platform", order[-1] == "dynamo-platform")
    check("recipe satisfies the prerequisite rules", so.rule_violations(graph) == [])
    check("grove installs before dynamo-platform", order.index("grove") < order.index("dynamo-platform"))
    s = ss.Sentinel(ss.Config(gpu_nodes=1, quarantine=True))
    s.handle(0, "n1", healthy=False)
    check("one GPU node trips the breaker at the first cordon", s.tripped)
    check("trip threshold for 40 nodes at 50 percent is 20", ss.Sentinel(ss.Config(gpu_nodes=40)).trip_threshold() == 20)
    m = ss.Sentinel(ss.Config(gpu_nodes=20))
    m.handle(0, "n1", healthy=False)
    check("default is monitor only", not m.cordoned)
    print(f"{passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run_lab() else 0)
