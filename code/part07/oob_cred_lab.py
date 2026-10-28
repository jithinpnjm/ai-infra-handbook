#!/usr/bin/env python3
"""Self-checking lab for Chapter 7.1: BMCs, IPMI and out-of-band management."""
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

import cred_audit
import oob_sim

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

    # 1. Verify oob_sim.reach() across all 6 failure scenarios + BMC firmware crash
    results = {
        name: oob_sim.reach(ac, host, os_state, mgmt, prod)
        for name, ac, host, os_state, mgmt, prod in oob_sim.SCENARIOS
    }
    check(
        "oob_sim.py models in-band SSH vs out-of-band BMC reachability across all 6 scenarios",
        results["healthy server"] == (True, True, True, True)
        and results["OS kernel panic"] == (False, True, True, True)
        and results["host powered off"] == (False, True, True, True)
        and results["production network down"] == (False, True, True, True)
        and results["management switch down"] == (True, False, False, False)
        and results["rack lost AC power"] == (False, False, False, False),
    )

    # 2. Verify cred_audit.py catches factory default (admin/admin on node005), empty password (node006), and 4 credential groups
    sample_csv = code_dir / "sample_bmc_accounts.csv"
    proc = subprocess.run(
        [sys.executable, str(code_dir / "cred_audit.py"), str(sample_csv)],
        capture_output=True,
        text=True,
    )
    out = proc.stdout
    check(
        "cred_audit.py detects 4 credential groups, node005 factory-default (admin), and node006 empty password (exit 1)",
        proc.returncode == 1
        and "4 different credential sets" in out
        and "PROBLEM node005: factory-default credentials (admin)" in out
        and "PROBLEM node006: empty BMC password" in out,
    )

    # 3. Verify a remediated uniform BMC credential CSV exits 0 with 1 group of 7 nodes
    with tempfile.TemporaryDirectory() as tmpdir:
        fixed_csv = Path(tmpdir) / "fixed_bmc_accounts.csv"
        with open(fixed_csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["node", "bmc_user", "bmc_password"])
            for i in range(1, 8):
                w.writerow([f"node00{i}", "bmcadmin", "R9#vK2!mQ8$pL5@x"])
        proc_ok = subprocess.run(
            [sys.executable, str(code_dir / "cred_audit.py"), str(fixed_csv)],
            capture_output=True,
            text=True,
        )
        check(
            "cred_audit.py exits 0 with 1 group (7 nodes) when all BMCs share a strong 16-char rotated credential",
            proc_ok.returncode == 0
            and "PROBLEM" not in proc_ok.stdout
            and "7  bmcadmin" in proc_ok.stdout,
        )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
