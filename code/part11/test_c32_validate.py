"""Chapter 11.32: example request bodies match the vendored NVKE OpenAPI schemas."""
import copy
from pathlib import Path

import pytest
import yaml

import c32_validate as v

HERE = Path(__file__).parent


def load(name):
    return yaml.safe_load((HERE / name).read_text())


@pytest.mark.parametrize(
    "schema,file",
    [
        ("CreateClusterRequest", "c32_cluster_minimal.yaml"),
        ("CreateClusterRequest", "c32_cluster_ha_gpu.yaml"),
        ("CreateNodePoolRequest", "c32_nodepool_add.yaml"),
        ("UpdateClusterRequest", "c32_patch_cluster_upgrade.yaml"),
        ("UpdateNodePoolRequest", "c32_patch_nodepool_version.yaml"),
        ("DeleteNodeRequest", "c32_delete_node.yaml"),
    ],
)
def test_examples_are_valid(schema, file):
    assert v.validate(schema, load(file)) == []


def test_spec_is_the_pinned_alpha_version():
    assert v.load_spec()["info"]["version"] == "0.1.0-alpha"


def test_unknown_nested_field_is_reported():
    doc = load("c32_cluster_ha_gpu.yaml")
    doc["nodePools"][0]["nico"]["bogus"] = 1
    assert "/nodePools/0/nico/bogus: unknown field" in v.validate("CreateClusterRequest", doc)


def test_unknown_field_in_node_pool_request_via_allof():
    doc = load("c32_nodepool_add.yaml")
    doc["oops"] = True
    assert "/oops: unknown field" in v.validate("CreateNodePoolRequest", doc)


def test_leading_v_and_missing_etcd_flag_rejected():
    doc = load("c32_cluster_minimal.yaml")
    doc["controlPlaneKubernetesVersion"] = "v1.36.3"
    assert v.validate("CreateClusterRequest", doc)
    doc = load("c32_cluster_minimal.yaml")
    del doc["etcdEncrypted"]
    assert any("etcdEncrypted" in e for e in v.validate("CreateClusterRequest", doc))


def test_two_providers_and_no_provider_rejected():
    doc = load("c32_cluster_minimal.yaml")
    doc["launchLayer"] = {}
    assert v.validate("CreateClusterRequest", doc)
    doc = load("c32_cluster_minimal.yaml")
    del doc["nico"]
    assert v.validate("CreateClusterRequest", doc)


def test_bad_taint_effect_rejected():
    doc = load("c32_cluster_ha_gpu.yaml")
    doc["nodePools"][0]["nodeTaints"][0]["effect"] = "Bogus"
    assert v.validate("CreateClusterRequest", copy.deepcopy(doc))


def test_patch_with_null_is_rejected():
    assert v.validate("UpdateClusterRequest", {"enableOidc": None})


def test_node_labels_are_not_patchable_on_a_pool():
    assert "/nodeLabels: unknown field" in v.validate("UpdateNodePoolRequest", {"nodeLabels": {"a": "b"}})


def test_cli_returns_nonzero_on_invalid(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("name: x\n")
    assert v.main(["c32_validate.py", "cluster", str(bad)]) == 1
    assert v.main(["c32_validate.py", "cluster", str(HERE / "c32_cluster_minimal.yaml")]) == 0
