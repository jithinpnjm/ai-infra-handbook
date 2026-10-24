"""Log services for redfish_mock.py (chapter 7.11): event logs, an IPMI-style SEL, ClearLog and CollectDiagnosticData."""
import hashlib, re

R = "/redfish/v1"


def odata(path, typ, **kw):
    d = {"@odata.id": path, "@odata.type": typ}
    d.update(kw)
    return d


def install_state(st):
    """Create log services: Manager EventLog (Event), Manager SEL (SEL entries), System EventLog (Event)."""
    st.logs = {}
    for owner, kind in ((st.mgr_uri, "Manager"), (st.sys_uri, "System")):
        base = f"{owner}/LogServices"
        names = [("EventLog", "Event", "Event log"), ("SEL", "SEL", "System Event Log (IPMI SEL)")] if kind == "Manager" else [("EventLog", "Event", "System event log")]
        st.tree[base] = odata(base, "#LogServiceCollection.LogServiceCollection", Name="Log Service Collection",
                              Members=[{"@odata.id": f"{base}/{n[0]}"} for n in names], **{"Members@odata.count": len(names)})
        for lid, etype, title in names:
            svc = f"{base}/{lid}"
            st.logs[svc] = {"entries": [], "next": 1, "type": etype, "max": 200, "policy": "WrapsWhenFull", "owner": owner, "attachments": {}}
            st.tree[owner].setdefault("LogServices", {"@odata.id": base})
            rebuild(st, svc)
    # wire the System links
    st.tree[st.sys_uri]["LogServices"] = {"@odata.id": f"{st.sys_uri}/LogServices"}
    st.tree[st.mgr_uri]["LogServices"] = {"@odata.id": f"{st.mgr_uri}/LogServices"}


def rebuild(st, svc):
    L = st.logs[svc]
    title = svc.rsplit("/", 1)[-1]
    acts = {"#LogService.ClearLog": {"target": f"{svc}/Actions/LogService.ClearLog"}}
    if L["owner"] == st.mgr_uri and title == "EventLog":
        acts["#LogService.CollectDiagnosticData"] = {
            "target": f"{svc}/Actions/LogService.CollectDiagnosticData",
            "DiagnosticDataType@Redfish.AllowableValues": ["Manager", "OEM"]}
    st.tree[svc] = odata(svc, "#LogService.v1_9_0.LogService", Id=title, Name=f"{title} log service", LogEntryType=L["type"],
                         OverWritePolicy=L["policy"], MaxNumberOfRecords=L["max"], ServiceEnabled=True,
                         DateTime=time_iso(st.now()), DateTimeLocalOffset="+00:00",
                         Entries={"@odata.id": f"{svc}/Entries"}, Status={"State": "Enabled", "Health": "OK"}, Actions=acts)
    members = [{"@odata.id": e["@odata.id"]} for e in L["entries"]]
    st.tree[f"{svc}/Entries"] = odata(f"{svc}/Entries", "#LogEntryCollection.LogEntryCollection", Name=f"{title} entries",
                                      Members=members, **{"Members@odata.count": len(members)})
    for e in L["entries"]:
        st.tree[e["@odata.id"]] = e


def time_iso(t):
    import time
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def add_entry(st, svc, severity="OK", message="", message_id=None, args=None, origin=None, group=None, sensor=None, extra=None):
    """Append an entry to a log service, honouring MaxNumberOfRecords and OverWritePolicy. Returns the entry or None."""
    L = st.logs[svc]
    if len(L["entries"]) >= L["max"]:
        if L["policy"] == "NeverOverWrites":
            return None
        old = L["entries"].pop(0)
        st.tree.pop(old["@odata.id"], None)
    eid = str(L["next"]); L["next"] += 1
    uri = f"{svc}/Entries/{eid}"
    now = time_iso(st.now())
    e = odata(uri, "#LogEntry.v1_22_0.LogEntry", Id=eid, Name=f"Log entry {eid}", EntryType=L["type"], Severity=severity,
              Created=now, Message=message)
    if L["type"] == "Event":
        e["MessageId"] = message_id or "Base.1.17.Success"
        e["MessageArgs"] = [str(a) for a in (args or [])]
        e["EventTimestamp"] = now
        if origin:
            e["Links"] = {"OriginOfCondition": {"@odata.id": origin}}
        if group:
            e["EventGroupId"] = group
    else:
        s = sensor or {}
        e["SensorType"] = s.get("type", "Temperature"); e["SensorNumber"] = s.get("number", 1)
        e["EntryCode"] = s.get("code", "Upper Critical - going high")
        e["MessageId"] = s.get("data", "0x57 0x00 0xff")
    e.update(extra or {})
    L["entries"].append(e)
    rebuild(st, svc)
    return e


def log_event(st, message_id, severity, message, origin=None, args=None, group=None):
    """Record an event in the manager and system event logs (called from the mock's event machinery)."""
    for svc in (f"{st.mgr_uri}/LogServices/EventLog", f"{st.sys_uri}/LogServices/EventLog"):
        add_entry(st, svc, severity, message, message_id, args, origin, group)


def clear(st, svc):
    L = st.logs[svc]
    for e in L["entries"]:
        st.tree.pop(e["@odata.id"], None)
    L["entries"] = []
    L["attachments"] = {}
    rebuild(st, svc)


def make_dump(st, svc):
    """Build a fake diagnostic bundle (text) and attach it to a new log entry."""
    L = st.logs[svc]
    body = ("DIAGNOSTIC BUNDLE (teaching mock)\n" + "\n".join(f"{e['Created']} {e['Severity']} {e['Message']}" for e in L["entries"]) + "\n").encode()
    e = add_entry(st, svc, "OK", "Diagnostic data collected.", "Base.1.17.Success", extra={})
    if e is None:
        return None
    eid = e["Id"]
    e["DiagnosticDataType"] = "Manager"
    e["AdditionalDataURI"] = f"{svc}/Entries/{eid}/attachment"
    e["AdditionalDataSizeBytes"] = len(body)
    L["attachments"][eid] = body
    rebuild(st, svc)
    return e
