#!/usr/bin/env python3
"""Record a Redfish service into a mockup folder (one index.json per URI), like DMTF's mockup format.

  rf_record.py https://bmc user password OUTDIR [--redact]

Then serve the recording with:  redfish_mock.py --mockup OUTDIR
Why: capture a real DGX or HGX tree once, then develop and test automation offline, forever, with no risk to
the machine. Serial numbers, MAC addresses and IP addresses are real data: --redact replaces the common ones.
Only GET is used. Run it with permission. Sessions are closed at the end.
"""
import json, os, re, sys
from redfish_crawl import Client, links

REDACT = {"SerialNumber", "UUID", "MACAddress", "PermanentMACAddress", "AssetTag", "HostName", "FQDN", "SKU"}


def redact(o):
    if isinstance(o, dict):
        return {k: ("REDACTED" if k in REDACT and isinstance(v, str) and v else redact(v)) for k, v in o.items()}
    if isinstance(o, list):
        return [redact(x) for x in o]
    if isinstance(o, str) and re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", o):
        return "0.0.0.0"
    return o


def record(c, outdir, do_redact=False):
    todo, seen, saved = ["/redfish/v1/"], set(), 0
    while todo:
        u = todo.pop().split("#")[0]
        key = u.rstrip("/")
        if key in seen or not key.startswith("/redfish/v1") or "/SessionService/Sessions/" in key or key.endswith("/attachment"):
            continue
        seen.add(key)
        st, _, body = c.req("GET", u)
        if st != 200 or not isinstance(body, dict):
            continue
        rel = key[len("/redfish/v1"):].strip("/")
        d = os.path.join(outdir, rel)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.json"), "w") as f:
            json.dump(redact(body) if do_redact else body, f, indent=2)
        saved += 1
        for l in links({k: v for k, v in body.items() if k not in ("@odata.id", "Actions")}):
            if l.startswith("/redfish/") and l.rstrip("/") not in seen:
                todo.append(l)
    return saved


if __name__ == "__main__":
    base, user, pw, out = sys.argv[1:5]
    c = Client(base, user, pw)
    try:
        n = record(c, out, "--redact" in sys.argv)
    finally:
        c.logout()
    print(f"recorded {n} resources into {out}")
