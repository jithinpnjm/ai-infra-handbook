#!/usr/bin/env python3
"""Bring one new GPU node from 'racked' to 'ready', step by step, with evidence, and safe to re-run.

  node_lifecycle.py http://bmc user pw --state state.json --bios profiles/ai_node_bios.json
                    --firmware baseline.json [--yes] [--reset-ok]

Steps (each checks first and skips what is already right, so running it twice is harmless):
  1 inventory   record what the BMC reports (evidence)
  2 health      no sensor flagged, no degraded PCIe/port/drive (reuses rf_sensors and rf_hardware)
  3 firmware    versions match the baseline (drift stops the run: updating is a separate, reviewed job, chapter 7.10)
  4 bios        stage the target BIOS settings; with --reset-ok restart the host and check they are live
  5 boot        set a ONE-TIME network boot override; with --reset-ok restart and check it was consumed
  6 ready       write the record
Anything that changes the node needs --yes. The state file keeps the result of every step and the evidence, so a
failed run can be fixed and continued. The run STOPS at the first failure.
"""
import json, os, sys, time
from redfish_crawl import Client
import rf_inventory, rf_sensors, rf_hardware, rf_firmware, rf_bios
from rf_inventory import get


class Step:
    name = "?"
    def run(self, ctx):
        raise NotImplementedError


def load_state(path):
    return json.load(open(path)) if path and os.path.exists(path) else {"steps": {}, "evidence": {}}


def save_state(path, st):
    if path:
        json.dump(st, open(path, "w"), indent=2)


def step_inventory(ctx):
    rows = rf_inventory.inventory(ctx["c"])
    ctx["state"]["evidence"]["inventory"] = rows
    return "done", f"{len(rows)} system(s), BMC firmware {rows[0].get('bmc_fw') if rows else '?'}"


def step_health(ctx):
    c = ctx["c"]
    problems = []
    for ch, used, rows in rf_sensors.collect(c):
        problems += [f"sensor {r['name']}: {'; '.join(r['flags'])}" for r in rows if r["flags"]]
    an = rf_hardware.analyse(rf_hardware.walk(c))
    for grp in ("pcie", "port", "drive", "volume"):
        problems += [f"{grp} {name.rsplit('/', 1)[-1]}: {'; '.join(f)}" for name, _, _, f in an[grp] if f]
    ctx["state"]["evidence"]["health_problems"] = problems
    if problems:
        return "failed", f"{len(problems)} problem(s): " + " | ".join(problems[:3])
    return "done", "no flagged sensors, links or drives"


def step_firmware(ctx):
    if not ctx.get("firmware"):
        return "skipped", "no firmware baseline given"
    us, items = rf_firmware.inventory(ctx["c"])
    rows, bad = rf_firmware.drift(items, json.load(open(ctx["firmware"])))
    ctx["state"]["evidence"]["firmware_drift"] = [r for r in rows if r[3] != "ok"]
    if bad:
        worst = [f"{k}: have {h}, want {w}" for k, w, h, s in rows if s in ("DRIFT", "MISSING")]
        return "failed", f"{bad} component(s) differ from the baseline (update them with the firmware procedure first): " + "; ".join(worst[:3])
    return "done", "all baseline components match"


def step_bios(ctx):
    c = ctx["c"]
    s = rf_bios.find_system(c)
    bios = get(c, s["Bios"]["@odata.id"])
    reg = rf_bios.load_registry(c, bios)
    rows = rf_bios.plan(bios["Attributes"], json.load(open(ctx["bios"])), reg)
    bad = [r for r in rows if r[3] in ("UNKNOWN", "READONLY", "INVALID")]
    if bad:
        return "failed", "the target has attributes this BIOS does not accept: " + ", ".join(f"{r[0]} ({r[3]})" for r in bad)
    changes = {r[0]: r[2] for r in rows if r[3] == "CHANGE"}
    if not changes:
        return "done", "BIOS already matches the target"
    if not ctx["yes"]:
        return "dry-run", f"would stage {len(changes)} BIOS change(s): {json.dumps(changes)}"
    settings = bios["@Redfish.Settings"]["SettingsObject"]["@odata.id"]
    st, _, resp = ctx["c"].req("PATCH", settings, {"Attributes": changes})
    if st != 200:
        return "failed", f"BIOS settings refused: HTTP {st}"
    if not ctx["reset_ok"]:
        return "pending", "BIOS settings staged; they need a host restart (run again with --reset-ok on a drained node)"
    st, _, _ = ctx["c"].req("POST", s["Actions"]["#ComputerSystem.Reset"]["target"], {"ResetType": "GracefulRestart"})
    live = get(c, bios["@odata.id"])["Attributes"]
    wrong = {k: live.get(k) for k, v in changes.items() if live.get(k) != v}
    return ("done", "BIOS settings are live") if not wrong else ("failed", f"settings not live after restart: {wrong}")


def step_boot(ctx):
    c = ctx["c"]
    s = rf_bios.find_system(c)
    boot = s.get("Boot") or {}
    if boot.get("BootSourceOverrideEnabled") == "Disabled" and ctx["state"]["steps"].get("boot", {}).get("status") == "done":
        return "done", "already provisioned"
    if not ctx["yes"]:
        return "dry-run", "would set a one-time Pxe boot override"
    st, _, resp = c.req("PATCH", s["@odata.id"], {"Boot": {"BootSourceOverrideEnabled": "Once", "BootSourceOverrideTarget": "Pxe", "BootSourceOverrideMode": "UEFI"}})
    if st != 200:
        return "failed", f"boot override refused: HTTP {st}"
    if not ctx["reset_ok"]:
        return "pending", "one-time Pxe override set; it is consumed at the next restart (--reset-ok)"
    c.req("POST", s["Actions"]["#ComputerSystem.Reset"]["target"], {"ResetType": "GracefulRestart"})
    after = get(c, s["@odata.id"])["Boot"]
    return ("done", "override consumed: the node booted from the network once") if after.get("BootSourceOverrideEnabled") == "Disabled" else ("failed", f"override still set: {after}")


def step_ready(ctx):
    done = [k for k, v in ctx["state"]["steps"].items() if v["status"] == "done"]
    return "done", f"{len(done)} step(s) done before this one; node record written"


STEPS = [("inventory", step_inventory), ("health", step_health), ("firmware", step_firmware), ("bios", step_bios),
         ("boot", step_boot), ("ready", step_ready)]


def run(c, state_path=None, bios=None, firmware=None, yes=False, reset_ok=False, out=print):
    state = load_state(state_path)
    ctx = dict(c=c, state=state, bios=bios, firmware=firmware, yes=yes, reset_ok=reset_ok)
    for name, fn in STEPS:
        prior = state["steps"].get(name, {}).get("status")
        if name == "bios" and not bios:
            state["steps"][name] = dict(status="skipped", detail="no BIOS target given"); continue
        if name == "boot" and prior == "done":
            out(f"[{name:9}] done earlier, skipped"); continue
        status, detail = fn(ctx)
        state["steps"][name] = dict(status=status, detail=detail, at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        out(f"[{name:9}] {status:8} {detail}")
        save_state(state_path, state)
        if status in ("failed", "pending", "dry-run"):
            out(f"STOPPED at '{name}'. Fix the cause and run again: finished steps are re-checked and skipped.")
            return state, False
    save_state(state_path, state)
    return state, True


if __name__ == "__main__":
    base, user, pw = sys.argv[1:4]
    a = sys.argv[4:]
    val = lambda n, d=None: a[a.index(n) + 1] if n in a else d
    c = Client(base, user, pw)
    try:
        _, ok = run(c, val("--state"), val("--bios"), val("--firmware"), "--yes" in a, "--reset-ok" in a)
    finally:
        c.logout()
    sys.exit(0 if ok else 1)
