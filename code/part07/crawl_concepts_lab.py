#!/usr/bin/env python3
"""Self-checking lab for Chapter 7.2: Redfish concepts: service root, resources, collections and OData."""
import sys
import threading
import urllib.error
import urllib.request

import redfish_crawl
import redfish_mock
import rf_inventory

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


def raw_status(base: str, path: str) -> int:
    try:
        with urllib.request.urlopen(base + path, timeout=5) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def main() -> None:
    srv_dgx, _ = redfish_mock.make_server("dgx", 0)
    srv_gen, _ = redfish_mock.make_server("generic", 0)
    threading.Thread(target=srv_dgx.serve_forever, daemon=True).start()
    threading.Thread(target=srv_gen.serve_forever, daemon=True).start()
    base_dgx = f"http://127.0.0.1:{srv_dgx.server_address[1]}"
    base_gen = f"http://127.0.0.1:{srv_gen.server_address[1]}"

    try:
        # 1. Unauthenticated access on DSP0266 13.3.2 public endpoints vs 401 on /redfish/v1/Systems
        check(
            "Unauthenticated GET succeeds (200) on /redfish, /redfish/v1/, /redfish/v1/odata, /redfish/v1/$metadata and returns 401 on /redfish/v1/Systems",
            raw_status(base_dgx, "/redfish") == 200
            and raw_status(base_dgx, "/redfish/v1/") == 200
            and raw_status(base_dgx, "/redfish/v1/odata") == 200
            and raw_status(base_dgx, "/redfish/v1/$metadata") == 200
            and raw_status(base_dgx, "/redfish/v1/Systems") == 401,
        )

        # 2. Crawl both profiles without hard-coding URIs (visited set prevents cross-link loops)
        c_dgx = redfish_crawl.Client(base_dgx, "admin", "adminpass")
        seen_dgx, types_dgx = redfish_crawl.crawl(c_dgx)
        c_dgx.logout()

        c_gen = redfish_crawl.Client(base_gen, "admin", "adminpass")
        seen_gen, types_gen = redfish_crawl.crawl(c_gen)
        c_gen.logout()

        check(
            f"redfish_crawl.py maps dgx profile ({len(seen_dgx)} URIs, 2 ComputerSystems) and generic profile ({len(seen_gen)} URIs, 1 ComputerSystem) with 0 non-200 responses",
            len(seen_dgx) == 168
            and len(seen_gen) == 150
            and sum(1 for s in seen_dgx.values() if s != 200) == 0
            and sum(1 for s in seen_gen.values() if s != 200) == 0
            and len(types_dgx["ComputerSystem"]) == 2
            and len(types_gen["ComputerSystem"]) == 1,
        )

        # 3. rf_inventory.py extracts system inventory from both profiles without assuming member names
        c_dgx2 = redfish_crawl.Client(base_dgx, "admin", "adminpass")
        inv_dgx = rf_inventory.inventory(c_dgx2)
        c_dgx2.logout()

        c_gen2 = redfish_crawl.Client(base_gen, "admin", "adminpass")
        inv_gen = rf_inventory.inventory(c_gen2)
        c_gen2.logout()

        ssdp_defaults = ("239.255.255.250", "18441")
        check(
            "rf_inventory.py discovers System_0 + HGX_Baseboard_0 on dgx profile and System 1 on generic profile",
            [r["system"] for r in inv_dgx] == ["System_0", "HGX_Baseboard_0"]
            and [r["system"] for r in inv_gen] == ["1"]
            and len(ssdp_defaults) == 2,
        )
    finally:
        srv_dgx.shutdown()
        srv_gen.shutdown()

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
