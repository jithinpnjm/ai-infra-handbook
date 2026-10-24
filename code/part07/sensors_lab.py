#!/usr/bin/env python3
"""Self-checking lab for chapter 7.8: read sensors in both layouts, flag problems by value, export for Prometheus.

Runs in-process. Part A uses the teaching mock. Part B uses DMTF's rack-server example (set REDFISH_PUBLICATIONS to
a clone of DMTF/Redfish-Publications) and removes the modern Sensors link to force the old Thermal/Power route.
The Prometheus check needs the prometheus_client package; it is skipped if missing.
"""
import os, sys, threading
from redfish_mock import make_server
from redfish_crawl import Client
import rf_sensors

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def serve(**kw):
    srv, st = make_server("dgx", 0, **kw)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, st, f"http://127.0.0.1:{srv.server_address[1]}"


def main():
    srv, st, base = serve()
    c = Client(base, "admin", "adminpass")
    S = "/redfish/v1/Chassis/Chassis_0/Sensors/"

    res = rf_sensors.collect(c)
    ch, used, rows = res[0]
    check("mock: 4 readings found through the Sensors collection", used == "Sensors" and len(rows) == 4, (used, len(rows)))
    check("mock: nothing is flagged when all values are normal", not any(r["flags"] for r in rows))

    st.tree[S + "Temp_GPU0"]["Reading"] = 92.0
    rows = rf_sensors.collect(c)[0][2]
    gpu = [r for r in rows if r["name"] == "Temp GPU0"][0]
    check("a reading above the critical threshold is flagged even though the BMC's Health still says OK",
          any("CRITICAL" in f for f in gpu["flags"]) and gpu["health"] == "OK", gpu["flags"])

    st.tree[S + "Temp_GPU0"]["Reading"] = 85.0
    gpu = [r for r in rf_sensors.collect(c)[0][2] if r["name"] == "Temp GPU0"][0]
    check("between caution and critical: flagged as 'above caution'", any("caution" in f for f in gpu["flags"]), gpu["flags"])

    st.tree[S + "Temp_GPU0"]["Reading"] = None
    gpu = [r for r in rf_sensors.collect(c)[0][2] if r["name"] == "Temp GPU0"][0]
    check("an enabled sensor with a null reading is flagged 'no reading'", "no reading" in gpu["flags"], gpu["flags"])

    st.tree[S + "Temp_GPU0"]["Reading"] = 61.0
    st.tree[S + "Fan_1"]["Status"] = {"State": "Enabled", "Health": "Critical"}
    fan = [r for r in rf_sensors.collect(c)[0][2] if r["name"] == "Fan 1"][0]
    check("a sensor whose Health is Critical is flagged", "health=Critical" in fan["flags"], fan["flags"])

    st.tree[S + "Fan_1"]["Status"] = {"State": "Disabled"}
    st.tree[S + "Fan_1"]["Reading"] = None
    fan = [r for r in rf_sensors.collect(c)[0][2] if r["name"] == "Fan 1"][0]
    check("a Disabled sensor is not flagged (nothing to read)", fan["flags"] == [], fan["flags"])

    out = rf_sensors.prom(rf_sensors.collect(c))
    check("Prometheus output has one reading and one ok-line per numeric sensor",
          out.count("redfish_sensor_reading{") == 3 and out.count("redfish_sensor_ok{") == 3, out)
    try:
        from prometheus_client.parser import text_string_to_metric_families
        fams = list(text_string_to_metric_families(out))
        samples = sum(len(f.samples) for f in fams)
        check("the Prometheus text parses with the official client library", samples == 6, samples)
    except ImportError:
        print("SKIP  prometheus_client not installed")
    c.logout(); srv.shutdown()

    root = os.environ.get("REDFISH_PUBLICATIONS")
    if not root:
        print("SKIP  part B needs REDFISH_PUBLICATIONS")
    else:
        mock = os.path.join(root, "mockups", "public-rackmount1")
        srv, st, base = serve(mockup=mock)
        c = Client(base, "admin", "adminpass")
        ch, used, rows = rf_sensors.collect(c)[0]
        modern = len(rows)
        check(f"DMTF rack server: {modern} readings through the modern Sensors collection", used == "Sensors" and modern > 30, (used, modern))
        del st.tree["/redfish/v1/Chassis/1U"]["Sensors"]
        ch, used, rows = rf_sensors.collect(c)[0]
        kinds = {r["kind"] for r in rows}
        sources = {r["source"] for r in rows}
        check(f"with Sensors removed the old route is used: {len(rows)} readings from Thermal and Power",
              used.startswith("legacy") and sources == {"Thermal", "Power"} and len(rows) >= 5, (used, sources, len(rows)))
        check("the old route covers temperatures, fans, voltages and power", {"Temperature", "Rotational", "Voltage", "Power"} <= kinds, kinds)
        flagged = [r for r in rows if r["flags"]]
        check("the old route flags the same kind of problem (an enabled sensor above a limit or with Warning health)", len(flagged) >= 1,
              [(r["name"], r["reading"]) for r in rows[:5]])
        c.logout(); srv.shutdown()

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
