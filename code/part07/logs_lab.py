#!/usr/bin/env python3
"""Self-checking lab for chapter 7.11: log services, entries, overwrite policy, clearing, diagnostic bundles.

In-process mock with a simulated clock. A pass means the mock and rf_logs.py follow the Redfish log model
(LogService, LogEntry, ClearLog, CollectDiagnosticData). It says nothing about what a real BMC logs.
"""
import os, sys, tempfile, threading
from redfish_mock import make_server
from redfish_crawl import Client
from protocol_lab import call
import mock_logs
import rf_logs

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def main():
    srv, st = make_server("dgx", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    clock = [1_800_000_000.0]
    st.now = lambda: clock[0]
    c = Client(base, "admin", "adminpass")
    SYS = "/redfish/v1/Systems/System_0"
    MEL = "/redfish/v1/Managers/BMC_0/LogServices/EventLog"
    SEL = "/redfish/v1/Managers/BMC_0/LogServices/SEL"
    SEVL = "/redfish/v1/Systems/System_0/LogServices/EventLog"

    svcs = rf_logs.log_services(c)
    check("3 log services are found by following links: manager EventLog, manager SEL, system EventLog",
          sorted((o, s["Id"], s.get("LogEntryType")) for o, _, s in svcs) == [("Manager", "EventLog", "Event"), ("Manager", "SEL", "SEL"), ("System", "EventLog", "Event")],
          [(o, s["Id"]) for o, _, s in svcs])

    # events become log entries
    call(base, "POST", SYS + "/Actions/ComputerSystem.Reset", {"ResetType": "ForceOff"})
    call(base, "POST", SYS + "/Actions/ComputerSystem.Reset", {"ResetType": "On"})
    s, h, b = call(base, "GET", MEL + "/Entries")
    check("a power state change is written to the manager event log (2 entries, members inline)",
          b["Members@odata.count"] == 2 and "Message" in b["Members"][0], (b["Members@odata.count"], list(b["Members"][0])[:4]))
    e = b["Members"][0]
    check("each entry has EntryType Event, a MessageId, Severity, Created and the origin resource",
          e["EntryType"] == "Event" and e["MessageId"].startswith("ResourceEvent.") and e["Severity"] == "OK" and e["Created"].endswith("Z")
          and e["Links"]["OriginOfCondition"]["@odata.id"] == SYS, e)
    s, h, b = call(base, "GET", SEVL + "/Entries")
    check("the same events are in the system event log", b["Members@odata.count"] == 2)
    s, h, b = call(base, "GET", MEL + "/Entries?$top=1")
    check("$top=1 pages the log and gives a nextLink", len(b["Members"]) == 1 and "Members@odata.nextLink" in b and b["Members@odata.count"] == 2, b.get("Members@odata.nextLink"))
    check("entries are returned in order, oldest first", [m["Id"] for m in call(base, "GET", MEL + "/Entries")[2]["Members"]] == ["1", "2"])

    # schema validation (optional)
    try:
        import schema_tools
        if os.environ.get("REDFISH_PUBLICATIONS"):
            errs = []
            for u in (MEL, SEL, MEL + "/Entries/1", "/redfish/v1/Managers/BMC_0/LogServices"):
                errs += schema_tools.validate_payload(call(base, "GET", u)[2]) or []
            mock_logs.add_entry(st, SEL, "Critical", "Upper Critical - going high", sensor={"type": "Temperature", "number": 12})
            errs += schema_tools.validate_payload(call(base, "GET", SEL + "/Entries/1")[2]) or []
            check("log service, collection, an Event entry and an SEL entry validate against the official schemas", not errs, errs)
            mock_logs.clear(st, SEL)
    except ImportError:
        print("SKIP  schema check needs jsonschema and referencing")

    # severity filter and grouping through the tool
    mock_logs.add_entry(st, SEL, "Critical", "Upper Critical - going high", sensor={"type": "Temperature", "number": 12, "code": "Upper Critical - going high"})
    mock_logs.add_entry(st, MEL, "Warning", "Fan 3 speed low", "Base.1.17.Success", ["3"], "/redfish/v1/Chassis/Chassis_0", group="grp-7")
    mock_logs.add_entry(st, MEL, "Warning", "Fan 3 redundancy lost", "Base.1.17.Success", ["3"], "/redfish/v1/Chassis/Chassis_0", group="grp-7")
    rows = []
    for owner, oid, svc in rf_logs.log_services(c):
        rows += [rf_logs.norm(oid, svc, x) for x in rf_logs.entries(c, svc)]
    crit = [r for r in rows if rf_logs.SEV.get(r["severity"], 0) >= 2]
    check("filtering at Critical finds the SEL entry, with its sensor type and entry code", len(crit) == 1 and crit[0]["sensor"] == "Temperature" and crit[0]["code"].startswith("Upper Critical"), crit)
    grp = [r for r in rows if r["group"] == "grp-7"]
    check("entries with the same EventGroupId can be grouped (same cause)", len(grp) == 2, len(grp))

    # overwrite policy
    L = st.logs[MEL]
    L["max"] = 5
    mock_logs.rebuild(st, MEL)
    for i in range(8):
        mock_logs.add_entry(st, MEL, "OK", f"filler {i}")
    ids = [x["Id"] for x in L["entries"]]
    check("WrapsWhenFull keeps the newest 5 entries and drops the oldest (ids keep counting up)", len(ids) == 5 and ids[-1] == "12" and int(ids[0]) > 1, ids)
    L["policy"] = "NeverOverWrites"
    mock_logs.rebuild(st, MEL)
    before = [x["Id"] for x in L["entries"]]
    r = mock_logs.add_entry(st, MEL, "Critical", "this event is lost")
    check("NeverOverWrites discards new entries when full", r is None and [x["Id"] for x in L["entries"]] == before)
    svc = call(base, "GET", MEL)[2]
    probs = rf_logs.service_problems(svc, 5, clock[0])
    check("the tool warns about a full NeverOverWrites log", any("DISCARDED" in p for p in probs), probs)
    probs = rf_logs.service_problems(svc, 5, clock[0] - 2000)
    check("the tool warns when the BMC clock differs from ours by 2000 s", any("clock differs" in p for p in probs), probs)
    L["policy"] = "WrapsWhenFull"; L["max"] = 200
    mock_logs.rebuild(st, MEL)

    # clear
    etag = call(base, "GET", MEL + "/Entries")[1]["ETag"]
    mock_logs.add_entry(st, MEL, "OK", "arrived after I read the log")
    s, _, _ = call(base, "POST", MEL + "/Actions/LogService.ClearLog", {"LogEntriesETag": etag})
    check("ClearLog with a stale LogEntriesETag is refused (412): the log changed since you looked", s == 412, s)
    s, _, _ = call(base, "POST", MEL + "/Actions/LogService.ClearLog", {}, auth=("viewer", "viewpass"))
    check("a ReadOnly user cannot clear a log (403)", s == 403, s)
    etag = call(base, "GET", MEL + "/Entries")[1]["ETag"]
    s, _, _ = call(base, "POST", MEL + "/Actions/LogService.ClearLog", {"LogEntriesETag": etag})
    check("ClearLog with the current ETag works (204) and the log is empty", s == 204 and call(base, "GET", MEL + "/Entries")[2]["Members@odata.count"] == 0, s)

    # diagnostic bundle
    call(base, "POST", SYS + "/Actions/ComputerSystem.Reset", {"ResetType": "ForceOff"})
    s, h, b = call(base, "POST", MEL + "/Actions/LogService.CollectDiagnosticData", {"DiagnosticDataType": "Banana"})
    check("an unknown DiagnosticDataType gives 400", s == 400, s)
    s, h, b = call(base, "POST", MEL + "/Actions/LogService.CollectDiagnosticData", {})
    check("a missing DiagnosticDataType gives 400", s == 400, s)
    s, h, b = call(base, "POST", MEL + "/Actions/LogService.CollectDiagnosticData", {"DiagnosticDataType": "Manager"})
    check("CollectDiagnosticData is a long action: 202 with a task monitor", s == 202 and "TaskMonitors" in h.get("Location", ""), (s, h))
    out = []
    path = os.path.join(tempfile.mkdtemp(), "bundle.bin")
    sleep = lambda x: clock.__setitem__(0, clock[0] + x)
    # the monitor above is still running; the tool starts its own collection
    rc = rf_logs.collect_bundle(c, path, sleep=sleep, now=lambda: clock[0], out=out.append)
    data = open(path, "rb").read() if os.path.exists(path) else b""
    check("the tool collects a bundle: saved file has the size the log entry promised", rc == 0 and data.startswith(b"DIAGNOSTIC BUNDLE") and f"{len(data)} bytes" in out[-1], (rc, out))
    last = st.logs[MEL]["entries"][-1]
    check("the new log entry carries AdditionalDataURI, AdditionalDataSizeBytes and DiagnosticDataType",
          last["AdditionalDataURI"].endswith("/attachment") and last["AdditionalDataSizeBytes"] == len(data) and last["DiagnosticDataType"] == "Manager", last)
    s_, h_, b_ = call(base, "POST", MEL + "/Actions/LogService.CollectDiagnosticData", {"DiagnosticDataType": "Manager"})
    clock[0] += 25
    s_, h_, b_ = call(base, "GET", h_["Location"])
    entry = call(base, "GET", h_.get("Location", "/none"))[2] if h_.get("Location") else {}
    check("when the task ends, its Location header is the new LogEntry, which has the download address (schema rule)",
          s_ == 200 and "/LogServices/EventLog/Entries/" in h_.get("Location", "") and entry.get("AdditionalDataURI", "").endswith("/attachment"), (s_, h_.get("Location")))
    out.clear()
    # force a mismatch: next collection returns an entry whose size field we corrupt right after creation
    orig = mock_logs.make_dump
    def corrupt(st_, svc_):
        e = orig(st_, svc_); e["AdditionalDataSizeBytes"] += 5; return e
    mock_logs.make_dump = corrupt
    rc = rf_logs.collect_bundle(c, path + "3", sleep=sleep, now=lambda: clock[0], out=out.append)
    mock_logs.make_dump = orig
    check("the tool detects a size mismatch between the entry and the downloaded data (exit 7)", rc == 7 and "size mismatch" in out[-1], (rc, out))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
