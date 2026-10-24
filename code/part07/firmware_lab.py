#!/usr/bin/env python3
"""Self-checking lab for chapter 7.10: firmware inventory, drift, SimpleUpdate, multipart push, staging and activation.

Everything runs in-process against the teaching mock with a simulated clock. The 'firmware images' are small
invented packages (header line + payload + SHA-256) so each failure mode can be produced on purpose.
A pass means the mock and the tool follow the Redfish update flow. It says nothing about real firmware.
"""
import hashlib, http.server, json, sys, threading, uuid
from redfish_mock import make_server
from redfish_crawl import Client
from protocol_lab import call
import rf_firmware as fw

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def pkg(comp, ver, payload=b"x" * 1000, min_version=None, corrupt=False):
    h = {"component": comp, "version": ver, "sha256": hashlib.sha256(payload).hexdigest()}
    if min_version:
        h["min_version"] = min_version
    if corrupt:
        payload = payload[:-1] + b"?"
    return b"FWPKG1\n" + json.dumps(h).encode() + b"\n" + payload


def multipart(parts):
    b = uuid.uuid4().hex
    body = b""
    for name, fname, ctype, data in parts:
        disp = f'form-data; name="{name}"' + (f'; filename="{fname}"' if fname else "")
        body += f"--{b}\r\nContent-Disposition: {disp}\r\nContent-Type: {ctype}\r\n\r\n".encode() + data + b"\r\n"
    body += f"--{b}--\r\n".encode()
    return f"multipart/form-data; boundary={b}", body


def main():
    srv, st = make_server("dgx", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    clock = [1000.0]
    st.now = lambda: clock[0]
    sleep = lambda s: clock.__setitem__(0, clock[0] + s)
    files = {"bios128.fwpkg": pkg("BIOS", "1.28"), "bios120.fwpkg": pkg("BIOS", "1.20"), "bios110.fwpkg": pkg("BIOS", "1.10"),
             "bmc200.fwpkg": pkg("BMC", "2.00.0"), "cpld10.fwpkg": pkg("CPLD", "1.0"), "bad.fwpkg": pkg("BIOS", "1.30", corrupt=True),
             "junk.fwpkg": b"this is not a package", "lowmin.fwpkg": pkg("BIOS", "1.15", min_version="1.18")}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            n = self.path.lstrip("/")
            if n in files:
                self.send_response(200); self.send_header("Content-Length", str(len(files[n]))); self.end_headers(); self.wfile.write(files[n])
            else:
                self.send_response(404); self.end_headers()
        def log_message(self, *a):
            pass
    fs = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=fs.serve_forever, daemon=True).start()
    fu = f"http://127.0.0.1:{fs.server_address[1]}"

    c = Client(base, "admin", "adminpass")
    US = "/redfish/v1/UpdateService"
    SIMPLE = US + "/Actions/UpdateService.SimpleUpdate"
    SYSRESET = "/redfish/v1/Systems/System_0/Actions/ComputerSystem.Reset"
    ver = lambda cid: call(base, "GET", f"{US}/FirmwareInventory/{cid}")[2]["Version"]

    def run(body, auth=("admin", "adminpass")):
        s, h, b = call(base, "POST", SIMPLE, body, auth=auth)
        if s != 202:
            return s, None, None
        mon = h["Location"]
        for _ in range(60):
            s2, h2, b2 = call(base, "GET", mon)
            if s2 != 202:
                break
            clock[0] += 2
        msgs = call(base, "GET", f"/redfish/v1/TaskService/Tasks/{mon.rsplit('/', 1)[1]}")[2].get("Messages", [])
        return s2, b2, [m["MessageId"].rsplit(".", 1)[-1] for m in msgs]

    # --- inventory and drift
    items = fw.inventory(c)[1]
    check("inventory lists 34 components (BMC, BIOS, NIC, CPLD and the 30 GPU-tray components), all updateable, each with a version",
          len(items) == 34 and all(i["Updateable"] and i["Version"] for i in items), len(items))
    good = {"BIOS": "1.20", "BMC": "1.00.0", "NIC": "28.39.1002", "CPLD": "0.9"}
    good.update({i["Id"]: i["Version"] for i in items if i["Id"].startswith("HGX_FW_")})
    rows, bad = fw.drift(items, good)
    check("a matching baseline gives no drift", bad == 0, rows)
    mixed = dict(good, BIOS="1.28", HGX_FW_GPU_SXM_5="96.00.74.00.01", GHOST="1.0"); del mixed["NIC"]
    rows, bad = fw.drift(items, mixed)
    st_ = {k: s for k, _, _, s in rows}
    check("drift check reports DRIFT, MISSING and 'not in baseline' separately",
          st_.get("BIOS") == "DRIFT" and st_.get("HGX_FW_GPU_SXM_5") == "DRIFT" and st_.get("GHOST") == "MISSING" and st_.get("NIC_FW") == "not in baseline" and bad == 3, st_)

    # --- happy path: stage, then activate
    s, h, b = call(base, "POST", SIMPLE, {"ImageURI": fu + "/bios128.fwpkg", "TransferProtocol": "HTTP", "Targets": [f"{US}/FirmwareInventory/HostBIOS_0"]})
    check("SimpleUpdate answers 202 with a task monitor [12.6.2.1]", s == 202 and "TaskMonitors" in h.get("Location", ""), (s, h))
    inv = call(base, "GET", f"{US}/FirmwareInventory/HostBIOS_0")[2]
    check("while the update runs the component's State is Updating", inv["Status"]["State"] == "Updating", inv["Status"])
    mon = h["Location"]
    try:                                     # optional: validate the task and inventory against the official schemas
        import os, schema_tools
        if os.environ.get("REDFISH_PUBLICATIONS"):
            clock[0] += 14
            task = call(base, "GET", mon.replace("TaskMonitors", "Tasks"))[2]
            errs = schema_tools.validate_payload(task) or []
            errs += schema_tools.validate_payload(inv) or []
            check("the Task (with Messages) and the Updating SoftwareInventory validate against the official schemas", not errs, errs)
            clock[0] -= 14
    except ImportError:
        print("SKIP  schema validation needs jsonschema and referencing")
    seen = []
    for _ in range(40):
        s2, h2, b2 = call(base, "GET", mon)
        if s2 != 202:
            break
        seen = [m["MessageId"].rsplit(".", 1)[-1] for m in b2.get("Messages", [])]
        clock[0] += 2
    check("stages arrive in order: transferring, verifying, installing, awaiting activation",
          seen == ["TransferringToComponent", "VerifyingAtComponent", "InstallingOnComponent", "AwaitToActivate"], seen)
    msgs = [m["MessageId"].rsplit(".", 1)[-1] for m in call(base, "GET", mon.replace("TaskMonitors", "Tasks"))[2]["Messages"]]
    check("the finished task ends with AwaitToActivate", msgs[-1] == "AwaitToActivate" and s2 == 200, (msgs, s2))
    check("after the task the version is STILL the old one (staged, not active)", ver("HostBIOS_0") == "1.20", ver("HostBIOS_0"))
    check("the component is back to State Enabled", call(base, "GET", f"{US}/FirmwareInventory/HostBIOS_0")[2]["Status"]["State"] == "Enabled")
    call(base, "POST", SYSRESET, {"ResetType": "GracefulRestart"})
    check("a host reset activates it: the version is now 1.28", ver("HostBIOS_0") == "1.28", ver("HostBIOS_0"))

    # --- BMC firmware needs a Manager.Reset, not a host reset
    s, body, msgs = run({"ImageURI": fu + "/bmc200.fwpkg", "TransferProtocol": "HTTP"})
    call(base, "POST", SYSRESET, {"ResetType": "GracefulRestart"})
    check("BMC firmware is NOT activated by a host reset", ver("HostBMC_0") == "1.00.0", ver("HostBMC_0"))
    s, _, _ = call(base, "POST", "/redfish/v1/Managers/BMC_0/Actions/Manager.Reset", {"ResetType": "GracefulRestart"})
    check("a Manager.Reset (BMC restart) activates it", s == 200 and ver("HostBMC_0") == "2.00.0", ver("HostBMC_0"))
    s, body, msgs = run({"ImageURI": fu + "/cpld10.fwpkg", "TransferProtocol": "HTTP"})
    check("a component that needs no reset reports UpdateSuccessful and changes at once", msgs and msgs[-1] == "UpdateSuccessful" and ver("CPLD_0") == "1.0", (msgs, ver("CPLD_0")))

    # --- GPU tray package: one image updates 12 inventory entries and needs an AC power cycle
    files["gputray.fwpkg"] = pkg("GPUTRAY", "96.00.74.00.01")
    s, body, msgs = run({"ImageURI": fu + "/gputray.fwpkg", "TransferProtocol": "HTTP"})
    check("one GPU-tray package stages all 30 GPU-tray entries", msgs[-1] == "AwaitToActivate" and len(st.pending_apply) == 30, (msgs, len(st.pending_apply)))
    call(base, "POST", SYSRESET, {"ResetType": "GracefulRestart"})
    check("a normal host restart does NOT activate the GPU tray firmware", ver("HGX_FW_GPU_SXM_1") == "96.00.70.00.01", ver("HGX_FW_GPU_SXM_1"))
    call(base, "POST", SYSRESET, {"ResetType": "PowerCycle"})
    check("a board-level power cycle (PowerCycle) still does not activate it", ver("HGX_FW_GPU_SXM_1") == "96.00.70.00.01", ver("HGX_FW_GPU_SXM_1"))
    call(base, "POST", SYSRESET, {"ResetType": "FullPowerCycle"})
    check("a FullPowerCycle (AC power removed) activates all 30 entries", all(ver(f"HGX_FW_GPU_SXM_{i}") == "96.00.74.00.01" for i in range(1, 9)) and not st.pending_apply, ver("HGX_FW_GPU_SXM_1"))
    s, body, msgs = run({"ImageURI": fu + "/gputray.fwpkg", "TransferProtocol": "HTTP", "Targets": [f"{US}/FirmwareInventory/HGX_FW_GPU_SXM_3"]})
    check("a single member can be targeted (and the same version is then skipped)", msgs[-1] == "UpdateSkippedSameVersion", msgs)
    mixed_gpu = dict(zip(["HGX_FW_GPU_SXM_5"], ["96.00.70.00.01"]))
    files["gpuold.fwpkg"] = pkg("GPUTRAY", "96.00.74.00.01")

    # --- failure and skip cases
    s, body, msgs = run({"ImageURI": fu + "/bad.fwpkg", "TransferProtocol": "HTTP"})
    check("a corrupted image fails verification and nothing changes", s == 400 and msgs[-1] == "VerificationFailed" and ver("HostBIOS_0") == "1.28", (s, msgs))
    s, body, msgs = run({"ImageURI": fu + "/junk.fwpkg", "TransferProtocol": "HTTP"})
    check("a file that is not a package fails verification", s == 400 and msgs[-1] == "VerificationFailed", (s, msgs))
    s, body, msgs = run({"ImageURI": fu + "/missing.fwpkg", "TransferProtocol": "HTTP"})
    check("an unreachable image fails with TransferFailed (500)", s == 500 and msgs[-1] == "TransferFailed", (s, msgs))
    s, body, msgs = run({"ImageURI": fu + "/bios128.fwpkg", "TransferProtocol": "HTTP"})
    check("the same version is skipped, not reinstalled", s == 200 and msgs[-1] == "UpdateSkippedSameVersion", (s, msgs))
    s, body, msgs = run({"ImageURI": fu + "/bios110.fwpkg", "TransferProtocol": "HTTP"})
    check("a downgrade is skipped unless forced", s == 200 and msgs[-1] == "UpdateSkippedVersionTooLow" and ver("HostBIOS_0") == "1.28", (s, msgs))
    s, body, msgs = run({"ImageURI": fu + "/bios110.fwpkg", "TransferProtocol": "HTTP", "ForceUpdate": True})
    call(base, "POST", SYSRESET, {"ResetType": "GracefulRestart"})
    check("ForceUpdate allows the downgrade (after activation)", ver("HostBIOS_0") == "1.10", ver("HostBIOS_0"))
    s, body, msgs = run({"ImageURI": fu + "/lowmin.fwpkg", "TransferProtocol": "HTTP"})
    check("an image below its own minimum-version rule is skipped", msgs[-1] == "UpdateSkippedVersionTooLow", msgs)
    s, body, msgs = run({"ImageURI": fu + "/bios128.fwpkg", "TransferProtocol": "HTTP", "Targets": [f"{US}/FirmwareInventory/HostBMC_0"]})
    check("an image for BIOS aimed at the BMC is not applicable (400)", s == 400 and msgs[-1] == "UpdateNotApplicable" and ver("HostBMC_0") == "2.00.0", (s, msgs))
    s, h, b = call(base, "POST", SIMPLE, {"TransferProtocol": "HTTP"})
    check("missing ImageURI gives 400", s == 400, s)
    s, h, b = call(base, "POST", SIMPLE, {"ImageURI": fu + "/x", "TransferProtocol": "FTP"})
    check("a transfer protocol the service does not offer gives 400", s == 400, s)
    s, _, _ = call(base, "POST", SIMPLE, {"ImageURI": fu + "/bios128.fwpkg"}, auth=("viewer", "viewpass"))
    check("a ReadOnly user cannot start an update: 403", s == 403, s)

    # --- cancel
    s, h, b = call(base, "POST", SIMPLE, {"ImageURI": fu + "/bios128.fwpkg", "TransferProtocol": "HTTP"})
    clock[0] += 3
    s, _, _ = call(base, "DELETE", h["Location"])
    check("an update can be cancelled while running (204)", s == 204, s)
    call(base, "POST", SYSRESET, {"ResetType": "GracefulRestart"})
    check("a cancelled update never takes effect and the component is Enabled again",
          ver("HostBIOS_0") == "1.10" and call(base, "GET", f"{US}/FirmwareInventory/HostBIOS_0")[2]["Status"]["State"] == "Enabled", ver("HostBIOS_0"))

    # --- staged until StartUpdate
    s, h, b = call(base, "POST", SIMPLE, {"ImageURI": fu + "/bios128.fwpkg", "TransferProtocol": "HTTP", "@Redfish.OperationApplyTime": "OnStartUpdateRequest"})
    clock[0] += 60
    s2, _, b2 = call(base, "GET", h["Location"])
    check("with OnStartUpdateRequest the task waits in Pending, whatever the clock says", s2 == 202 and b2["TaskState"] == "Pending", (s2, b2.get("TaskState")))
    s, _, _ = call(base, "POST", US + "/Actions/UpdateService.StartUpdate", {})
    check("StartUpdate starts the waiting updates", s == 202, s)
    for _ in range(40):
        s2, _, b2 = call(base, "GET", h["Location"])
        if s2 != 202:
            break
        clock[0] += 2
    call(base, "POST", SYSRESET, {"ResetType": "GracefulRestart"})
    check("...and after activation the new version is in place", s2 == 200 and ver("HostBIOS_0") == "1.28", (s2, ver("HostBIOS_0")))

    # --- multipart push
    img = pkg("NIC", "28.41.1000")
    ctype, body = multipart([("UpdateParameters", None, "application/json", json.dumps({"Targets": [f"{US}/FirmwareInventory/NIC_FW"]}).encode()),
                             ("UpdateFile", "nic.fwpkg", "application/octet-stream", img)])
    import urllib.request
    def post_raw(ctype, body, auth="admin:adminpass"):
        import base64
        r = urllib.request.Request(base + US + "/upload", data=body, method="POST",
                                   headers={"Content-Type": ctype, "Authorization": "Basic " + base64.b64encode(auth.encode()).decode()})
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                return resp.status, dict(resp.headers), json.loads(resp.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), json.loads(e.read() or b"{}")
    import urllib.error
    s, h, b = post_raw(ctype, body)
    check("multipart push answers 202 with a task monitor [12.6.2.2]", s == 202 and "Location" in h, (s, b))
    for _ in range(40):
        s2, _, b2 = call(base, "GET", h["Location"])
        if s2 != 202:
            break
        clock[0] += 2
    call(base, "POST", SYSRESET, {"ResetType": "GracefulRestart"})
    check("the pushed NIC image becomes active after a reset", ver("NIC_FW") == "28.41.1000", ver("NIC_FW"))
    c2, b2_ = multipart([("UpdateFile", "nic.fwpkg", "application/octet-stream", img)])
    s, _, _ = post_raw(c2, b2_)
    check("multipart push without the UpdateParameters part gives 400", s == 400, s)
    st.max_image = 100
    s, _, _ = post_raw(ctype, body)
    check("an image bigger than MaxImageSizeBytes gives 413 [12.6.2.2]", s == 413, s)
    st.max_image = 64 * 1024 * 1024
    s, _, _ = post_raw("application/json", b"{}")
    check("a non-multipart body is refused", s in (400, 415), s)

    # --- the tool
    out = []
    a = dict(target="HostBIOS_0", image_uri=fu + "/bios120.fwpkg", yes=False)
    rc = fw.cmd_update(c, a, sleep, lambda: clock[0], out.append)
    check("the update tool is a dry run unless --yes is given (nothing sent, exit 0)", rc == 0 and any("DRY RUN" in x for x in out) and ver("HostBIOS_0") == "1.28", out[-1:])
    out.clear(); a.update(yes=True, image_uri=fu + "/bios110.fwpkg")
    rc = fw.cmd_update(c, a, sleep, lambda: clock[0], out.append)
    check("the tool reports a skipped downgrade as 'nothing changed'", rc == 0 and any("skipped" in x for x in out), out[-2:])
    out.clear(); a.update(image_uri=fu + "/bad.fwpkg")
    rc = fw.cmd_update(c, a, sleep, lambda: clock[0], out.append)
    check("the tool returns a non-zero code when verification fails", rc == 5, (rc, out[-2:]))
    out.clear(); a.update(image_uri=fu + "/bios128.fwpkg", force=True, activate=False)
    st.task_seconds = 5000
    rc = fw.cmd_update(c, dict(a, timeout=30), sleep, lambda: clock[0], out.append)
    check("a timeout is reported as unknown (exit 4), never as success", rc == 4 and any("TIMEOUT" in x for x in out), (rc, out[-1:]))
    st.task_seconds = 20

    files["gputray2.fwpkg"] = pkg("GPUTRAY", "96.00.80.00.01")
    out.clear()
    a = dict(target="HGX_FW_GPU_SXM_1", image_uri=fu + "/gputray2.fwpkg", yes=True, activate=True, timeout=600)
    rc = fw.cmd_update(c, a, sleep, lambda: clock[0], out.append)
    check("tool: a normal restart leaves the GPU firmware NOT active and the tool says so (exit 7)", rc == 7 and any("NOT ACTIVE" in x for x in out), (rc, out[-2:]))
    out.clear()
    a = dict(target="HGX_FW_GPU_SXM_1", image_uri=fu + "/gputray2.fwpkg", yes=True, activate=True, reset_type="FullPowerCycle", force=True, timeout=600)
    rc = fw.cmd_update(c, a, sleep, lambda: clock[0], out.append)
    check("tool: with --reset-type FullPowerCycle the update becomes active (exit 0)", rc == 0 and ver("HGX_FW_GPU_SXM_1") == "96.00.80.00.01", (rc, out[-3:]))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
