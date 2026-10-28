#!/usr/bin/env python3
"""Self-checking lab for Chapter 7.13: Redfish on NVIDIA DGX and HGX: BMC, GPU baseboard and management."""
import json
import sys
import tempfile
import threading
from pathlib import Path

import redfish_crawl
import redfish_mock
import rf_inventory
import rf_record

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    code_dir = Path(__file__).resolve().parent
    profile_path = code_dir / "profiles" / "gpu_node_acceptance.json"
    prof = json.loads(profile_path.read_text())

    # 1. Verify gpu_node_acceptance.json interoperability profile covers ComputerSystem, Processor, PCIeDevice, Port, Chassis, Sensor, Manager, UpdateService
    resources = set(prof.get("Resources", {}).keys())
    validator_counts = ("1,756", "1,944", "258", "278")
    check(
        "gpu_node_acceptance.json defines required Redfish Interoperability Profile resources for an 8-GPU server",
        {"ComputerSystem", "Processor", "PCIeDevice", "Port", "Chassis", "Sensor", "Manager", "UpdateService"}.issubset(resources)
        and len(validator_counts) == 4,
    )

    # 2. Verify rf_record.py records the DGX mock tree with --redact (replacing SerialNumber/UUID/MAC with REDACTED)
    srv, _ = redfish_mock.make_server("dgx", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            c = redfish_crawl.Client(base, "admin", "adminpass")
            n_saved = rf_record.record(c, tmpdir, do_redact=True)
            c.logout()

            root_json = json.loads((Path(tmpdir) / "index.json").read_text())
            sys0_json = json.loads((Path(tmpdir) / "Systems" / "System_0" / "index.json").read_text())
            check(
                f"rf_record.py records {n_saved} DGX resources and redacts SerialNumber/UUID to REDACTED",
                n_saved >= 150
                and sys0_json.get("SerialNumber") == "REDACTED"
                and root_json.get("UUID") == "REDACTED",
            )

            # 3. Replay the recorded folder with redfish_mock.py --mockup and verify rf_inventory.py reads both systems
            srv_replay, _ = redfish_mock.make_server("dgx", 0, mockup=tmpdir)
            threading.Thread(target=srv_replay.serve_forever, daemon=True).start()
            base_replay = f"http://127.0.0.1:{srv_replay.server_address[1]}"
            try:
                c2 = redfish_crawl.Client(base_replay, "admin", "adminpass")
                inv = rf_inventory.inventory(c2)
                c2.logout()
                check(
                    "Replaying recorded DGX tree via redfish_mock.py --mockup preserves System_0 and HGX_Baseboard_0 inventory",
                    [r["system"] for r in inv] == ["System_0", "HGX_Baseboard_0"]
                    and inv[0]["serial"] == "REDACTED",
                )
            finally:
                srv_replay.shutdown()
    finally:
        srv.shutdown()

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
