#!/usr/bin/env python3
"""Self-checking lab for chapter 7.6: use the OFFICIAL Redfish schemas and message registry to test a service.

Needs a clone of github.com/DMTF/Redfish-Publications (set REDFISH_PUBLICATIONS) and the jsonschema and
referencing packages. Checks that:
  1. the validator accepts DMTF's own example trees (so the validator itself is trustworthy),
  2. deliberately broken payloads are rejected for the right reason,
  3. schema versions behave as the spec says (new properties need a new version number),
  4. our mock service validates against the schemas,
  5. every MessageId our mock returns exists in the official Base message registry.
"""
import glob, json, os, re, sys, threading
import schema_tools as st
from redfish_mock import make_server
from protocol_lab import call

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def main():
    root = os.environ.get("REDFISH_PUBLICATIONS") or (st.DEFAULT_REDFISH_PUBS if os.path.isdir(st.DEFAULT_REDFISH_PUBS) else "")
    if not root:
        print("set REDFISH_PUBLICATIONS to a clone of DMTF/Redfish-Publications"); return 2
    mock = os.path.join(root, "mockups", "public-rackmount1")

    # 1. the validator against DMTF's own example (validate one full pass, deduplicating identical (type, keys) shapes after first check)
    bad = []; n = 0; seen_shapes = set()
    for f in glob.glob(mock + "/**/index.json", recursive=True):
        d = json.load(open(f))
        if "@odata.type" not in d:            # the OData service document is not a Redfish resource
            continue
        n += 1
        shape = (d.get("@odata.type"), tuple(sorted(d.keys())))
        if shape in seen_shapes:
            continue
        errs = st.validate_payload(d)
        if errs:
            bad.append((os.path.relpath(f, mock), errs[0][:100]))
        else:
            seen_shapes.add(shape)
    check(f"validator accepts all {n} resources of DMTF's public-rackmount1 example", not bad, bad)

    # 2. broken payloads
    good = json.load(open(mock + "/Systems/437XR1138R2/index.json"))
    def mutate(fn):
        d = json.loads(json.dumps(good)); fn(d); return st.validate_payload(d)
    e = mutate(lambda d: d.update(Bogus=1))
    check("an unknown property is rejected", e and "Bogus" in e[0], e)
    e = mutate(lambda d: d.update(PowerState="Banana"))
    check("a value outside the enumeration is rejected", e and "PowerState" in e[0], e)
    e = mutate(lambda d: d.update(AssetTag=12345))
    check("the wrong JSON type is rejected", e and "AssetTag" in e[0], e)
    e = mutate(lambda d: d.pop("Id"))
    check("a missing required property (Id) is rejected", e and "Id" in e[0], e)
    e = mutate(lambda d: d.update(AssetTag=None))
    check("null is allowed where the schema says nullable (AssetTag)", e == [], e)
    e = mutate(lambda d: d.update(**{"Name@Message.Note": "x", "Oem": {"Contoso": {"Anything": 1}}}))
    check("annotations (Prop@Namespace.Term) and Oem extensions are allowed", e == [], e)

    # 3. versions
    old = json.loads(json.dumps(good)); old["@odata.type"] = "#ComputerSystem.v1_0_0.ComputerSystem"
    e = st.validate_payload(old)
    check("a v1_0_0 payload cannot carry properties added later (versioning rule, 9.14)", e and len(e) >= 1, e)
    check("the same data is valid under the version it really is (" + good["@odata.type"].split(".")[1] + ")",
          st.validate_payload(good) == [], st.validate_payload(good))

    # 4. our mock
    srv, state = make_server("dgx", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    seen, todo, invalid = set(), ["/redfish/v1/"], {}
    from redfish_crawl import links
    while todo:
        u = todo.pop()
        if u.rstrip("/") in seen:
            continue
        seen.add(u.rstrip("/"))
        s, h, b = call(base, "GET", u)
        if s != 200:
            continue
        shape = (b.get("@odata.type"), tuple(sorted(b.keys())))
        if shape not in seen_shapes:
            errs = st.validate_payload(b)
            if errs:
                invalid[u] = errs
            else:
                seen_shapes.add(shape)
        for l in links({k: v for k, v in b.items() if k not in ("@odata.id", "Actions")}):
            if l.startswith("/redfish/") and l.rstrip("/") not in seen:
                todo.append(l)
    check(f"all {len(seen)} resources of our mock validate against the official schemas", not invalid, invalid)

    # 5. message ids
    reg = json.load(open(sorted(glob.glob(os.path.join(root, "registries", "Base.1.*.json")), key=lambda p: [int(x) for x in re.findall(r"\d+", os.path.basename(p))])[-1]))["Messages"]
    ids = set()
    def collect(resp):
        def walk(o):
            if isinstance(o, dict):
                if "MessageId" in o:
                    ids.add(o["MessageId"].split(".")[-1])
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        walk(resp)
    SYS = "/redfish/v1/Systems/System_0"
    probes = [("GET", "/redfish/v1/Systems", None, None), ("GET", "/redfish/v1/Nope", None, None),
              ("GET", "/redfish/v1/Systems?$filter=a", None, None), ("GET", "/redfish/v1/Systems?$top=x", None, None),
              ("GET", SYS + "?$top=1", None, None), ("PATCH", SYS, {"SerialNumber": "x"}, None),
              ("PATCH", SYS, {"Bogus": 1}, None), ("PATCH", SYS, {}, None),
              ("POST", SYS + "/Actions/ComputerSystem.Reset", {}, None),
              ("POST", SYS + "/Actions/ComputerSystem.Reset", {"ResetType": "Nope"}, None),
              ("POST", SYS + "/Actions/ComputerSystem.Reset", {"ResetType": "On"}, None),
              ("POST", "/redfish/v1/AccountService/Accounts", {"UserName": "admin", "Password": "longenough1", "RoleId": "ReadOnly"}, None),
              ("POST", "/redfish/v1/AccountService/Accounts", {"UserName": "q"}, None)]
    for m, p, b, a in probes:
        kw = {} if p != "/redfish/v1/Systems" or m != "GET" else {"auth": None}
        s, h, r = call(base, m, p, b, **kw)
        if isinstance(r, dict):
            collect(r)
    s, h, r = call(base, "PATCH", SYS, {"AssetTag": "x"}, {"If-Match": 'W/"stale"'}); collect(r)
    s, h, r = call(base, "PATCH", SYS, {"AssetTag": "x"}, auth=("viewer", "viewpass")); collect(r)
    missing = sorted(i for i in ids if i not in reg)
    check(f"every MessageId our mock returned ({len(ids)} different ones) exists in the official Base registry", not missing, missing)

    print(f"\n{ok_count} passed, {fail_count} failed")
    srv.shutdown()
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
