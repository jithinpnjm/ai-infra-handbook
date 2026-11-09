#!/usr/bin/env python3
"""Validate YAML blocks in handbook chapters against real upstream CRD schemas.

Usage: python3 -I tools/check_crd_yaml.py <crd.yaml> [more crds ...] -- <doc.md ...>

Every ```yaml block with apiVersion+kind matching a loaded CRD is checked with
unknown fields rejected (unless the schema sets x-kubernetes-preserve-unknown-fields).
Placeholders like <...> or ... inside values are tolerated by relaxing types.
"""
import sys, re, yaml, jsonschema

def conv(s):
    if not isinstance(s, dict):
        return s
    o = {}
    t = s.get("type")
    for k, v in s.items():
        if k == "properties":
            o[k] = {a: conv(b) for a, b in v.items()}
        elif k == "items":
            o[k] = conv(v)
        elif k == "additionalProperties":
            o[k] = conv(v) if isinstance(v, dict) else v
        elif k in ("allOf", "anyOf", "oneOf"):
            o[k] = [conv(x) for x in v]
        elif k in ("required", "enum", "type", "minimum", "maximum", "pattern", "minLength"):
            o[k] = v
    if t == "object" and "properties" in s and not s.get("x-kubernetes-preserve-unknown-fields") \
            and "additionalProperties" not in s:
        o["additionalProperties"] = False
    if s.get("x-kubernetes-int-or-string"):
        o.pop("type", None)
        o["type"] = ["integer", "string"]
    o.pop("required", None) if False else None
    return o

def load_crds(paths):
    out = {}
    for p in paths:
        for d in yaml.safe_load_all(open(p)):
            if not d or d.get("kind") != "CustomResourceDefinition":
                continue
            kind = d["spec"]["names"]["kind"]
            for v in d["spec"]["versions"]:
                sch = v.get("schema", {}).get("openAPIV3Schema")
                if sch:
                    out[(d["spec"]["group"] + "/" + v["name"], kind)] = conv(sch)
    return out

def main():
    a = sys.argv[1:]
    i = a.index("--")
    crds = load_crds(a[:i])
    bad = 0
    n = 0
    for f in a[i + 1:]:
        txt = open(f).read()
        if f.endswith((".yaml", ".yml")):
            blocks = [(txt, 1)]
        else:
            blocks = [(m.group(1), txt[:m.start()].count("\n") + 2) for m in re.finditer(r"```ya?ml\n(.*?)```", txt, re.S)]
        for blk, line in blocks:
            try:
                docs = [d for d in yaml.safe_load_all(blk) if isinstance(d, dict)]
            except yaml.YAMLError as e:
                if re.search(r"^kind:", blk, re.M):
                    print(f"YAMLERR {f}:{line} {str(e)[:80]}")
                    bad += 1
                continue
            for d in docs:
                key = (d.get("apiVersion"), d.get("kind"))
                if key not in crds:
                    continue
                n += 1
                v = jsonschema.Draft7Validator(crds[key])
                for e in sorted(v.iter_errors(d), key=lambda e: list(e.path)):
                    msg = e.message[:110]
                    if "is not of type" in msg and re.search(r"[<.]", str(e.instance)):
                        continue
                    print(f"BAD {f.split('/')[-1][:10]}:{line} {key[1]} /{'/'.join(map(str, e.path))}: {msg}")
                    bad += 1
    print(f"checked {n} resources, {bad} problems")

main()
