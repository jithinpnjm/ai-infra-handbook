#!/usr/bin/env python3
"""Read Redfish logs, check the log services themselves, and collect a diagnostic bundle.

  rf_logs.py services http://host:port user pw                      list every log service, its size and policy
  rf_logs.py show     http://host:port user pw [--min Warning] [--since 2026-10-24T00:00:00Z] [--grep text]
  rf_logs.py collect  http://host:port user pw --out bundle.bin [--yes]
  rf_logs.py clear    http://host:port user pw --service <uri> [--yes]       (never clears unless --yes)

Log services are found by following LogServices links from Managers, Systems and Chassis, so it works on any
service. Entries are normalised: time, severity, type, message id, text, origin. A log that is nearly full
(and NeverOverWrites) or a BMC clock that disagrees with yours is reported, because both make logs misleading.
"""
import calendar, sys, time
from redfish_crawl import Client, links
from rf_inventory import get

SEV = {"OK": 0, "Warning": 1, "Critical": 2}


def log_services(c):
    root = get(c, "/redfish/v1/")
    out = []
    for fam in ("Managers", "Systems", "Chassis"):
        if fam not in root:
            continue
        coll = get(c, root[fam]["@odata.id"]) or {}
        for m in coll.get("Members", []):
            owner = get(c, m["@odata.id"]) or {}
            ls = owner.get("LogServices", {}).get("@odata.id")
            if not ls:
                continue
            for s in (get(c, ls) or {}).get("Members", []):
                svc = get(c, s["@odata.id"])
                if svc:
                    out.append((fam[:-1] if fam != "Chassis" else "Chassis", m["@odata.id"].rsplit("/", 1)[-1], svc))
    return out


def entries(c, svc, limit=2000):
    link = svc.get("Entries", {}).get("@odata.id")
    rows, seen = [], set()
    uri = link
    while uri and uri not in seen and len(rows) < limit:
        seen.add(uri)
        coll = get(c, uri)
        if not coll:
            break
        for m in coll.get("Members", []):
            e = m if "EntryType" in m else get(c, m["@odata.id"])
            if e:
                rows.append(e)
        uri = coll.get("Members@odata.nextLink")
    return rows


def parse_time(s):
    try:
        return calendar.timegm(time.strptime(s[:19], "%Y-%m-%dT%H:%M:%S"))
    except (TypeError, ValueError):
        return None


def short_id(mid):
    """'Registry.1.0.Name' -> 'Registry.Name' (raw SEL data is left as it is)."""
    parts = mid.split(".")
    return parts[0] + "." + ".".join(parts[3:]) if len(parts) >= 4 else mid


def norm(owner, svc, e):
    return dict(owner=owner, service=svc.get("Id"), id=e.get("Id"), created=e.get("Created") or e.get("EventTimestamp") or "",
                severity=e.get("Severity") or "", type=e.get("EntryType") or "", message_id=e.get("MessageId") or "",
                message=e.get("Message") or "", origin=((e.get("Links") or {}).get("OriginOfCondition") or e.get("OriginOfCondition") or {}).get("@odata.id", ""),
                group=e.get("EventGroupId") or "", resolved=e.get("Resolved"), attachment=e.get("AdditionalDataURI"),
                sensor=(e.get("SensorType") or ""), code=e.get("EntryCode") or "")


def service_problems(svc, n_entries, local_now, skew_limit=300):
    out = []
    mx = svc.get("MaxNumberOfRecords")
    if mx:
        fill = n_entries / mx
        if svc.get("OverWritePolicy") == "NeverOverWrites" and fill >= 0.8:
            out.append(f"{svc['Id']}: {n_entries}/{mx} entries and NeverOverWrites: new events will be DISCARDED when full")
        elif fill >= 0.95:
            out.append(f"{svc['Id']}: {n_entries}/{mx} entries, old entries are about to be overwritten")
    t = parse_time(svc.get("DateTime"))
    if t is not None and abs(t - local_now) > skew_limit:
        out.append(f"{svc['Id']}: BMC clock differs from this computer by {int(t - local_now)} s: timestamps will not line up")
    return out


def collect_bundle(c, out_path, sleep=time.sleep, now=time.time, out=print, timeout=300):
    """POST CollectDiagnosticData on the manager's event log, follow the task, download and size-check the attachment."""
    for owner, oid, svc in log_services(c):
        act = (svc.get("Actions") or {}).get("#LogService.CollectDiagnosticData")
        if not act:
            continue
        st, hd, body = c.req("POST", act["target"], {"DiagnosticDataType": "Manager"})
        if st != 202:
            out(f"collect refused: HTTP {st}"); return 3
        mon, start = hd["Location"], now()
        while True:
            st, h2, b2 = c.req("GET", mon)
            if st != 202:
                break
            if now() - start > timeout:
                out("TIMEOUT: result unknown"); return 4
            sleep(max(1, int(h2.get("Retry-After", 2))))
        if st != 200:
            out(f"collection failed: HTTP {st}"); return 5
        loc = h2.get("Location")
        e = get(c, loc) if loc else None           # the schema says the finished task's Location is the new LogEntry
        if not e or not e.get("AdditionalDataURI"):
            news = [x for x in entries(c, get(c, svc["@odata.id"])) if x.get("AdditionalDataURI")]
            e = news[-1] if news else None         # fallback for services that do not set Location
        if not e:
            out("no entry with attached data was created"); return 6
        import urllib.request
        r = urllib.request.Request(c.base + e["AdditionalDataURI"], headers={"X-Auth-Token": c.token})
        data = urllib.request.urlopen(r, timeout=30, context=c.ctx).read()
        if e.get("AdditionalDataSizeBytes") not in (None, len(data)):
            out(f"size mismatch: header says {e['AdditionalDataSizeBytes']} bytes, got {len(data)}"); return 7
        open(out_path, "wb").write(data)
        out(f"saved {len(data)} bytes to {out_path} (log entry {e['Id']}, {e.get('DiagnosticDataType')})")
        return 0
    out("no log service offers CollectDiagnosticData"); return 2


def main(argv):
    cmd, base, user, pw = argv[1:5]
    flags = argv[5:]
    val = lambda n, d=None: flags[flags.index(n) + 1] if n in flags else d
    c = Client(base, user, pw)
    try:
        if cmd == "services":
            for owner, oid, svc in log_services(c):
                n = len(entries(c, svc))
                print(f"{owner:8} {oid:12} {svc['Id']:10} type={str(svc.get('LogEntryType')):6} entries={n}/{svc.get('MaxNumberOfRecords')} policy={svc.get('OverWritePolicy')}")
                for p in service_problems(svc, n, time.time()):
                    print("   WARNING", p)
            return 0
        if cmd == "show":
            minsev = SEV.get(val("--min", "OK"), 0)
            since = parse_time(val("--since")) if val("--since") else None
            grep = val("--grep")
            rows = []
            for owner, oid, svc in log_services(c):
                for e in entries(c, svc):
                    r = norm(oid, svc, e)
                    if SEV.get(r["severity"], 0) < minsev:
                        continue
                    t = parse_time(r["created"])
                    if since and (t is None or t < since):
                        continue
                    if grep and grep.lower() not in (r["message"] + r["message_id"]).lower():
                        continue
                    rows.append(r)
            rows.sort(key=lambda r: r["created"])
            for r in rows:
                print(f"{r['created']} {r['owner']}/{r['service']:8} {r['severity']:8} {short_id(r['message_id'])[:38]:38} {r['message']}")
            print(f"\n{len(rows)} entries")
            return 0
        if cmd == "collect":
            return collect_bundle(c, val("--out", "bundle.bin"))
        if cmd == "clear":
            target = val("--service")
            if "--yes" not in flags:
                print(f"DRY RUN: would clear {target}. Collect a bundle first, then add --yes."); return 0
            svc = get(c, target)
            act = svc["Actions"]["#LogService.ClearLog"]["target"]
            etag = get(c, svc["Entries"]["@odata.id"]) and c.req("GET", svc["Entries"]["@odata.id"])[1].get("ETag")
            st, _, b = c.req("POST", act, {"LogEntriesETag": etag} if etag else {})
            print(f"HTTP {st}")
            return 0 if st in (200, 204) else 1
        print(__doc__); return 2
    finally:
        c.logout()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
