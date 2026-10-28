#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.30: Go for Kubernetes engineers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from client_go_mechanics_sim import (
    DefaultRESTMapperSim,
    FakeClientsetWithCacheSim,
    get_scaled_value_from_int_or_percent,
    parse_k8s_quantity_milli,
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
    # 1. KPG Ch. 4: resource.Quantity (binary Ki/Mi vs decimal m/k/M) and intstr.GetScaledValueFromIntOrPercent
    cpu_m = parse_k8s_quantity_milli("2500m")
    cpu_whole = parse_k8s_quantity_milli("2.5")
    mem_1ki_milli = parse_k8s_quantity_milli("1Ki")
    mem_1k_milli = parse_k8s_quantity_milli("1k")
    scaled_up = get_scaled_value_from_int_or_percent("25%", total=10, round_up=True)
    scaled_down = get_scaled_value_from_int_or_percent("25%", total=10, round_up=False)
    check(
        "KPG Ch. 4 Quantity parses 2500m == 2.5 (2500 milli), distinguishes 1Ki (1024) from 1k (1000), and scales 25% of 10 to ceil=3 vs floor=2",
        cpu_m == 2500
        and cpu_whole == 2500
        and mem_1ki_milli == 1_024_000
        and mem_1k_milli == 1_000_000
        and scaled_up == 3
        and scaled_down == 2,
    )

    # 2. KPG Ch. 5: DefaultRESTMapper GVK <-> GVR pluralization (Deployment -> deployments, Ingress -> ingresses, GPUHealthPolicy -> gpuhealthpolicies)
    mapper = DefaultRESTMapperSim()
    mapper.add("apps", "v1", "Deployment", "Namespaced")
    mapper.add("networking.k8s.io", "v1", "Ingress", "Namespaced")
    mapper.add("platform.example.com", "v1alpha1", "GPUHealthPolicy", "Cluster")
    check(
        "KPG Ch. 5 DefaultRESTMapper pluralizes Deployment->deployments, Ingress->ingresses, and GPUHealthPolicy->gpuhealthpolicies",
        mapper.gvk_to_gvr[("apps", "v1", "Deployment")][2] == "deployments"
        and mapper.gvk_to_gvr[("networking.k8s.io", "v1", "Ingress")][2] == "ingresses"
        and mapper.gvk_to_gvr[("platform.example.com", "v1alpha1", "GPUHealthPolicy")][2] == "gpuhealthpolicies",
    )

    # 3. KPG Ch. 6 & 7: Lister DeepCopy() cache safety + fake Clientset PrependReactor & Actions()
    cs = FakeClientsetWithCacheSim({"gpu-01": {"unschedulable": False, "labels": {"gpu": "h100"}}})
    # Mutating a DeepCopy leaves the shared cache untouched
    copied = cs.lister_get("gpu-01", deep_copy=True)
    copied["labels"]["gpu"] = "corrupted"
    cache_still_clean = cs.lister_get("gpu-01", deep_copy=True)["labels"]["gpu"] == "h100"

    cs.patch_node("gpu-01", {"unschedulable": True})
    # Prepend a reactor that injects a conflict error on the next patch
    cs.prepend_reactor("patch", "nodes", lambda name, p: (True, RuntimeError("409 Conflict injected by PrependReactor")))
    got_reactor_err = False
    try:
        cs.patch_node("gpu-01", {"unschedulable": False})
    except RuntimeError:
        got_reactor_err = True

    check(
        "DeepCopy() protects shared Lister cache from mutation, and fake Clientset records Actions() and executes PrependReactor error injection",
        cache_still_clean is True
        and len(cs.actions) == 2
        and got_reactor_err is True,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
