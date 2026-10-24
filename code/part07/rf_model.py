#!/usr/bin/env python3
"""Map how Systems, Chassis and Managers relate on one Redfish service, and check the links agree.

  rf_model.py http://host:port user password [--mermaid]

The three families are found from the service root (Systems, Chassis, Managers), never by typed address.
Each resource lists related ones under Links. A link A -> B should normally be matched by a link B -> A:
  ComputerSystem.Links.Chassis        <->  Chassis.Links.ComputerSystems
  ComputerSystem.Links.ManagedBy      <->  Manager.Links.ManagerForServers
  Chassis.Links.ManagedBy             <->  Manager.Links.ManagerForChassis
  Chassis.Links.Contains              <->  Chassis.Links.ContainedBy
It reports links that point nowhere and links that are only half there. Teaching tool: some real BMCs omit
the reverse link on purpose or by accident, so a report is a question to ask, not always a bug.
"""
import sys
from redfish_crawl import Client


def members(c, root, key):
    link = root.get(key, {}).get("@odata.id")
    if not link:
        return []
    st, _, coll = c.req("GET", link)
    if st != 200:
        return []
    out = []
    for m in coll.get("Members", []):
        st, _, r = c.req("GET", m["@odata.id"])
        if st == 200:
            out.append(r)
    nxt = coll.get("Members@odata.nextLink")
    return out


def ids(links):
    if isinstance(links, dict):
        links = [links]
    return [x["@odata.id"].rstrip("/") for x in (links or []) if isinstance(x, dict) and "@odata.id" in x]


def build(c):
    st, _, root = c.req("GET", "/redfish/v1/")
    res = {"System": {}, "Chassis": {}, "Manager": {}}
    for kind, key in (("System", "Systems"), ("Chassis", "Chassis"), ("Manager", "Managers")):
        for r in members(c, root, key):
            res[kind][r["@odata.id"].rstrip("/")] = r
    return res


def edges(res):
    """Yield (from_kind, from_uri, relation, to_uri)."""
    for u, r in res["System"].items():
        L = r.get("Links", {})
        for t in ids(L.get("Chassis")): yield "System", u, "Chassis", t
        for t in ids(L.get("ManagedBy")): yield "System", u, "ManagedBy", t
    for u, r in res["Chassis"].items():
        L = r.get("Links", {})
        for t in ids(L.get("ComputerSystems")): yield "Chassis", u, "ComputerSystems", t
        for t in ids(L.get("ManagedBy")): yield "Chassis", u, "ManagedBy", t
        for t in ids(L.get("Contains")): yield "Chassis", u, "Contains", t
        for t in ids(L.get("ContainedBy")): yield "Chassis", u, "ContainedBy", t
    for u, r in res["Manager"].items():
        L = r.get("Links", {})
        for t in ids(L.get("ManagerForServers")): yield "Manager", u, "ManagerForServers", t
        for t in ids(L.get("ManagerForChassis")): yield "Manager", u, "ManagerForChassis", t
        for t in ids(L.get("ManagerInChassis")): yield "Manager", u, "ManagerInChassis", t


# relation -> (kind of the target, reverse relation on the target)
REVERSE = {("System", "Chassis"): ("Chassis", "ComputerSystems"), ("Chassis", "ComputerSystems"): ("System", "Chassis"),
           ("System", "ManagedBy"): ("Manager", "ManagerForServers"), ("Manager", "ManagerForServers"): ("System", "ManagedBy"),
           ("Chassis", "ManagedBy"): ("Manager", "ManagerForChassis"), ("Manager", "ManagerForChassis"): ("Chassis", "ManagedBy"),
           ("Chassis", "Contains"): ("Chassis", "ContainedBy"), ("Chassis", "ContainedBy"): ("Chassis", "Contains")}


def check(res):
    E = set((k, u, rel, t) for k, u, rel, t in edges(res))
    problems = []
    for k, u, rel, t in sorted(E):
        rev = REVERSE.get((k, rel))
        tk = rev[0] if rev else None
        if tk and t not in res[tk]:
            problems.append(f"DANGLING  {u} --{rel}--> {t} (no such {tk.lower()} in the collection)")
        elif rev and (tk, t, rev[1], u) not in E:
            problems.append(f"ONE-WAY   {u} --{rel}--> {t} (but {t} has no {rev[1]} link back)")
    return problems


def mermaid(res):
    def nid(u): return "n" + str(abs(hash(u)) % 10**8)
    lines = ["flowchart LR"]
    for kind, shape in (("System", '(["{}"])'), ("Chassis", '["{}"]'), ("Manager", '{{{{"{}"}}}}')):
        for u in res[kind]:
            lines.append(f"    {nid(u)}{shape.format(kind + ': ' + u.rsplit('/', 1)[-1])}")
    seen = set()
    for k, u, rel, t in edges(res):
        if rel in ("ComputerSystems", "ManagerForServers", "ManagerForChassis", "ContainedBy"):
            continue                      # draw each relationship once, from the 'owning' side
        key = (u, rel, t)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"    {nid(u)} -->|{rel}| {nid(t)}")
    return "\n".join(lines)


if __name__ == "__main__":
    base, user, pw = sys.argv[1:4]
    c = Client(base, user, pw)
    res = build(c)
    print(f"Systems: {len(res['System'])}  Chassis: {len(res['Chassis'])}  Managers: {len(res['Manager'])}")
    for kind in ("System", "Chassis", "Manager"):
        for u, r in res[kind].items():
            extra = {"System": f"SystemType={r.get('SystemType')} PowerState={r.get('PowerState')}",
                     "Chassis": f"ChassisType={r.get('ChassisType')}",
                     "Manager": f"ManagerType={r.get('ManagerType')} FW={r.get('FirmwareVersion')}"}[kind]
            print(f"  {kind:8} {u}   {extra}")
    print()
    for k, u, rel, t in edges(res):
        print(f"  {u} --{rel}--> {t}")
    probs = check(res)
    print(f"\nlink check: {len(probs)} finding(s)")
    for p in probs:
        print("  " + p)
    if "--mermaid" in sys.argv:
        print("\n" + mermaid(res))
    c.logout()
