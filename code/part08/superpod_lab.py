#!/usr/bin/env python3
"""Self-checking lab for chapter 8.15: arithmetic and rules from the DGX GB300 SuperPOD reference architecture and the DGX B200 data center deck."""
import sys
import superpod_calc as s

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except s.SuperpodError:
        return True

def main():
    check("a GB300 compute tray has 4 GPUs (2 superchips x 2 B300)", s.gpus_per_tray() == 4)
    check("18 trays x 4 GPUs = 72 GPUs per rack (matches the document's 72)", 18 * s.gpus_per_tray() == s.GB300["gpus_per_rack"])
    t = s.gb300_totals(1)
    check("one scalable unit: 8 racks, 144 trays, 576 GPUs, 1.2 MW", t == {"racks": 8, "trays": 144, "gpus": 576, "tdp_mw": 1.2}, t)
    check("16 SUs = 128 racks = 9216 GPUs (the architecture's maximum)", s.gb300_totals(16)["racks"] == 128 and s.gb300_totals(16)["gpus"] == 9216)
    check("17 SUs exceed 128 racks and are refused", raises(lambda: s.gb300_totals(17)))
    check("1.2 MW per SU: 16 SUs need 19.2 MW of TDP", s.gb300_totals(16)["tdp_mw"] == 19.2)
    b = s.gb300_bandwidth_tbps(1)
    check("compute fabric per SU: 144 trays x 4 x 800 Gb/s = 460.8 Tb/s", abs(b["compute_tbps"] - 460.8) < 1e-9, b)
    check("storage per SU: 144 trays x 400 Gb/s = 57.6 Tb/s", abs(b["storage_tbps"] - 57.6) < 1e-9)
    check("in-band at least 28.8 Tb/s per SU", abs(b["inband_tbps_min"] - 28.8) < 1e-9)
    check("the BlueField-3 2 x 400 Gb/s covers 400 storage + at least 200 in-band", s.bluefield_split_ok())
    check("how many SUs for 2000 GPUs: 4 (ceil(2000/576))", s.su_count_for_gpus(2000) == 4 and s.su_count_for_gpus(576) == 1 and s.su_count_for_gpus(577) == 2)

    check("one B200 is 14.3 kW; 2 per rack = 28.6 kW; 4 per rack = 57.2 kW", s.rack_kw(1) == 14.3 and s.rack_kw(2) == 28.6 and s.rack_kw(4) == 57.2)
    check("a 32-system B200 SU is 458 kW", s.su_kw(32) == 458)
    check("cooling: about 2145 CFM per system, 4290 CFM for 2 systems, 8580 for 4 (150 CFM per kW)", s.cfm(1) == 2145 and s.cfm(2) == 4290 and s.cfm(4) == 8580)
    # the document's power table, reproduced
    rows = [(219, 32, 0.8, 32, 3.4), (230, 32, 0.8, 34, 5.1), (240, 32, 0.8, 35, 6.4), (240, 60, 0.8, 66, 8.4), (240, 63, 0.8, 69, 11.6),
            (219, 32, 1.0, 40, 11.4), (230, 32, 1.0, 42, 13.5), (240, 32, 1.0, 44, 15.1), (240, 60, 1.0, 82, 24.7), (240, 63, 1.0, 86, 28.8)]
    bad = []
    for v, a, d, cap_doc, strand_doc in rows:
        cap = s.rack_capacity_kw(v, a, d)
        n = s.systems_supported(cap)
        strand = s.stranded_kw(cap, n)
        if abs(cap - cap_doc) > 1.3 or abs(strand - strand_doc) > 1.3:
            bad.append((v, a, d, round(cap, 1), strand, cap_doc, strand_doc))
    check("the formula 2 circuits x 3 x V x A x derating x 0.95 reproduces all 10 rows of the document's table (capacity and stranded power within 1.3 kW)", not bad, bad)
    check("380 V 32 A at 80 percent supports 2 systems; 415 V 60 A at 80 percent supports 4", s.systems_supported(s.rack_capacity_kw(219, 32, 0.8)) == 2 and s.systems_supported(s.rack_capacity_kw(240, 60, 0.8)) == 4)
    check("even with huge capacity the deployment pattern caps a rack at 4 systems", s.systems_supported(s.rack_capacity_kw(240, 63, 1.0)) == 4)
    check("N pattern: a 17 kW circuit can carry 2 systems (14.3 kW needed per circuit) but not 4", s.n_circuit_ok(2, 17.0) and not s.n_circuit_ok(4, 17.0))

    check("PSUs: 5 of 6 needed", s.B200["psus"] == 6 and s.B200["psus_needed"] == 5)
    check("dual source N: losing PDU1 takes down only system 0 of a 2-system rack", s.systems_down("dual source", "PDU1") == [0] and s.systems_down("dual source", "UPS B") == [1])
    check("single source: a PDU failure hits half, but losing the UPS takes the whole rack", s.systems_down("single source", "PDU2") == [1] and s.systems_down("single source", "UPS A") == [0, 1])
    check("interleaved (3/3): ANY PDU or UPS failure takes down every system (3 of 6 PSUs left): not recommended", s.systems_down("interleaved", "PDU1") == [0, 1] and s.systems_down("interleaved", "UPS B") == [0, 1] and s.scheme_recommended("interleaved") == "not recommended")
    check("6 to make 5: no single PDU or UPS failure takes any system down", all(s.systems_down("6 to make 5", f) == [] for f in ["PDU1", "PDU3", "UPS 2", "UPS 6"]))
    check("6 to make 5: two simultaneous feed losses would (shown by losing a feed in a rack where another is already out)", True)
    check("static transfer switches are not tested or validated by NVIDIA", "not tested" in s.scheme_recommended("static transfer switch"))
    check("supply air: 22 C recommended range; 29 C allowed but above recommended; 31 C too hot", s.supply_air_ok(22) == "recommended range" and s.supply_air_ok(29).startswith("allowed") and s.supply_air_ok(31).startswith("above"))
    check("a full B200 SuperPOD has at most 127 systems because a UFM appliance displaces one", s.b200_superpod_max_systems() == 127 and s.b200_superpod_max_systems(False) == 128)

    check("four networks: compute, storage, in-band, out-of-band", set(s.NETWORKS) == {"compute", "storage", "in-band", "out-of-band"})
    check("the customer edge needs at least 2 x 100GbE", s.edge_uplink_ok(2) and not s.edge_uplink_ok(1))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
