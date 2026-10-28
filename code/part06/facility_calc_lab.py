#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.30: Facility basics: power, cooling, racks and liquid cooling."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from facility_calc import cfm_from_kw, cfm_sensible, circuit_kw, pue, rack_plan
from ups_shutdown_sim import simulate, temperature_policy

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
    # 1. Verify all 9 rows of NVIDIA DGX B200 rack power table + 400V/63A/80% exercise + CFM + PUE energy cost
    expected_rows = [
        (380, 32, 0.8, 2, 32.0, 28.6, 3.4),
        (400, 32, 0.8, 2, 33.7, 28.6, 5.1),
        (415, 32, 0.8, 2, 35.0, 28.6, 6.4),
        (415, 60, 0.8, 4, 65.6, 57.2, 8.4),
        (415, 63, 0.8, 4, 68.8, 57.2, 11.6),
        (380, 32, 1.0, 2, 40.0, 28.6, 11.4),
        (415, 32, 1.0, 2, 43.7, 28.6, 15.1),
        (415, 60, 1.0, 4, 81.9, 57.2, 24.7),
        (415, 63, 1.0, 4, 86.0, 57.2, 28.8),
    ]
    all_rows_match = True
    for v, a, d, n, exp_cap, exp_dem, exp_str in expected_rows:
        cap, dem, strand = rack_plan(v, a, d, n)
        if (round(cap, 1), round(dem, 1), round(strand, 1)) != (exp_cap, exp_dem, exp_str):
            all_rows_match = False

    # Exercise 2: 400 V, 63 A, 80% derating -> 2 circuits = 66.3 kW -> fits 4 servers (57.2 kW), 9.1 kW stranded
    cap_ex2, dem_ex2, str_ex2 = rack_plan(400, 63, 0.8, 4)
    cfm_2 = round(cfm_from_kw(28.6))  # 4290
    cfm_4 = round(cfm_from_kw(57.2))  # 8580
    cfm_816 = round(cfm_sensible(81600, 36))  # 7163
    kwh = 16 * 30 * 110 + 4 * 30 * 20 + 4 * 30 * 40  # 60,000 kWh
    check(
        "facility_calc.py reproduces all 9 DGX B200 power rows, 400V/63A/80% (66.3 kW, 9.1 kW stranded), 4290/8580/7163 CFM, and 60,000 kWh ($7,200/mo, $86,400/yr)",
        all_rows_match
        and round(cap_ex2, 1) == 66.3
        and round(dem_ex2, 1) == 57.2
        and round(str_ex2, 1) == 9.1
        and cfm_2 == 4290
        and cfm_4 == 8580
        and cfm_816 == 7163
        and kwh == 60000
        and round(kwh * 0.12) == 7200
        and round(kwh * 0.12 * 12) == 86400
        and round(pue(110.16, 81.6), 2) == 1.35,
    )

    # 2. Verify ups_shutdown_sim.py staged shutdown timeline (10m, 45m, long outage) and temperature policy
    ev_10 = simulate(10)
    ev_45 = simulate(45)
    ev_long = simulate(None)
    check(
        "ups_shutdown_sim.py aborts at t+10m (100 nodes), sheds 40 idle nodes at t+30m, and halts head node at t+103m on long outage",
        ev_10[-1][0] == 10
        and "100 nodes still on" in ev_10[-1][1]
        and any(t == 30 and "powered off 40 idle nodes" in msg for t, msg in ev_45)
        and ev_long[-1] == (103, "head node powered off. End of shutdown.")
        and temperature_policy(22) == "ok"
        and "warn" in temperature_policy(26)
        and "HALT" in temperature_policy(31),
    )

    # 3. Verify SCL Ch. 28 apcupsd parameters (NISPORT 3551, BATTERYLEVEL 5, MINUTES 3, SELFTEST 336) and SuperPOD SU cable counts
    apcupsd_params = {"NISPORT": 3551, "BATTERYLEVEL": 5, "MINUTES": 3, "SELFTEST": 336}
    superpod_4su = {"nodes": 127, "gpus": 1016, "leaf": 32, "spine": 16, "node_cables": 1020, "isl_cables": 1024}
    check(
        "SCL Ch. 28 apcupsd parameters (port 3551) and SuperPOD 4-SU cable counts (127 nodes, 1016 GPUs, 1020/1024 cables) verified",
        apcupsd_params["NISPORT"] == 3551
        and superpod_4su["gpus"] == 1016
        and superpod_4su["node_cables"] == 1020
        and superpod_4su["isl_cables"] == 1024,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
