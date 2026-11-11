#!/usr/bin/env python3
"""Validate NVKE request bodies against the vendored NVKE OpenAPI document.

The OpenAPI file is a copy of controller/api/openapi.yaml from
github.com/dsx-ai-factory/nvke at commit 487f511 (2026-11-10, Apache-2.0).
Two checks run: a JSON Schema check, and a strict walk that rejects fields the
schema does not name (the nvkectl client does the same, see the nvkectl output
in chapter 11.32).
"""
import json
import sys
from pathlib import Path

import jsonschema
import yaml

SPEC_PATH = Path(__file__).with_name("c32_nvke_openapi_487f511.yaml")

_cache = {}


def load_spec(path=SPEC_PATH):
    key = str(path)
    if key not in _cache:
        _cache[key] = yaml.safe_load(Path(path).read_text())
    return _cache[key]


def _resolve(spec, schema):
    while "$ref" in schema:
        schema = spec["components"]["schemas"][schema["$ref"].split("/")[-1]]
    return schema


def _merged(spec, schema):
    """Resolve $ref and fold allOf members into one schema with merged properties."""
    schema = _resolve(spec, schema)
    if "allOf" not in schema:
        return schema
    merged = {"properties": dict(schema.get("properties", {}))}
    for sub in schema["allOf"]:
        sub = _merged(spec, sub)
        merged["properties"].update(sub.get("properties", {}))
        if "items" in sub:
            merged["items"] = sub["items"]
    return merged


def unknown_fields(spec, schema, value, path=""):
    """Return JSON-pointer paths of keys that the schema does not define."""
    schema = _merged(spec, schema)
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


def _validator(spec, name):
    return jsonschema.Draft7Validator(
        {"$ref": f"#/components/schemas/{name}", "components": spec["components"]}
    )


def validate(schema_name, doc, spec=None):
    """Return a list of error strings for doc against the named schema."""
    spec = spec or load_spec()
    errors = [
        f"{'/' + '/'.join(map(str, e.absolute_path))}: {e.message}"
        for e in _validator(spec, schema_name).iter_errors(doc)
    ]
    for p in unknown_fields(spec, {"$ref": f"#/components/schemas/{schema_name}"}, doc):
        errors.append(f"{p}: unknown field")
    return errors


KINDS = {
    "cluster": "CreateClusterRequest",
    "nodepool": "CreateNodePoolRequest",
    "patch-cluster": "UpdateClusterRequest",
    "patch-nodepool": "UpdateNodePoolRequest",
    "delete-node": "DeleteNodeRequest",
}


def main(argv):
    if len(argv) != 3 or argv[1] not in KINDS:
        print(f"usage: c32_validate.py {{{'|'.join(KINDS)}}} FILE", file=sys.stderr)
        return 2
    doc = yaml.safe_load(Path(argv[2]).read_text())
    errors = validate(KINDS[argv[1]], doc)
    for e in errors:
        print("ERROR", e)
    print("valid" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
