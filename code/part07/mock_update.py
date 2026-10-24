"""Firmware inventory and UpdateService for redfish_mock.py (chapter 7.10). Teaching code, not a real updater.

Image format (INVENTED for this lab, real packages are vendor formats such as NVIDIA .fwpkg):
    b"FWPKG1\\n" + one JSON header line + b"\\n" + payload bytes
    header = {"component": "BIOS", "version": "1.28", "sha256": "<hex of payload>", "min_version": "1.10"}
The mock fetches the image, checks the header and the hash, and plays the update out over a task with the
stage messages from the DMTF Update message registry (TransferringToComponent, VerifyingAtComponent,
InstallingOnComponent, AwaitToActivate or UpdateSuccessful, or a failure message).
Components differ in how they activate: 'BMC' needs a Manager.Reset, 'SYSTEM' needs a ComputerSystem.Reset,
None applies at once.
"""
import copy, email.parser, email.policy, hashlib, json, re, urllib.request, urllib.error

R = "/redfish/v1"
FW = f"{R}/UpdateService/FirmwareInventory"

# id, name, version, activation, software id, group
# The GPU-tray ids and versions follow the BCM 11 Administrator Manual's DGX H100 example (HGX_FW_GPU_SXM_n and so on).
COMPONENTS = [("HostBMC_0", "BMC firmware", "1.00.0", "BMC", "BMC", None),
              ("HostBIOS_0", "System BIOS", "1.20", "SYSTEM", "BIOS", None),
              ("NIC_FW", "NIC firmware", "28.39.1002", "SYSTEM", "NIC", None),
              ("CPLD_0", "Motherboard CPLD", "0.9", None, "CPLD", None)]
# the 30 GPU-tray components listed in the BCM manual (versions are the 'before' values from its example)
_TRAY = [("HGX_FW_BMC_0", "HGX-22.10-1-rc1"), ("HGX_FW_FPGA_0", "2.0A"), ("HGX_FW_ERoT_BMC_0", "00.02.0100.0000_n00"),
         ("HGX_FW_ERoT_FPGA_0", "00.02.0100.0000_n00")]
_TRAY += [(f"HGX_FW_ERoT_NVSwitch_{i}", "00.02.0100.0000_n00") for i in range(4)] + [("HGX_FW_ERoT_PCIeSwitch_0", "00.02.0100.0000_n00")]
_TRAY += [(f"HGX_FW_GPU_SXM_{i}", "96.00.70.00.01") for i in range(1, 9)] + [(f"HGX_FW_NVSwitch_{i}", "96.00.3F.00.01") for i in range(4)]
_TRAY += [(f"HGX_FW_PCIeRetimer_{i}", "2.7.0") for i in range(8)] + [("HGX_FW_PCIeSwitch_0", "1.7.5A")]
COMPONENTS += [(cid, cid.replace("HGX_FW_", "").replace("_", " ") + " firmware", ver, "AC", cid, "GPUTRAY") for cid, ver in _TRAY]


def version_tuple(v):
    """Compare version strings piece by piece; numbers sort before text so mixed formats never crash."""
    return tuple((0, int(x), "") if x.isdigit() else (1, 0, x) for x in re.split(r"[.\-_]", str(v)))


def install_state(st):
    st.fw = {}
    st.max_image = 64 * 1024 * 1024
    st.pending_apply = []                       # (activation, fw id, version) waiting for a reset
    sysid = next(u for u in st.tree if u.startswith(f"{R}/Systems/") and u.count("/") == 4)
    mgrid = next(u for u in st.tree if u.startswith(f"{R}/Managers/") and u.count("/") == 4)
    members = []
    for cid, name, ver, act, sid, grp in COMPONENTS:
        st.fw[cid] = dict(name=name, version=ver, activation=act, sid=sid, state="Enabled", group=grp)
        members.append({"@odata.id": f"{FW}/{cid}"})
    st.tree[f"{R}/UpdateService"] = {
        "@odata.id": f"{R}/UpdateService", "@odata.type": "#UpdateService.v1_17_1.UpdateService", "Id": "UpdateService",
        "Name": "Update Service", "ServiceEnabled": True, "MaxImageSizeBytes": st.max_image,
        "FirmwareInventory": {"@odata.id": FW}, "MultipartHttpPushUri": f"{R}/UpdateService/upload",
        "Status": {"State": "Enabled", "Health": "OK"},
        "Actions": {"#UpdateService.SimpleUpdate": {
                        "target": f"{R}/UpdateService/Actions/UpdateService.SimpleUpdate",
                        "TransferProtocol@Redfish.AllowableValues": ["HTTP", "HTTPS"]},
                    "#UpdateService.StartUpdate": {"target": f"{R}/UpdateService/Actions/UpdateService.StartUpdate"}}}
    st.tree[FW] = {"@odata.id": FW, "@odata.type": "#SoftwareInventoryCollection.SoftwareInventoryCollection",
                   "Name": "Firmware Inventory", "Members": members, "Members@odata.count": len(members)}
    st.mgr_uri, st.sys_uri = mgrid, sysid
    for cid in st.fw:
        sync_fw(st, cid)
    st.tree[mgrid].setdefault("Actions", {})["#Manager.Reset"] = {
        "target": f"{mgrid}/Actions/Manager.Reset",
        "ResetType@Redfish.AllowableValues": ["GracefulRestart", "ForceRestart"]}
    st.tree[R]["UpdateService"] = {"@odata.id": f"{R}/UpdateService"}


def sync_fw(st, cid):
    f = st.fw[cid]
    u = f"{FW}/{cid}"
    related = [{"@odata.id": st.mgr_uri}] if f["activation"] == "BMC" else [{"@odata.id": st.sys_uri}]
    st.tree[u] = {"@odata.id": u, "@odata.type": "#SoftwareInventory.v1_15_0.SoftwareInventory", "Id": cid, "Name": f["name"],
                  "Version": f["version"], "Updateable": True, "SoftwareId": f["sid"], "Manufacturer": "ExampleCorp",
                  "VersionScheme": "DotIntegerNotation", "RelatedItem": related,
                  "Status": {"State": f["state"], "Health": "OK"}}


def parse_image(raw):
    """Return (header, payload) or raise ValueError."""
    if not raw.startswith(b"FWPKG1\n"):
        raise ValueError("not a firmware package")
    rest = raw[len(b"FWPKG1\n"):]
    line, _, payload = rest.partition(b"\n")
    return json.loads(line), payload


def fetch(uri):
    with urllib.request.urlopen(uri, timeout=3) as r:
        return r.read()


def start_update(st, raw_or_uri, targets, force, name_for_msgs, apply_time="Immediate"):
    """Decide the outcome now, play it out over a task. Returns (task id, response status override or None)."""
    msgs = []                                                  # list of (fraction_start, message id, args, severity)
    try:
        raw = raw_or_uri if isinstance(raw_or_uri, bytes) else fetch(raw_or_uri)
    except (urllib.error.URLError, OSError, ValueError):
        return st.new_task("Firmware update", {"status": 500, "body": err_body("TransferFailed", name_for_msgs)},
                           stages=[(0.0, "TransferringToComponent", [name_for_msgs, "target"], "OK"),
                                   (0.3, "TransferFailed", [name_for_msgs, "target"], "Critical")], fail=True, pending=(apply_time == "OnStartUpdateRequest"))
    try:
        header, payload = parse_image(raw)
    except ValueError:
        return st.new_task("Firmware update", {"status": 400, "body": err_body("VerificationFailed", name_for_msgs)},
                           stages=[(0.0, "TransferringToComponent", [name_for_msgs, "target"], "OK"),
                                   (0.3, "VerifyingAtComponent", [name_for_msgs, "target"], "OK"),
                                   (0.5, "VerificationFailed", [name_for_msgs, "target"], "Critical")], fail=True, pending=(apply_time == "OnStartUpdateRequest"))
    comp = header.get("component")
    cids = [k for k, f in st.fw.items() if f["sid"] == comp or (f.get("group") and f["group"] == comp)]
    wanted = [t.rstrip("/").rsplit("/", 1)[-1] for t in (targets or [])]
    stages = [(0.0, "TransferringToComponent", [name_for_msgs, comp], "OK"), (0.3, "VerifyingAtComponent", [name_for_msgs, comp], "OK")]
    pend = (apply_time == "OnStartUpdateRequest")
    if wanted:                                   # a target may be one member of a group package
        cids = [k for k in cids if k in wanted] or []
    if not cids:
        stages.append((0.5, "UpdateNotApplicable", [name_for_msgs, wanted[0] if wanted else comp], "Warning"))
        return st.new_task("Firmware update", {"status": 400, "body": err_body("UpdateNotApplicable", name_for_msgs, comp)}, stages=stages, fail=True, pending=pend)
    if hashlib.sha256(payload).hexdigest() != header.get("sha256"):
        stages.append((0.5, "VerificationFailed", [name_for_msgs, cids[0]], "Critical"))
        return st.new_task("Firmware update", {"status": 400, "body": err_body("VerificationFailed", name_for_msgs, cids[0])}, stages=stages, fail=True, pending=pend)
    versions = {k: (header.get("versions") or {}).get(k, header["version"]) for k in cids}
    first = cids[0]
    cur, new = st.fw[first]["version"], versions[first]
    if all(st.fw[k]["version"] == versions[k] for k in cids) and not force:
        stages.append((0.5, "UpdateSkippedSameVersion", [first, name_for_msgs], "OK"))
        return st.new_task("Firmware update", {"status": 200, "body": ok_body("UpdateSkippedSameVersion")}, stages=stages, pending=pend)
    low = header.get("min_version")
    lower = all(version_tuple(versions[k]) < version_tuple(st.fw[k]["version"]) for k in cids)
    if not force and (lower or (low and version_tuple(new) < version_tuple(low))):
        stages.append((0.5, "UpdateSkippedVersionTooLow", [first, name_for_msgs], "OK"))
        return st.new_task("Firmware update", {"status": 200, "body": ok_body("UpdateSkippedVersionTooLow")}, stages=stages, pending=pend)
    stages.append((0.6, "InstallingOnComponent", [name_for_msgs, first if len(cids) == 1 else comp], "OK"))
    acts = {st.fw[k]["activation"] for k in cids}

    def apply():
        for k in cids:
            if st.fw[k]["activation"] is None:
                st.fw[k]["version"] = versions[k]
            else:
                st.pending_apply.append((st.fw[k]["activation"], k, versions[k]))
            st.fw[k]["state"] = "Enabled"
            sync_fw(st, k)
    if acts == {None}:
        stages.append((0.9, "UpdateSuccessful", [first, name_for_msgs], "OK"))
        final = {"status": 200, "body": ok_body("UpdateSuccessful")}
    else:
        stages.append((0.9, "AwaitToActivate", [name_for_msgs, first if len(cids) == 1 else comp], "OK"))
        final = {"status": 200, "body": ok_body("AwaitToActivate")}
    final["apply"] = apply
    tid = st.new_task("Firmware update", final, stages=stages, pending=pend, on_start=lambda: [_mark(st, k) for k in cids])
    st.tasks[tid]["fw"] = cids
    if not pend:
        for k in cids:
            _mark(st, k)
    return tid


def _mark(st, cid):
    st.fw[cid]["state"] = "Updating"
    sync_fw(st, cid)


def ok_body(mid):
    m = {"@odata.type": "#Message.v1_1_1.Message", "MessageId": f"Update.1.0.{mid}", "Message": mid, "Severity": "OK"}
    return {"error": {"code": f"Update.1.0.{mid}", "message": mid, "@Message.ExtendedInfo": [m]}}


def err_body(mid, *args):
    m = {"@odata.type": "#Message.v1_1_1.Message", "MessageId": f"Update.1.0.{mid}", "Message": mid, "Severity": "Critical",
         "MessageArgs": [str(a) for a in args]}
    return {"error": {"code": f"Update.1.0.{mid}", "message": mid, "@Message.ExtendedInfo": [m]}}


def activate(st, kind):
    """What makes staged firmware the running version: Manager.Reset ('BMC'), a host restart or DC power cycle
    ('SYSTEM'), or a full AC power cycle ('AC', which also covers 'SYSTEM'), as in the BCM manual's DGX H100 example."""
    kinds = {"BMC": {"BMC"}, "SYSTEM": {"SYSTEM"}, "AC": {"AC", "SYSTEM"}}[kind]
    keep, done = [], []
    for act, cid, ver in st.pending_apply:
        if act in kinds:
            st.fw[cid]["version"] = ver
            done.append(cid)
        else:
            keep.append((act, cid, ver))
    st.pending_apply = keep
    for cid in done:
        sync_fw(st, cid)
    return done


def parse_multipart(content_type, body):
    """Return {part name: (headers, bytes)} using the standard library email parser."""
    raw = b"Content-Type: " + content_type.encode() + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
    msg = email.parser.BytesParser(policy=email.policy.HTTP).parsebytes(raw)
    out = {}
    for part in msg.iter_parts():
        name = part.get_param("name", header="content-disposition")
        out[name] = (part, part.get_payload(decode=True))
    return out
