"""Chapter 11.32: the spec linter agrees with the rejections seen on a local NVKE controller."""
import copy
from pathlib import Path

import yaml

import c32_spec_lint as lint

HERE = Path(__file__).parent


def load(name="c32_cluster_ha_gpu.yaml"):
    return yaml.safe_load((HERE / name).read_text())


def rules(spec, sev="ERROR"):
    return {r for s, r, _ in lint.lint(spec) if s == sev}


def test_good_specs_have_no_errors():
    assert rules(load()) == set()
    assert rules(load("c32_cluster_minimal.yaml")) == set()


def test_single_node_without_vip_warns():
    assert "vip" in rules(load("c32_cluster_minimal.yaml"), "WARN")


def test_three_nodes_without_vip_is_an_error():
    spec = load()
    del spec["controlPlaneVIP"]
    assert "vip" in rules(spec)


def test_vip_inside_pod_cidr_is_an_error():
    spec = load()
    spec["controlPlaneVIP"] = "192.168.5.5"
    assert "vip" in rules(spec)


def test_small_pod_cidr_fails_capacity_check_with_the_same_numbers_as_the_api():
    spec = load("c32_cluster_minimal.yaml")
    spec["network"] = {"podCIDR": "192.168.0.0/23"}
    spec["nodePools"] = [{"name": "p", "nodeNamePrefix": "w", "desiredNodeCount": 2,
                          "nico": {"instanceTypeID": "x", "vpcPrefixIDs": ["y"], "release": "r"}}]
    msgs = [m for s, r, m in lint.lint(spec) if r == "cidr-capacity"]
    assert msgs and "2 /24 node blocks" in msgs[0] and "4 are required" in msgs[0]


def test_reserved_label_and_taint_domains_rejected():
    spec = load()
    spec["nodePools"][0]["nodeLabels"] = {"kubernetes.io/foo": "x"}
    spec["nodePools"][0]["nodeTaints"][0]["key"] = "node.k8s.io/x"
    assert {"labels", "taints"} <= rules(spec)


def test_no_execute_taint_warns():
    spec = load()
    spec["nodePools"][0]["nodeTaints"][0]["effect"] = "NoExecute"
    assert "taints" in rules(spec, "WARN")


def test_max_surge_above_one_and_even_counts():
    spec = load()
    spec["controlPlaneConfig"]["maxSurge"] = 2
    assert "surge" in rules(spec)
    spec = load()
    spec["controlPlaneConfig"]["desiredCount"] = 2
    assert "quorum" in rules(spec, "WARN")


def test_node_name_too_long():
    spec = load()
    spec["name"] = "a" * 55
    spec["nodePools"][0]["nodeNamePrefix"] = "gpu"
    assert "node-name" in rules(spec)


def test_duplicate_pool_and_missing_release():
    spec = load()
    spec["nodePools"].append(copy.deepcopy(spec["nodePools"][0]))
    del spec["nodePools"][1]["nico"]["release"]
    assert {"pool-name", "release"} <= rules(spec)


def test_missing_etcd_and_version_with_v():
    spec = load()
    del spec["etcdEncrypted"]
    spec["controlPlaneKubernetesVersion"] = "v1.36.3"
    assert {"etcd", "version"} <= rules(spec)


def test_cli_exit_codes(tmp_path):
    bad = tmp_path / "s.yaml"
    bad.write_text("name: A\n")
    assert lint.main(["x", str(bad)]) == 1
    assert lint.main(["x", str(HERE / "c32_cluster_ha_gpu.yaml")]) == 0
