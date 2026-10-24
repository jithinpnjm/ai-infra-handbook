#!/usr/bin/env python3
"""Read power, thermal and sensor data from any Redfish service, new layout or old, and flag problems.

  rf_sensors.py http://host:port user password [--all] [--prom]

For every chassis it tries, in this order (all discovered from links, no fixed addresses):
  1. Sensors collection        (current design: one Sensor resource per measurement)
  2. Thermal  (Temperatures, Fans)   and  Power (Voltages, PowerControl, PowerSupplies)   (old design, deprecated)
It normalises everything to rows: chassis, source, name, kind, reading, units, health, upper-critical limit,
then flags: health not OK, reading at or above the upper critical or fatal threshold (checked by VALUE, not only
by the BMC's own health flag), and an enabled sensor with no reading (null).
--prom prints Prometheus text format instead of a report. This is a teaching tool, not a monitoring product.
"""
import sys
from redfish_crawl import Client
from rf_inventory import get, collection


def health(r):
    s = r.get("Status") or {}
    return s.get("Health"), s.get("State")


def from_sensors(c, chassis):
    rows = []
    link = chassis.get("Sensors", {}).get("@odata.id")
    if not link:
        return rows
    for s in collection(c, link):
        th = s.get("Thresholds") or {}
        def lim(n):
            return (th.get(n) or {}).get("Reading")
        h, st = health(s)
        rows.append(dict(source="Sensors", name=s.get("Name") or s.get("Id"), kind=s.get("ReadingType") or "?",
                         ctx=s.get("PhysicalContext") or "", reading=s.get("Reading") if s.get("Reading") is not None else s.get("SpeedRPM"),
                         units=s.get("ReadingUnits") or ("RPM" if "SpeedRPM" in s else ""), health=h, state=st,
                         caution=lim("UpperCaution"), critical=lim("UpperCritical"), fatal=lim("UpperFatal")))
    return rows


def from_legacy(c, chassis):
    rows = []
    t = chassis.get("Thermal", {}).get("@odata.id")
    if t and (th := get(c, t)):
        for x in th.get("Temperatures", []):
            h, st = health(x)
            rows.append(dict(source="Thermal", name=x.get("Name"), kind="Temperature", ctx=x.get("PhysicalContext") or "",
                             reading=x.get("ReadingCelsius"), units="Cel", health=h, state=st,
                             caution=x.get("UpperThresholdNonCritical"), critical=x.get("UpperThresholdCritical"),
                             fatal=x.get("UpperThresholdFatal")))
        for x in th.get("Fans", []):
            h, st = health(x)
            rows.append(dict(source="Thermal", name=x.get("Name") or x.get("FanName"), kind="Rotational", ctx=x.get("PhysicalContext") or "",
                             reading=x.get("Reading"), units=x.get("ReadingUnits") or "", health=h, state=st,
                             caution=None, critical=x.get("UpperThresholdCritical"), fatal=x.get("UpperThresholdFatal")))
    p = chassis.get("Power", {}).get("@odata.id")
    if p and (pw := get(c, p)):
        for x in pw.get("Voltages", []):
            h, st = health(x)
            rows.append(dict(source="Power", name=x.get("Name"), kind="Voltage", ctx=x.get("PhysicalContext") or "",
                             reading=x.get("ReadingVolts"), units="V", health=h, state=st,
                             caution=x.get("UpperThresholdNonCritical"), critical=x.get("UpperThresholdCritical"),
                             fatal=x.get("UpperThresholdFatal")))
        for x in pw.get("PowerControl", []):
            h, st = health(x)
            rows.append(dict(source="Power", name=x.get("Name"), kind="Power", ctx="Chassis",
                             reading=x.get("PowerConsumedWatts"), units="W", health=h, state=st,
                             caution=None, critical=x.get("PowerCapacityWatts"), fatal=None))
        for x in pw.get("PowerSupplies", []):
            h, st = health(x)
            rows.append(dict(source="Power", name=x.get("Name"), kind="Power", ctx="PowerSupply",
                             reading=x.get("PowerInputWatts") if x.get("PowerInputWatts") is not None else x.get("LastPowerOutputWatts"),
                             units="W", health=h, state=st, caution=None, critical=x.get("PowerCapacityWatts"), fatal=None))
    return rows


def flags(r):
    out = []
    if r["state"] in ("Disabled", "Absent"):
        return out
    if r["health"] not in (None, "OK"):
        out.append(f"health={r['health']}")
    v = r["reading"]
    if r["state"] == "Enabled" and v is None:
        out.append("no reading")
    if isinstance(v, (int, float)):
        if r["fatal"] is not None and v >= r["fatal"]:
            out.append(f"AT/ABOVE FATAL limit {r['fatal']}")
        elif r["critical"] is not None and v >= r["critical"]:
            out.append(f"AT/ABOVE CRITICAL limit {r['critical']}")
        elif r["caution"] is not None and v >= r["caution"]:
            out.append(f"above caution limit {r['caution']}")
    return out


def collect(c):
    root = get(c, "/redfish/v1/")
    result = []
    for ch in collection(c, root["Chassis"]["@odata.id"]):
        rows = from_sensors(c, ch)
        used = "Sensors"
        if not rows:
            rows = from_legacy(c, ch)
            used = "legacy Thermal/Power" if rows else "none"
        for r in rows:
            r["chassis"] = ch["@odata.id"].rsplit("/", 1)[-1]
            r["flags"] = flags(r)
        result.append((ch["@odata.id"].rsplit("/", 1)[-1], used, rows))
    return result


def prom(result):
    lines = ["# TYPE redfish_sensor_reading gauge", "# TYPE redfish_sensor_ok gauge"]
    def esc(x): return str(x).replace("\\", "\\\\").replace('"', '\\"')
    for ch, used, rows in result:
        for r in rows:
            if isinstance(r["reading"], (int, float)):
                lab = f'chassis="{esc(ch)}",sensor="{esc(r["name"])}",kind="{esc(r["kind"])}",units="{esc(r["units"])}"'
                lines.append(f"redfish_sensor_reading{{{lab}}} {r['reading']}")
                lines.append(f"redfish_sensor_ok{{{lab}}} {0 if r['flags'] else 1}")
    return "\n".join(lines)


if __name__ == "__main__":
    base, user, pw = sys.argv[1:4]
    c = Client(base, user, pw)
    res = collect(c)
    if "--prom" in sys.argv:
        print(prom(res))
    else:
        total = flagged = 0
        for ch, used, rows in res:
            print(f"chassis {ch}: {len(rows)} readings via {used}")
            for r in rows:
                total += 1; flagged += bool(r["flags"])
                if "--all" in sys.argv or r["flags"]:
                    print(f"   {r['source']:8} {str(r['name'])[:34]:34} {r['kind']:12} {r['reading']!s:>8} {r['units']:5} {'; '.join(r['flags'])}")
        print(f"\n{total} readings, {flagged} flagged")
    c.logout()
