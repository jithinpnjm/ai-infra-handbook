#!/usr/bin/env python3
"""One inventory line per computer system on a Redfish service. Discovers everything from the root.

  rf_inventory.py http://host:port user password [--csv]

Reads what exists and skips what does not (the spec says many parts are optional): model, serial number,
UUID, power state, health, BIOS version, processor and GPU counts, memory, the managing BMC and its firmware.
Uses $select where it helps nothing is assumed beyond the standard schema names.
"""
import csv, sys
from redfish_crawl import Client


def get(c, uri):
    st, _, b = c.req("GET", uri)
    return b if st == 200 and isinstance(b, dict) else None


def collection(c, uri):
    out, seen = [], set()
    while uri and uri not in seen:
        seen.add(uri)
        coll = get(c, uri)
        if not coll:
            break
        for m in coll.get("Members", []):
            r = get(c, m["@odata.id"])
            if r:
                out.append(r)
        uri = coll.get("Members@odata.nextLink")
    return out


def inventory(c):
    root = get(c, "/redfish/v1/")
    rows = []
    systems = collection(c, root["Systems"]["@odata.id"])
    managers = {m["@odata.id"].rstrip("/"): m for m in collection(c, root["Managers"]["@odata.id"])}
    for s in systems:
        procs = collection(c, s["Processors"]["@odata.id"]) if "Processors" in s else []
        cpus = [p for p in procs if p.get("ProcessorType") == "CPU"]
        gpus = [p for p in procs if p.get("ProcessorType") == "GPU"]
        mgr = (s.get("Links", {}).get("ManagedBy") or [{}])[0].get("@odata.id", "").rstrip("/")
        m = managers.get(mgr, {})
        rows.append({
            "system": s["@odata.id"].rsplit("/", 1)[-1],
            "type": s.get("SystemType", ""),
            "model": s.get("Model") or "",
            "serial": s.get("SerialNumber") or "",
            "uuid": s.get("UUID") or "",
            "power": s.get("PowerState") or "",
            "health": (s.get("Status") or {}).get("HealthRollup") or (s.get("Status") or {}).get("Health") or "",
            "bios": s.get("BiosVersion") or "",
            "cpus": len(cpus) or (s.get("ProcessorSummary") or {}).get("Count") or "",
            "gpus": len(gpus) if procs else "",
            "mem_gib": (s.get("MemorySummary") or {}).get("TotalSystemMemoryGiB") or "",
            "bmc": mgr.rsplit("/", 1)[-1],
            "bmc_fw": m.get("FirmwareVersion") or "",
        })
    return rows


if __name__ == "__main__":
    base, user, pw = sys.argv[1:4]
    c = Client(base, user, pw)
    rows = inventory(c)
    if "--csv" in sys.argv:
        w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]) if rows else [])
        w.writeheader(); w.writerows(rows)
    else:
        for r in rows:
            print("  ".join(f"{k}={v}" for k, v in r.items() if v != ""))
    c.logout()
