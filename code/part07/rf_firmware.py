#!/usr/bin/env python3
"""Firmware inventory, drift check and a careful update through Redfish.

  rf_firmware.py inventory http://host:port user pw [--csv]
  rf_firmware.py drift     http://host:port user pw --baseline baseline.json
  rf_firmware.py update    http://host:port user pw --target HostBIOS_0 --image-uri http://files/bios.fwpkg
                           [--force] [--activate] [--reset-type FullPowerCycle] [--yes] [--timeout 900]

baseline.json maps a component (its SoftwareId or Id) to the version you expect, e.g. {"BIOS": "1.28"}.
'update' prints its plan and sends NOTHING unless --yes is given. With --activate it also resets the BMC or
the host when the update needs that, so drain the node first. Teaching tool for the mock: real firmware
(especially GPU, NVSwitch and NIC firmware) has vendor rules this does not know. Follow the vendor procedure.
"""
import json, sys, time
from redfish_crawl import Client
from rf_inventory import get, collection


def inventory(c):
    root = get(c, "/redfish/v1/")
    us = get(c, root["UpdateService"]["@odata.id"])
    items = collection(c, us["FirmwareInventory"]["@odata.id"]) if "FirmwareInventory" in us else []
    return us, items


def drift(items, baseline):
    """Return (rows, problems). Baseline keys match SoftwareId first, then Id."""
    by_key = {}
    for it in items:
        by_key[it.get("SoftwareId") or it["Id"]] = it
        by_key.setdefault(it["Id"], it)
    rows, bad = [], 0
    for key, want in baseline.items():
        it = by_key.get(key)
        if not it:
            rows.append((key, want, None, "MISSING")); bad += 1
        elif it.get("Version") == want:
            rows.append((key, want, it.get("Version"), "ok"))
        else:
            rows.append((key, want, it.get("Version"), "DRIFT")); bad += 1
    known = set(baseline)
    for it in items:
        if (it.get("SoftwareId") or it["Id"]) not in known and it["Id"] not in known:
            rows.append((it["Id"], None, it.get("Version"), "not in baseline"))
    return rows, bad


def find_reset(c, root, kind, item, want=None):
    """Discover the reset action for an inventory item from its RelatedItem link (Manager.Reset or ComputerSystem.Reset).
    'want' asks for a specific ResetType (for example FullPowerCycle); it must be in the action's allowable values."""
    for rel in item.get("RelatedItem", []) or []:
        r = get(c, rel["@odata.id"])
        if not r:
            continue
        for name, act in (r.get("Actions") or {}).items():
            if name in ("#Manager.Reset", "#ComputerSystem.Reset"):
                allowed = act.get("ResetType@Redfish.AllowableValues") or []
                choice = want if want in allowed else ("GracefulRestart" if "GracefulRestart" in allowed else (allowed[0] if allowed else None))
                if want and want not in allowed:
                    return rel["@odata.id"], act["target"], None
                return rel["@odata.id"], act["target"], choice
    return None, None, None


def wait_task(c, monitor, timeout, sleep=time.sleep, now=time.time, out=print):
    """Poll a task monitor until it ends. Returns (final status, body, messages). A timeout is 'unknown', not success."""
    start, seen = now(), 0
    last_msgs = []
    while True:
        st, hd, body = c.req("GET", monitor)
        if st == 202:
            msgs = (body or {}).get("Messages", [])
            for m in msgs[seen:]:
                out(f"    [{(body or {}).get('PercentComplete', '?')}%] {m.get('Message')}")
            seen = len(msgs); last_msgs = msgs
            if now() - start > timeout:
                return "TIMEOUT", body, last_msgs
            try:
                wait = max(1, int(hd.get("Retry-After", 2)))
            except (TypeError, ValueError):
                wait = 2
            sleep(wait)
            continue
        return st, body, last_msgs


def cmd_update(c, a, sleep=time.sleep, now=time.time, out=print):
    us, items = inventory(c)
    by_id = {i["Id"]: i for i in items}
    t = by_id.get(a["target"])
    if not t:
        out(f"unknown target {a['target']}. Known: {', '.join(by_id)}"); return 2
    if not t.get("Updateable", False):
        out(f"{a['target']} is not marked Updateable"); return 2
    action = (us.get("Actions") or {}).get("#UpdateService.SimpleUpdate")
    if not action:
        out("this service offers no SimpleUpdate action"); return 2
    body = {"ImageURI": a["image_uri"], "TransferProtocol": a.get("protocol", "HTTP"), "Targets": [t["@odata.id"]]}
    if a.get("force"):
        body["ForceUpdate"] = True
    out(f"PLAN  component {t['Id']} ({t.get('Name')}) is at version {t.get('Version')}")
    out(f"      POST {action['target']}")
    out(f"      body {json.dumps(body)}")
    if not a.get("yes"):
        out("DRY RUN: nothing sent. Drain the node, then add --yes."); return 0
    if t.get("Status", {}).get("State") == "Updating":
        out("refusing: this component is already Updating"); return 3
    st, hd, resp = c.req("POST", action["target"], body)
    if st != 202:
        out(f"update request refused: HTTP {st} {json.dumps(resp)[:300]}"); return 3
    out(f"accepted, following {hd['Location']}")
    final, fbody, msgs = wait_task(c, hd["Location"], a.get("timeout", 900), sleep, now, out)
    if final == "TIMEOUT":
        out("TIMEOUT: result unknown. Check the task and the inventory by hand before doing anything else."); return 4
    mid = ((fbody or {}).get("error", {}).get("@Message.ExtendedInfo") or [{}])[0].get("MessageId", "")
    out(f"task finished: HTTP {final} {mid}")
    if final != 200:
        return 5
    if mid.endswith("UpdateSkippedSameVersion") or mid.endswith("UpdateSkippedVersionTooLow"):
        out("nothing was changed (skipped)"); return 0
    if mid.endswith("AwaitToActivate"):
        if not a.get("activate"):
            out("STAGED: the new version becomes active after a reset. Re-run with --activate or reset it yourself."); return 0
        root = get(c, "/redfish/v1/")
        rel, target, choice = find_reset(c, root, "reset", t, a.get("reset_type"))
        if not target or not choice:
            out(f"cannot find a reset action{' with ResetType ' + a['reset_type'] if a.get('reset_type') else ''} for this component"); return 6
        out(f"activating: POST {target} ResetType={choice}")
        st, _, _ = c.req("POST", target, {"ResetType": choice})
        if st not in (200, 202, 204):
            out(f"reset refused: HTTP {st}"); return 6
    now_item = get(c, t["@odata.id"])
    out(f"inventory now says {t['Id']} = {now_item.get('Version')}")
    if now_item.get("Version") in (None, t.get("Version")):
        out("NOT ACTIVE: the version did not change. This component may need a stronger reset (for example a full AC power cycle, "
            "as the BCM manual describes for the DGX H100 GPU tray). Check the vendor's activation table.")
        return 7
    return 0


def main(argv):
    cmd, base, user, pw = argv[1:5]
    flags = argv[5:]
    c = Client(base, user, pw)
    try:
        if cmd == "inventory":
            us, items = inventory(c)
            for i in items:
                print(f"{i['Id']:24} {str(i.get('SoftwareId') or ''):8} {str(i.get('Version')):14} updateable={i.get('Updateable')} state={i.get('Status', {}).get('State')}")
            return 0
        if cmd == "drift":
            base_json = json.load(open(flags[flags.index("--baseline") + 1]))
            us, items = inventory(c)
            rows, bad = drift(items, base_json)
            for k, want, have, status in rows:
                print(f"{k:24} expected={want!s:10} found={have!s:12} {status}")
            print(f"\n{bad} problem(s)")
            return 1 if bad else 0
        if cmd == "update":
            get_v = lambda n, d=None: flags[flags.index(n) + 1] if n in flags else d
            return cmd_update(c, dict(target=get_v("--target"), image_uri=get_v("--image-uri"), force="--force" in flags,
                                      activate="--activate" in flags, yes="--yes" in flags, reset_type=get_v("--reset-type"), timeout=int(get_v("--timeout", 900))))
        print(__doc__); return 2
    finally:
        c.logout()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
