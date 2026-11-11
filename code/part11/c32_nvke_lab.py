#!/usr/bin/env python3
"""Self-checking lab for chapters 11.32 to 11.34: every NVKE example validates and the planner arithmetic holds."""
import json
import sys
from pathlib import Path

import yaml

import c32_spec_lint as lint
import c32_upgrade_planner as up
import c32_validate as val

HERE = Path(__file__).parent


def load(name):
    return yaml.safe_load((HERE / name).read_text())


def run_lab() -> int:
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
        print(("PASS " if cond else "FAIL ") + name)

    for schema, f in [
        ("CreateClusterRequest", "c32_cluster_minimal.yaml"),
        ("CreateClusterRequest", "c32_cluster_ha_gpu.yaml"),
        ("CreateNodePoolRequest", "c32_nodepool_add.yaml"),
        ("UpdateClusterRequest", "c32_patch_cluster_upgrade.yaml"),
        ("UpdateNodePoolRequest", "c32_patch_nodepool_version.yaml"),
        ("DeleteNodeRequest", "c32_delete_node.yaml"),
    ]:
        check(f"{f} matches {schema}", val.validate(schema, load(f)) == [])
    ha = load("c32_cluster_ha_gpu.yaml")
    check("HA spec has no lint errors", not [x for x in lint.lint(ha) if x[0] == "ERROR"])
    bad = dict(ha, controlPlaneVIP="192.168.5.5")
    check("VIP inside the pod CIDR is an error", any(r == "vip" for s, r, _ in lint.lint(bad) if s == "ERROR"))
    check("spec carries the three required cluster fields", {"name", "controlPlaneKubernetesVersion", "etcdEncrypted"} <= set(ha))
    kinds = [d["kind"] for d in yaml.safe_load_all((HERE / "c32_release_set.yaml").read_text())]
    check("release set holds the three release kinds", kinds == ["MachineImage", "ClusterRelease", "NodePoolRelease"])
    site = load("c32_sitespec_provisioned.yaml")
    check("site spec has an odd node count", len(site["cluster"]["nodes"]) % 2 == 1)
    stack = json.loads((HERE / "c32_stack_config.json").read_text())
    check("stack config keeps the documented keys", set(stack) == {"nico", "images", "mirror"})
    check("planner allows one minor", up.plan("1.36.3", "1.37.2", {"gpu": "1.36.3"})[0] == ("patch-cluster", "1.37.2"))
    try:
        up.check_cp_step("1.35.3", "1.37.2")
        check("planner refuses two minors", False)
    except up.SkewError:
        check("planner refuses two minors", True)
    check("recycle example: budget 2, one node down, pool 4", up.recycle_marks(4, 3, 2) == 1)
    check("three control plane nodes tolerate one failure", up.ControlPlane(3).survivable_failures() == 1)
    print(f"{passed} passed, {failed} failed")
    return failed


if __name__ == "__main__":
    sys.exit(1 if run_lab() else 0)
