#!/usr/bin/env python3
"""Read, compare and change BIOS settings through Redfish, the safe way.

  rf_bios.py show   http://host:port user pw [--system ID]
  rf_bios.py plan   http://host:port user pw --target profiles/ai_node_bios.json
  rf_bios.py apply  http://host:port user pw --target profiles/ai_node_bios.json [--reset] [--yes]

How Redfish BIOS settings work (DSP0266 9.10, the Settings resource):
  * 'Bios' shows the LIVE attributes. A change is PATCHed to its Settings object ('@Redfish.Settings'), which holds
    the PENDING values. They become live at the next reset (the apply time the service advertises).
  * The attribute REGISTRY lists every attribute, its type and allowed values, so a tool can check a value
    before sending it. Names differ per platform: never hard-code them.
apply is a dry run unless --yes. With --reset it restarts the host (drain the node first) and checks the live values.
"""
import json, sys, time
from redfish_crawl import Client
from rf_inventory import get, collection


def find_system(c, sid=None):
    root = get(c, "/redfish/v1/")
    systems = collection(c, root["Systems"]["@odata.id"])
    systems = [s for s in systems if "Bios" in s]
    if sid:
        systems = [s for s in systems if s["Id"] == sid]
    if not systems:
        raise SystemExit("no system with a Bios resource found")
    return systems[0]


def load_registry(c, bios):
    """Return {attribute name: entry} from the attribute registry the Bios resource names."""
    rid = bios.get("AttributeRegistry")
    root = get(c, "/redfish/v1/")
    if not rid or "Registries" not in root:
        return {}
    for f in collection(c, root["Registries"]["@odata.id"]):
        if f.get("Registry") == rid or f.get("Id") == rid:
            for loc in f.get("Location", []):
                reg = get(c, loc.get("Uri") or "")
                if reg:
                    return {e["AttributeName"]: e for e in reg.get("RegistryEntries", {}).get("Attributes", [])}
    return {}


def plan(current, target, registry):
    """Return a list of (attribute, current, wanted, action). action: ok, CHANGE, UNKNOWN, READONLY or INVALID."""
    rows = []
    for name, want in target.items():
        if name.startswith("_"):
            continue
        e = registry.get(name)
        if name not in current and e is None:
            rows.append((name, None, want, "UNKNOWN"))
            continue
        if e and e.get("ReadOnly"):
            rows.append((name, current.get(name), want, "READONLY"))
            continue
        if e and e.get("Type") == "Enumeration" and want not in [v["ValueName"] for v in e.get("Value", [])]:
            rows.append((name, current.get(name), want, "INVALID"))
            continue
        rows.append((name, current.get(name), want, "ok" if current.get(name) == want else "CHANGE"))
    return rows


def main(argv):
    cmd, base, user, pw = argv[1:5]
    flags = argv[5:]
    val = lambda n, d=None: flags[flags.index(n) + 1] if n in flags else d
    c = Client(base, user, pw)
    try:
        s = find_system(c, val("--system"))
        bios = get(c, s["Bios"]["@odata.id"])
        reg = load_registry(c, bios)
        if cmd == "show":
            for k, v in sorted(bios["Attributes"].items()):
                print(f"{k:24} {v}")
            print(f"\nregistry: {bios.get('AttributeRegistry')} ({len(reg)} attributes)")
            return 0
        target = json.load(open(val("--target")))
        rows = plan(bios["Attributes"], target, reg)
        for name, cur, want, act in rows:
            print(f"{name:24} now={cur!s:10} want={want!s:10} {act}")
        bad = [r for r in rows if r[3] in ("UNKNOWN", "READONLY", "INVALID")]
        changes = {r[0]: r[2] for r in rows if r[3] == "CHANGE"}
        if cmd == "plan":
            print(f"\n{len(changes)} to change, {len(bad)} problem(s)")
            return 1 if bad else 0
        if bad:
            print("refusing: the target has attributes this BIOS does not accept"); return 2
        if not changes:
            print("nothing to change"); return 0
        settings_uri = bios["@Redfish.Settings"]["SettingsObject"]["@odata.id"]
        if "--yes" not in flags:
            print(f"DRY RUN: would PATCH {settings_uri} with {json.dumps(changes)}"); return 0
        st, hd, resp = c.req("PATCH", settings_uri, {"Attributes": changes})
        if st != 200:
            print(f"refused: HTTP {st} {json.dumps(resp)[:300]}"); return 3
        pend = get(c, settings_uri)["Attributes"]
        missing = {k: v for k, v in changes.items() if pend.get(k) != v}
        print(f"staged {len(changes)} change(s); pending now: {json.dumps(pend)}")
        if missing:
            print("pending values do not match what was sent:", missing); return 4
        if "--reset" not in flags:
            print("STAGED: the new values become live after the next host reset (not done: --reset was not given)."); return 0
        act = s.get("Actions", {}).get("#ComputerSystem.Reset")
        print(f"resetting: POST {act['target']} GracefulRestart")
        st, _, _ = c.req("POST", act["target"], {"ResetType": "GracefulRestart"})
        if st not in (200, 202, 204):
            print(f"reset refused: HTTP {st}"); return 5
        live = get(c, bios["@odata.id"])["Attributes"]
        wrong = {k: (live.get(k), v) for k, v in changes.items() if live.get(k) != v}
        print("LIVE and verified" if not wrong else f"NOT LIVE yet: {wrong}")
        return 0 if not wrong else 6
    finally:
        c.logout()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
