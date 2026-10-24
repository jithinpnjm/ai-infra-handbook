#!/usr/bin/env python3
"""Inventory storage, network ports and PCIe devices through Redfish and flag degraded links.

  rf_hardware.py http://host:port user password [--all]

Walks the Systems and Chassis trees by following links (skipping logs, sensors, certificates), then looks at
every resource by @odata.type. It flags things that quietly cost performance:
  PCIe     LanesInUse < MaxLanes, or PCIeType older than MaxPCIeType   (link trained down, e.g. x16 Gen5 -> x4 Gen3)
  Ports    enabled port that is not LinkUp, or CurrentSpeedGbps below MaxSpeedGbps, or ActiveWidth below Width
  Drives   FailurePredicted, low PredictedMediaLifeLeftPercent, NegotiatedSpeedGbs below CapableSpeedGbs,
           Health not OK
  Volumes  Health not OK
A flag is a question for a human, not a verdict. Some devices legitimately run slower (power saving, mixed cables).
"""
import sys
from redfish_crawl import Client, links
from rf_inventory import get

SKIP = ("/LogServices", "/Sensors", "/Certificates", "/Assembly", "/Metrics", "/Registries", "/Thermal", "/Power",
        "/Controls", "/EnvironmentMetrics", "/TrustedComponents", "/ThermalSubsystem", "/PowerSubsystem")
GEN = {"Gen1": 1, "Gen2": 2, "Gen3": 3, "Gen4": 4, "Gen5": 5, "Gen6": 6}


def walk(c):
    root = get(c, "/redfish/v1/")
    todo = [root[k]["@odata.id"] for k in ("Systems", "Chassis") if k in root]
    seen, found = set(), []
    while todo:
        u = todo.pop().split("#")[0]          # '#/Array/0' points inside a resource we already have
        key = u.rstrip("/")
        if key in seen or any(s in key for s in SKIP):
            continue
        seen.add(key)
        r = get(c, u)
        if not r:
            continue
        r["_uri"] = key                       # where we really fetched it (a resource's own @odata.id can disagree)
        found.append(r)
        for l in links({k: v for k, v in r.items() if k not in ("@odata.id", "Actions", "Links")}):
            if l.startswith("/redfish/") and l.rstrip("/") not in seen:
                todo.append(l)
    return found


def typ(r):
    return (r.get("@odata.type") or "").lstrip("#").split(".")[0]


def hl(r):
    return (r.get("Status") or {}).get("Health")


def pcie_flags(pi):
    out = []
    if not isinstance(pi, dict):
        return out
    li, ml = pi.get("LanesInUse"), pi.get("MaxLanes")
    if isinstance(li, int) and isinstance(ml, int) and li < ml:
        out.append(f"link width x{li} of x{ml}")
    t, mt = GEN.get(pi.get("PCIeType")), GEN.get(pi.get("MaxPCIeType"))
    if t and mt and t < mt:
        out.append(f"PCIe Gen{t} of Gen{mt}")
    return out


def analyse(resources):
    rows = {"pcie": [], "port": [], "drive": [], "volume": [], "storage": []}
    for r in resources:
        t, name = typ(r), r["_uri"]
        if t in ("PCIeDevice", "NetworkAdapter", "StorageController", "Processor") or "PCIeInterface" in r:
            pi = r.get("PCIeInterface")
            if pi:
                rows["pcie"].append((name, r.get("Model") or r.get("Name"), pi, pcie_flags(pi) + ([f"health={hl(r)}"] if hl(r) not in (None, "OK") else [])))
        if t == "NetworkAdapter":
            for ctl in r.get("Controllers", []) or []:
                pi = (ctl.get("PCIeInterface") if isinstance(ctl, dict) else None)
                if pi:
                    rows["pcie"].append((name + "#controller", r.get("Model") or r.get("Name"), pi, pcie_flags(pi)))
        if t == "Port":
            f = []
            if r.get("LinkState") == "Enabled" and r.get("LinkStatus") not in (None, "LinkUp"):
                f.append(f"LinkStatus={r.get('LinkStatus')}")
            cs, ms = r.get("CurrentSpeedGbps"), r.get("MaxSpeedGbps")
            if isinstance(cs, (int, float)) and isinstance(ms, (int, float)) and r.get("LinkStatus") == "LinkUp" and cs < ms:
                f.append(f"speed {cs:g} of {ms:g} Gbps")
            aw, w = r.get("ActiveWidth"), r.get("Width")
            if isinstance(aw, int) and isinstance(w, int) and r.get("LinkStatus") == "LinkUp" and aw < w:
                f.append(f"width x{aw} of x{w}")
            if hl(r) not in (None, "OK"):
                f.append(f"health={hl(r)}")
            rows["port"].append((name, r.get("PortProtocol") or r.get("LinkNetworkTechnology") or "", r, f))
        if t == "Drive":
            f = []
            if r.get("FailurePredicted"):
                f.append("failure predicted")
            life = r.get("PredictedMediaLifeLeftPercent")
            if isinstance(life, (int, float)) and life < 10:
                f.append(f"media life left {life}%")
            ns, cs = r.get("NegotiatedSpeedGbs"), r.get("CapableSpeedGbs")
            if isinstance(ns, (int, float)) and isinstance(cs, (int, float)) and ns < cs:
                f.append(f"drive link {ns:g} of {cs:g} Gbps")
            if hl(r) not in (None, "OK"):
                f.append(f"health={hl(r)}")
            rows["drive"].append((name, r.get("Model") or r.get("Name"), r, f))
        if t == "Volume":
            rows["volume"].append((name, r.get("RAIDType") or "", r, [f"health={hl(r)}"] if hl(r) not in (None, "OK") else []))
        if t in ("Storage",):
            rows["storage"].append((name, r.get("Name"), r, []))
    return rows


def main(argv):
    base, user, pw = argv[1:4]
    c = Client(base, user, pw)
    res = walk(c)
    rows = analyse(res)
    show_all = "--all" in argv
    n_flag = 0
    print(f"walked {len(res)} resources")
    mismatch = [r for r in res if r.get("@odata.id", "").rstrip("/") != r["_uri"]]
    if mismatch:
        print(f"WARNING {len(mismatch)} resource(s) report an @odata.id different from the address they were fetched from, e.g.:")
        for r in mismatch[:3]:
            print(f"   fetched {r['_uri']}  but it says @odata.id = {r.get('@odata.id')}")
    print(f"PCIe interfaces: {len(rows['pcie'])}   ports: {len(rows['port'])}   drives: {len(rows['drive'])}   volumes: {len(rows['volume'])}   storage subsystems: {len(rows['storage'])}")
    for group, label in (("pcie", "PCIe"), ("port", "Port"), ("drive", "Drive"), ("volume", "Volume")):
        for name, what, r, f in rows[group]:
            if f or show_all:
                n_flag += bool(f)
                extra = ""
                if group == "pcie":
                    extra = f"{r.get('PCIeType')} x{r.get('LanesInUse')} (max {r.get('MaxPCIeType')} x{r.get('MaxLanes')})"
                elif group == "port":
                    extra = f"{r.get('LinkStatus')} {r.get('CurrentSpeedGbps')} Gbps"
                elif group == "drive":
                    gb = (r.get("CapacityBytes") or 0) / 1e9
                    extra = f"{r.get('Protocol')} {r.get('MediaType')} {gb:.0f} GB life {r.get('PredictedMediaLifeLeftPercent')}%"
                print(f"  {label:6} {name.split('/redfish/v1/')[-1][:58]:58} {extra}  {'; '.join(f)}")
    print(f"\n{n_flag} flagged")
    c.logout()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
