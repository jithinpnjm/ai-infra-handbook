"""Validate c31_nvke_cluster.yaml against the NVKE REST API schema (CreateClusterRequest).

Set NVKE_OPENAPI to controller/api/openapi.yaml of a clone of dsx-ai-factory/nvke
(checked here at commit 487f511, 2026-11-10). The tests skip when it is not set.
The schema does not forbid unknown fields, so a strict unknown-field walk is added,
matching the nvkectl behaviour described in the NVKE docs.
"""
import os
from pathlib import Path

import pytest
import yaml

jsonschema = pytest.importorskip("jsonschema")

HERE = Path(__file__).parent
DEFAULT = "/private/tmp/claude-501/v20/nvstack/nvke/controller/api/openapi.yaml"
PATH = Path(os.environ.get("NVKE_OPENAPI", DEFAULT))
pytestmark = pytest.mark.skipif(not PATH.exists(), reason="NVKE openapi.yaml not available")


@pytest.fixture(scope="module")
def spec():
    return yaml.safe_load(PATH.read_text())


def resolve(spec, schema):
    while "$ref" in schema:
        schema = spec["components"]["schemas"][schema["$ref"].split("/")[-1]]
    return schema


def unknown_fields(spec, schema, value, path=""):
    schema = resolve(spec, schema)
    out = []
    if isinstance(value, dict) and "properties" in schema:
        for k, v in value.items():
            if k not in schema["properties"]:
                out.append(f"{path}/{k}")
            else:
                out += unknown_fields(spec, schema["properties"][k], v, f"{path}/{k}")
    elif isinstance(value, list) and "items" in schema:
        for i, v in enumerate(value):
            out += unknown_fields(spec, schema["items"], v, f"{path}/{i}")
    return out


def validator(spec):
    return jsonschema.Draft7Validator(
        {"$ref": "#/components/schemas/CreateClusterRequest", "components": spec["components"]}
    )


def load():
    return yaml.safe_load((HERE / "c31_nvke_cluster.yaml").read_text())


def test_cluster_spec_matches_schema_and_has_no_unknown_fields(spec):
    doc = load()
    assert list(validator(spec).iter_errors(doc)) == []
    assert unknown_fields(spec, {"$ref": "#/components/schemas/CreateClusterRequest"}, doc) == []


def test_unknown_field_is_caught(spec):
    doc = load()
    doc["nodePools"][0]["nico"]["bogus"] = 1
    found = unknown_fields(spec, {"$ref": "#/components/schemas/CreateClusterRequest"}, doc)
    assert found == ["/nodePools/0/nico/bogus"]


def test_missing_etcd_flag_is_rejected(spec):
    doc = load()
    del doc["etcdEncrypted"]
    assert list(validator(spec).iter_errors(doc))


def test_leading_v_in_version_is_rejected(spec):
    doc = load()
    doc["controlPlaneKubernetesVersion"] = "v1.36.3"
    assert list(validator(spec).iter_errors(doc))


def test_two_providers_are_rejected(spec):
    doc = load()
    doc["launchLayer"] = {}
    assert list(validator(spec).iter_errors(doc))
