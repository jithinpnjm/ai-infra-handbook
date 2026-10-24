#!/usr/bin/env python3
"""Read and use the official Redfish JSON Schemas (from a clone of github.com/DMTF/Redfish-Publications).

  schema_tools.py explain ComputerSystem.v1_17_0           -> property table like the Resource Guide
  schema_tools.py explain ComputerSystem.v1_17_0 --prop Boot
  schema_tools.py check file.json [more.json]              -> validate payload files against their @odata.type
  schema_tools.py crawl http://host:port user password     -> log in, walk the service, validate every resource

Needs: pip install jsonschema referencing. Point REDFISH_PUBLICATIONS at the clone (the json-schema folder is used).
This is a learning tool. A pass means 'valid against the published schema', not 'correct hardware data'.
"""
import json, os, re, sys

BASE = "http://redfish.dmtf.org/schemas/v1/"


def schema_dir():
    root = os.environ.get("REDFISH_PUBLICATIONS", "")
    d = os.path.join(root, "json-schema")
    if not os.path.isdir(d):
        raise SystemExit("set REDFISH_PUBLICATIONS to a clone of github.com/DMTF/Redfish-Publications")
    return d


_cache = {}


def load(name):
    if name not in _cache:
        with open(os.path.join(schema_dir(), name)) as f:
            _cache[name] = json.load(f)
    return _cache[name]


_validators = {}
_registry = None


def make_validator(schema, key=None):
    """Validators are cached: building one parses the schema and the files it references."""
    global _registry
    import referencing, jsonschema
    from referencing.jsonschema import DRAFT4
    if key in _validators:
        return _validators[key]

    def retrieve(uri):
        name = uri.split("#")[0]
        if name.startswith(BASE):
            name = name[len(BASE):]
        try:
            return referencing.Resource.from_contents(load(name), default_specification=DRAFT4)
        except FileNotFoundError:
            raise referencing.exceptions.NoSuchResource(uri)

    if _registry is None:
        _registry = referencing.Registry(retrieve=retrieve)
    v = jsonschema.Draft4Validator(schema, registry=_registry)
    if key:
        _validators[key] = v
    return v


def split_type(odata_type):
    """'#ComputerSystem.v1_17_0.ComputerSystem' -> ('ComputerSystem', 'v1_17_0', 'ComputerSystem')"""
    m = re.match(r"^#([A-Za-z0-9_]+)\.(v\d+_\d+_\d+)\.([A-Za-z0-9_]+)$", odata_type or "")
    if m:
        return m.groups()
    m = re.match(r"^#([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)$", odata_type or "")
    return (m.group(1), None, m.group(2)) if m else (None, None, None)


def validate_payload(payload):
    """Return a list of error strings (empty list = valid) or None if the schema file is not available."""
    ns, ver, typ = split_type(payload.get("@odata.type"))
    if not ns:
        return ["no usable @odata.type"]
    fname = f"{ns}.{ver}.json" if ver else f"{ns}.json"
    try:
        schema = load(fname)
    except FileNotFoundError:
        return None
    # validate against the versioned definition of the type (schema files hold one file per version)
    v = make_validator({"$ref": f"{BASE}{fname}#/definitions/{typ}"}, key=(fname, typ))
    errs = []
    for e in sorted(v.iter_errors(payload), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in e.absolute_path) or "(top)"
        errs.append(f"{where}: {e.message[:140]}")
    return errs


def explain(type_ver, prop=None):
    ns, _, ver = type_ver.partition(".")
    schema = load(f"{ns}.{ver}.json" if ver else f"{ns}.json")
    d = schema["definitions"]
    node = d[ns]
    # collect allOf chain (the version file extends the previous version)
    props, req, seen = {}, set(), set()

    def walk(n):
        if "$ref" in n:
            ref = n["$ref"]
            if ref.startswith("#/definitions/"):
                nm = ref.split("/")[-1]
                if nm in seen:
                    return
                seen.add(nm)
                walk(d[nm])
            return
        for sub in n.get("allOf", []):
            walk(sub)
        props.update(n.get("properties", {}))
        req.update(n.get("required", []))

    walk(node)
    if prop:
        p = props.get(prop)
        if not p:
            print(f"{prop} is not a property of {type_ver}")
            return
        print(json.dumps(p, indent=2)[:3000])
        return
    print(f"{ns} {ver or ''}: {node.get('description','')}")
    try:
        top = load(f"{ns}.json")["definitions"][ns]          # the unversioned file holds URIs and capabilities
    except (FileNotFoundError, KeyError):
        top = node
    uris = top.get("uris", [])
    print(f"URIs: {', '.join(uris[:3])}{' ...' if len(uris) > 3 else ''}")
    print(f"capabilities: insertable={top.get('insertable')} updatable={top.get('updatable')} deletable={top.get('deletable')}\n")
    print(f"{'property':34} {'type':14} {'access':10} notes")
    for name in sorted(props):
        p = props[name]
        if name.startswith("@odata") and name not in ("@odata.id", "@odata.type"):
            continue
        t = p.get("type")
        if t is None:
            ref = p.get("$ref") or next((x.get("$ref") for x in p.get("anyOf", []) if x.get("$ref")), None)
            t = ref.split("/")[-1] if ref else "?"
        t = ",".join(t) if isinstance(t, list) else t
        acc = "read-only" if p.get("readonly") else "read-write"
        notes = []
        if name in req:
            notes.append("required")
        if p.get("enum"):
            notes.append("enum")
        if "versionAdded" in p:
            notes.append("added " + p["versionAdded"])
        if "versionDeprecated" in p:
            notes.append("deprecated " + p["versionDeprecated"])
        print(f"{name:34} {t[:14]:14} {acc:10} {' '.join(notes)}")


def main(argv):
    if len(argv) < 2:
        print(__doc__); return 2
    cmd = argv[1]
    if cmd == "explain":
        explain(argv[2], argv[argv.index("--prop") + 1] if "--prop" in argv else None)
        return 0
    if cmd == "check":
        bad = 0
        for fn in argv[2:]:
            errs = validate_payload(json.load(open(fn)))
            print(f"{fn}: " + ("no schema file for this type" if errs is None else "valid" if not errs else f"{len(errs)} problem(s)"))
            for e in (errs or [])[:10]:
                print("   ", e)
            bad += bool(errs)
        return 1 if bad else 0
    if cmd == "crawl":
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from redfish_crawl import Client, links
        c = Client(argv[2], argv[3], argv[4])
        seen, todo = set(), ["/redfish/v1/"]
        stats = {"valid": 0, "invalid": 0, "no schema": 0}
        problems = {}
        while todo:
            uri = todo.pop()
            if uri.rstrip("/") in seen:
                continue
            seen.add(uri.rstrip("/"))
            st, _, res = c.req("GET", uri)
            if st != 200 or not isinstance(res, dict):
                continue
            errs = validate_payload(res)
            if errs is None:
                stats["no schema"] += 1
            elif errs:
                stats["invalid"] += 1; problems[uri] = errs
            else:
                stats["valid"] += 1
            for l in links({k: v for k, v in res.items() if k not in ("@odata.id", "Actions")}):
                if l.startswith("/redfish/") and l.rstrip("/") not in seen:
                    todo.append(l)
        print(f"resources: {sum(stats.values())}  valid: {stats['valid']}  invalid: {stats['invalid']}  no schema file: {stats['no schema']}")
        for uri, errs in list(problems.items())[:15]:
            print(f"  {uri}")
            for e in errs[:4]:
                print("     ", e)
        c.logout()
        return 1 if stats["invalid"] else 0
    print(__doc__); return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
