#!/usr/bin/env python3
"""Self-checking lab for Chapter 7.7: Systems, Chassis and Managers: the core resource model."""
import sys
import threading

import redfish_crawl
import redfish_mock
import rf_inventory
import rf_model

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
    srv, _ = redfish_mock.make_server("dgx", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    try:
        c = redfish_crawl.Client(base, "admin", "adminpass")
        res = rf_model.build(c)
        probs = rf_model.check(res)
        mmd = rf_model.mermaid(res)
        inv = rf_inventory.inventory(c)
        c.logout()

        # 1. Verify rf_model.build() discovers 2 Systems, 1 Chassis, 1 Manager with 0 bidirectional link findings
        check(
            "rf_model.py discovers 2 Systems (System_0, HGX_Baseboard_0), 1 Chassis, 1 Manager with 0 bidirectional link errors",
            len(res["System"]) == 2
            and len(res["Chassis"]) == 1
            and len(res["Manager"]) == 1
            and len(probs) == 0
            and "flowchart LR" in mmd,
        )

        # 2. Verify rf_inventory.py reports CPU count (2) and RAM (2048 GiB) on System_0 and GPU count (8) on HGX_Baseboard_0
        by_sys = {r["system"]: r for r in inv}
        check(
            "rf_inventory.py extracts System_0 (2 CPUs, 2048 GiB) and HGX_Baseboard_0 (8 GPUs) managed by BMC_0",
            by_sys["System_0"]["cpus"] == 2
            and by_sys["System_0"]["mem_gib"] == 2048
            and by_sys["HGX_Baseboard_0"]["gpus"] == 8
            and by_sys["System_0"]["bmc"] == "BMC_0",
        )

        # 3. Verify rf_model.check() catches a deliberate one-way link when ManagerForChassis is removed
        res["Manager"]["/redfish/v1/Managers/BMC_0"]["Links"]["ManagerForChassis"] = []
        probs_broken = rf_model.check(res)
        check(
            "rf_model.check() detects ONE-WAY link when ManagerForChassis is missing from BMC_0",
            len(probs_broken) == 1 and "ONE-WAY" in probs_broken[0],
        )
    finally:
        srv.shutdown()

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
