#!/usr/bin/env python3
"""Self-checking lab for chapter 7.14: BIOS settings through the Settings resource, one-time boot, and a node
bring-up that stops on the first problem and can be re-run. In-process mock, no real hardware."""
import json, os, sys, tempfile, threading
from redfish_mock import make_server
from redfish_crawl import Client
from protocol_lab import call
import node_lifecycle, rf_bios

ok_count = fail_count = 0


def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))


def serve():
    srv, st = make_server("dgx", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return st, f"http://127.0.0.1:{srv.server_address[1]}"


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(here, "profiles", "ai_node_bios.json")
    st, base = serve()
    B = "/redfish/v1/Systems/System_0/Bios"
    RESET = "/redfish/v1/Systems/System_0/Actions/ComputerSystem.Reset"

    s, h, b = call(base, "GET", B)
    check("Bios shows live attributes and points to a Settings object and an attribute registry",
          s == 200 and b["AttributeRegistry"] and b["@Redfish.Settings"]["SettingsObject"]["@odata.id"] == B + "/Settings", b.get("@Redfish.Settings"))
    reg = call(base, "GET", "/redfish/v1/Registries")[2]["Members"][0]["@odata.id"]
    s, h, rf = call(base, "GET", reg)
    s, h, r = call(base, "GET", rf["Location"][0]["Uri"])
    names = {e["AttributeName"] for e in r["RegistryEntries"]["Attributes"]}
    check("the attribute registry lists every attribute with its allowed values", "PcieLinkSpeed" in names and len(names) >= 10, len(names))

    s, h, b = call(base, "PATCH", B + "/Settings", {"Attributes": {"PowerProfile": "MaxPerf"}})
    check("PATCH to Settings is accepted and the answer says a reset is required (Base ResetRequired)",
          s == 200 and "ResetRequired" in b["@Message.ExtendedInfo"][0]["MessageId"], (s, b.get("@Message.ExtendedInfo")))
    live = call(base, "GET", B)[2]["Attributes"]["PowerProfile"]
    pend = call(base, "GET", B + "/Settings")[2]["Attributes"]
    check("the LIVE value is unchanged and the PENDING value holds the change", live == "Balanced" and pend == {"PowerProfile": "MaxPerf"}, (live, pend))
    call(base, "POST", RESET, {"ResetType": "GracefulRestart"})
    check("after a host restart the pending value is live and the pending object is empty",
          call(base, "GET", B)[2]["Attributes"]["PowerProfile"] == "MaxPerf" and call(base, "GET", B + "/Settings")[2]["Attributes"] == {})
    s, _, b = call(base, "PATCH", B + "/Settings", {"Attributes": {"PowerProfile": "Turbo"}})
    check("a value outside the registry's list is refused (400 PropertyValueNotInList)", s == 400 and "PropertyValueNotInList" in json.dumps(b), s)
    s, _, b = call(base, "PATCH", B + "/Settings", {"Attributes": {"NoSuchSetting": 1}})
    check("an unknown attribute is refused (400 PropertyUnknown)", s == 400 and "PropertyUnknown" in json.dumps(b), s)
    s, _, b = call(base, "PATCH", B + "/Settings", {"Attributes": {"BiosVersionString": "9.9"}})
    check("a read-only attribute is refused (400 PropertyNotWritable)", s == 400 and "PropertyNotWritable" in json.dumps(b), s)
    s, _, b = call(base, "PATCH", B + "/Settings", {"Attributes": {"ProcCoreDisable": 500}})
    check("an integer outside its range is refused", s == 400, s)
    s, _, b = call(base, "PATCH", B + "/Settings", {"Attributes": {"ProcCoreDisable": "four"}})
    check("a wrong type is refused", s == 400, s)
    s, _, _ = call(base, "PATCH", B + "/Settings", {"Attributes": {"PowerProfile": "Balanced"}}, auth=("viewer", "viewpass"))
    check("a ReadOnly user cannot stage BIOS changes: 403", s == 403, s)
    s, _, _ = call(base, "POST", B + "/Actions/Bios.ResetBios", {})
    call(base, "POST", RESET, {"ResetType": "ForceRestart"})
    check("Bios.ResetBios then a restart returns the factory defaults", call(base, "GET", B)[2]["Attributes"]["PowerProfile"] == "Balanced")

    # one-time boot
    S = "/redfish/v1/Systems/System_0"
    call(base, "PATCH", S, {"Boot": {"BootSourceOverrideEnabled": "Once", "BootSourceOverrideTarget": "Pxe"}})
    call(base, "POST", RESET, {"ResetType": "GracefulRestart"})
    boot = call(base, "GET", S)[2]["Boot"]
    check("a 'Once' boot override is used by the next restart and then switches itself off", st.bios["boot_log"][-1] == "Pxe" and boot["BootSourceOverrideEnabled"] == "Disabled", (st.bios["boot_log"], boot))
    call(base, "POST", RESET, {"ResetType": "GracefulRestart"})
    check("the restart after that boots normally (no repeated PXE)", st.bios["boot_log"][-1] == "Hdd", st.bios["boot_log"])
    call(base, "PATCH", S, {"Boot": {"BootSourceOverrideEnabled": "Continuous", "BootSourceOverrideTarget": "Pxe"}})
    call(base, "POST", RESET, {"ResetType": "GracefulRestart"}); call(base, "POST", RESET, {"ResetType": "GracefulRestart"})
    check("a 'Continuous' override keeps booting from the network on every restart (a classic provisioning trap)",
          st.bios["boot_log"][-2:] == ["Pxe", "Pxe"] and call(base, "GET", S)[2]["Boot"]["BootSourceOverrideEnabled"] == "Continuous", st.bios["boot_log"])
    call(base, "PATCH", S, {"Boot": {"BootSourceOverrideEnabled": "Disabled", "BootSourceOverrideTarget": "None"}})

    # the tool and the lifecycle
    st2, base2 = serve()
    c = Client(base2, "admin", "adminpass")
    tmp = tempfile.mkdtemp(); sp = os.path.join(tmp, "node1.json")
    base_fw = {i["Id"]: i["Version"] for i in call(base2, "GET", "/redfish/v1/UpdateService/FirmwareInventory?$expand=.($levels=1)")[2]["Members"]}
    fwp = os.path.join(tmp, "baseline.json"); json.dump(base_fw, open(fwp, "w"))
    out = []
    state, ok = node_lifecycle.run(c, sp, target, fwp, yes=False, out=out.append)
    check("dry run: stops at the first step that would change something, changes nothing",
          not ok and any("dry-run" in l for l in out) and call(base2, "GET", "/redfish/v1/Systems/System_0/Bios/Settings")[2]["Attributes"] == {}, out[-2:])
    out.clear()
    state, ok = node_lifecycle.run(c, sp, target, fwp, yes=True, reset_ok=False, out=out.append)
    check("with --yes but no permission to restart, it stages and stops at 'pending'", not ok and state["steps"]["bios"]["status"] == "pending", out[-2:])
    out.clear()
    state, ok = node_lifecycle.run(c, sp, target, fwp, yes=True, reset_ok=True, out=out.append)
    check("with --reset-ok it finishes: BIOS live, boot override consumed, node ready",
          ok and state["steps"]["bios"]["status"] == "done" and state["steps"]["boot"]["status"] == "done" and state["steps"]["ready"]["status"] == "done", out)
    out.clear()
    state, ok = node_lifecycle.run(c, sp, target, fwp, yes=True, reset_ok=True, out=out.append)
    check("running it again is harmless: BIOS already matches, nothing is restarted again", ok and any("already matches" in l for l in out) and any("skipped" in l for l in out), out)
    check("the state file keeps the evidence (inventory snapshot) and each step's result", json.load(open(sp))["evidence"]["inventory"] and len(json.load(open(sp))["steps"]) == 6)

    # failures stop the run
    st3, base3 = serve(); c3 = Client(base3, "admin", "adminpass")
    st3.tree["/redfish/v1/Chassis/Chassis_0/PCIeDevices/GPU_3"]["PCIeInterface"].update(PCIeType="Gen3", LanesInUse=8)
    out.clear(); sp3 = os.path.join(tmp, "node3.json")
    state, ok = node_lifecycle.run(c3, sp3, target, fwp, yes=True, reset_ok=True, out=out.append)
    check("a degraded GPU link stops the run at 'health' and nothing after it is attempted",
          not ok and state["steps"]["health"]["status"] == "failed" and "bios" not in state["steps"] and "GPU_3" in state["steps"]["health"]["detail"], out)
    st3.tree["/redfish/v1/Chassis/Chassis_0/PCIeDevices/GPU_3"]["PCIeInterface"].update(PCIeType="Gen5", LanesInUse=16)
    out.clear()
    state, ok = node_lifecycle.run(c3, sp3, target, fwp, yes=True, reset_ok=True, out=out.append)
    check("after the fault is fixed the same command continues and completes", ok, out)
    st4, base4 = serve(); c4 = Client(base4, "admin", "adminpass")
    st4.fw["HostBIOS_0"]["version"] = "1.05"
    import mock_update; mock_update.sync_fw(st4, "HostBIOS_0")
    out.clear()
    state, ok = node_lifecycle.run(c4, os.path.join(tmp, "n4.json"), target, fwp, yes=True, reset_ok=True, out=out.append)
    check("firmware drift stops the run at 'firmware' (updates are a separate, reviewed job)", not ok and state["steps"]["firmware"]["status"] == "failed" and "HostBIOS_0" in state["steps"]["firmware"]["detail"], out)
    bad_target = os.path.join(tmp, "bad.json"); json.dump({"PowerProfile": "Turbo", "Ghost": 1}, open(bad_target, "w"))
    st5, base5 = serve(); c5 = Client(base5, "admin", "adminpass")
    out.clear()
    state, ok = node_lifecycle.run(c5, os.path.join(tmp, "n5.json"), bad_target, fwp, yes=True, reset_ok=True, out=out.append)
    check("a BIOS target with an invalid value or an unknown attribute is refused before anything is sent", not ok and state["steps"]["bios"]["status"] == "failed" and call(base5, "GET", "/redfish/v1/Systems/System_0/Bios/Settings")[2]["Attributes"] == {}, out)

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0


if __name__ == "__main__":
    sys.exit(main())
