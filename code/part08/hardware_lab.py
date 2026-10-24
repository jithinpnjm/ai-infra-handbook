#!/usr/bin/env python3
"""Self-checking lab for chapter 8.7: power, BMC, BIOS, firmware and SOL rules from the BCM 11 manual, tested in bcm_hardware.py."""
import os, stat, sys, tempfile
import bcm_hardware as h

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except h.HwError:
        return True

def main():
    # power method
    check("powercontrol apc uses the PDU ports", h.power_method("apc", ["apc01:6", "apc01:7"])["method"] == "pdu")
    r = h.power_method("ipmi0", ["apc01:6"])
    check("with ipmi0 configured PDU ports are ignored by default", r["method"] == "IPMI" and r["pdu_ports_used_for"] == "ignored")
    r = h.power_method("ipmi0", ["apc01:6"], power_off_pdu_outlet=True)
    check("PowerOffPDUOutlet=true also switches the PDU outlet off after the node is off", "outlet off" in r["pdu_ports_used_for"])
    check("ilo0, drac0, cimc0 and rf0 are accepted as BMC interface names", [h.power_method(x)["method"] for x in ("ilo0", "drac0", "cimc0", "rf0")] == ["iLO", "DRAC", "CIMC", "Redfish"])
    check("a BMC with a DHCP address is not power-managed by BCM", h.power_method("ipmi0", bmc_ip_mode="dhcp")["method"] == "none by BCM")
    check("a non-manageable PDU leaves the BMC state unknown (the manual's warning)", "unknown" in h.power_method("apc", ["dumb:1"], pdu_manageable=False)["note"])
    check("an invalid power control value is refused", raises(lambda: h.power_method("wol")))
    check("twin nodes on one PDU port are all affected by a power operation", h.shared_port_targets("pdu1:3", {"pdu1:3": ["node002", "node001"]}) == ["node001", "node002"])
    check("the five power status values", set(h.POWER_STATUS) == {"ON", "OFF", "RESET", "FAILED", "UNKNOWN"})

    # schedule
    nodes = [f"node{i:03d}" for i in range(1, 34)]
    s = h.power_schedule(nodes)
    check("default delay: 1 second between devices (33 nodes: the last starts at 32 s)", s[-1][0] == 32.0)
    check("-d 0.01 shortens it", h.power_schedule(nodes, delay=0.01)[-1][0] == 0.32)
    racks = [f"rack{i:02d}" for i in range(1, 13)]
    b = h.power_schedule(racks, parallel=3)
    check("power on -p 3 rack[01-12]: 4 batches, 20 s apart (starts at 0, 20, 40, 60)", sorted({t for t, _ in b}) == [0.0, 20.0, 40.0, 60.0])
    check("racks within a batch start together (delay 0)", [t for t, n in b if n in ("rack01", "rack02", "rack03")] == [0.0, 0.0, 0.0])
    check("power commands are blocked inside foreach/range", h.power_blocked_in_loop("power status") and not h.power_blocked_in_loop("get ip"))
    check("a closed device is skipped unless -f", not h.allowed_on_closed(False) and h.allowed_on_closed(True))

    # custom script contract
    d = tempfile.mkdtemp()
    script = os.path.join(d, "custompower")
    open(script, "w").write('#!/bin/bash\ncase "$1" in\n ON) echo "wake $CMD_MAC $2 arg=$3"; exit 0;;\n STATUS) echo ON; exit 0;;\n OFF|RESET) exit 3;;\nesac\nexit 1\n')
    os.chmod(script, os.stat(script).st_mode | stat.S_IXUSR)
    ok, out = h.run_custom_power(script, "ON", "node001", "42", env_mac="00:11:22:33:44:55")
    check("a custom power script gets <operation> <device> as $1 $2, an optional $3, and CMD_MAC", ok and out == "wake 00:11:22:33:44:55 node001 arg=42", out)
    check("exit code 0 means success, non-zero failure", h.run_custom_power(script, "STATUS", "node001")[0] and not h.run_custom_power(script, "OFF", "node001")[0])
    check("operations other than ON OFF RESET STATUS are refused", raises(lambda: h.run_custom_power(script, "SLEEP", "node001")))

    # BMC network and settings
    ips = h.addinterface_ips("10.148.0.1", 150)
    check("addinterface for 150 nodes from 10.148.0.1 ends at 10.148.0.150", ips[0] == "10.148.0.1" and ips[-1] == "10.148.0.150")
    check("--increment 2 steps by two", h.addinterface_ips("10.148.0.1", 3, 2) == ["10.148.0.1", "10.148.0.3", "10.148.0.5"])
    check("addresses outside the BMC network are refused", raises(lambda: h.addinterface_ips("10.148.255.250", 20)))
    part = {"user": "bright", "password": "p1"}
    cat = {"user": "root", "password": "p2"}
    check("BMC settings: partition applies when nothing is below", h.effective_bmc(None, None, part) == (part, "partition"))
    check("category overrides partition, node overrides category", h.effective_bmc(None, cat, part)[1] == "category" and h.effective_bmc({"user": "x"}, cat, part)[1] == "device")
    check("nothing defined anywhere: not set", h.effective_bmc(None, None, None) == (None, "not set"))
    devs = {"node001": {"category": "default"}, "node002": {"category": "default"}, "node003": {"category": "default", "bmc": {"user": "root", "password": "other"}},
            "node004": {"category": "none"}}
    cats = {"default": cat}
    rows = h.credentials_overview(devs, cats, None, "salt1")
    check("credentialsoverview: equal passwords give equal fingerprints within a session, an odd one stands out", rows["node001"][1] == rows["node002"][1] != rows["node003"][1])
    check("a different session salt gives different fingerprints for the same password", h.credentials_overview(devs, cats, None, "salt2")["node001"][1] != rows["node001"][1])
    check("a device with nothing set shows <not set>", rows["node004"][1] == "<not set>")
    inv = h.credentials_overview(devs, cats, None, "salt1", inverse=True)
    check("--inverse sorts by count ascending so outliers come first", inv[0][0] == 1 and inv[-1][0] == 2 and inv[-1][2] == ["node001", "node002"], inv)

    # BIOS
    b = h.BiosSettings({"Boot Mode": "UEFI Mode"})
    check("BIOS: a model must be set first", raises(lambda: b.set("Boot Mode", "Legacy BIOS Mode")))
    b.set_model("hpe_dl380")
    b.set("Boot Mode", "Legacy BIOS Mode")
    check("after commit: configured changed, pending and live unchanged", b.status("Boot Mode") == ("Legacy BIOS Mode", "-", "UEFI Mode"))
    b.apply()
    check("after `bios apply`: pending holds the new value, live still the old", b.status("Boot Mode") == ("Legacy BIOS Mode", "Legacy BIOS Mode", "UEFI Mode"))
    b.reboot()
    check("after a reboot the value is live", b.status("Boot Mode")[2] == "Legacy BIOS Mode")
    b2 = h.BiosSettings({"Boot Mode": "UEFI Mode"}); b2.set_model("x")
    check("a <default> configured value changes nothing on apply and reboot", (b2.apply(), b2.reboot(), b2.status("Boot Mode"))[2] == ("<default>", "-", "UEFI Mode"))
    check("an unknown BIOS parameter is refused", raises(lambda: b2.set("Nope", "1")))

    # firmware
    check("firmwaremanagemode accepts auto, h100, gb200, iLO, none and refuses others", all(h.firmware_mode_check(m) for m in ("auto", "h100", "gb200", "iLO", "none")) and raises(lambda: h.firmware_mode_check("dgx")))
    c = h.FirmwareComponent("HGX_FW_GPU_SXM_1", "96.00.70.00.01")
    c.flash("96.00.74.00.01")
    check("flashing shows progress", c.state == "flashing" and c.progress == 0.0)
    c.finish_flash()
    check("after flashing the state is pending with the AC power cycle hint", c.state == "pending" and c.result == "success: AC power cycle to activate")
    c.power_cycle("dc")
    check("a DC power cycle (plain power reset) does NOT activate it", c.state == "pending" and c.version == "96.00.70.00.01")
    c.power_cycle("ac")
    check("an AC power cycle activates it: success: activated, new version", c.state == "current" and c.result == "success: activated" and c.version == "96.00.74.00.01")
    check("firmware packages are looked for in /cm/local/apps/cmd/etc/htdocs/bios/firmware/", h.FWPKG_DIR.endswith("htdocs/bios/firmware/"))

    # SOL
    good = {"speed": 115200, "flow": "on", "port": "ttyS0"}
    check("SOL: all three layers agreeing on 115200, flow on, ttyS0 is clean", h.sol_problems(good, good, good) == [])
    p = h.sol_problems(good, dict(good, speed=57600), good)
    check("SOL: a speed mismatch between kernel and BIOS is reported", any("speed" in x for x in p))
    check("SOL: ttyAMA0 is the expected port on aarch64, not ttyS0", any("ttyAMA0" in x for x in h.sol_problems(good, good, good, arch="aarch64")))
    check("SOL: a speed above 115200 gets the manual's warning", any("115200" in x for x in h.sol_problems(dict(good, speed=230400), dict(good, speed=230400), dict(good, speed=230400))))
    check("SOL: shared NIC with a client on the dedicated port shows no console", any("shared NIC" in x for x in h.sol_problems(good, good, good, bmc_lan_shared_nic=True, client_on_dedicated_port=True)))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
