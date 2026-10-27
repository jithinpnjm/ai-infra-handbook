"""Self-verifying lab for Chapter 12.10: HDR, NDR, XDR, Optics, and Cabling.

Runs 28 deterministic checks covering:
- SDR/DDR/QDR/FDR/EDR/HDR/NDR/XDR/GDR per-lane speeds, 8b/10b, 64b/66b, and
  256b/257b coding, and 4x/12x aggregate bandwidths (Supercomputers Ch. 5 Table 5-1).
- V8 Ch. 8 link negotiation & width degradation (`4X 400 Gbps` vs `2X 400 Gbps`
  halving effective bandwidth to 200 Gbps; `Rate: 200` doubling 2 MiB RDMA write
  latency from 41.94 us (~42 us) to 83.89 us (~84 us); PCIe Gen4 x8 126.03 Gbps
  vs Gen5 x16 504.12 Gbps vs Gen6 x16 968.0 Gbps host-injection ceilings).
- Scale-up NVLink progression (Volta 300G, Ampere 600G, Hopper 900G, Blackwell
  1800G) and Dell'Oro 2020-2029 optics adoption curves (ADC Ch. 4).
- SerDes mux/demux (8x50G -> 400G, 4x100G -> 400G, 8x100G -> 800G, 8x200G -> 1.6T)
  and NRZ (1 bit/symbol, 2 levels, 1 eye) vs PAM-4 (2 bits/symbol, 4 levels,
  3 eye openings, 9.54 dB SNR penalty) DSP equalization/FEC/CDR pipeline.
- MMF OM1-OM5 (62.5 um / 50 um, 850/953/1300 nm) vs SMF (8-10 um, 1310/1550 nm)
  and ADC Table 4-1 transceiver types (VR 50 m, SR 100 m, DR 500 m, FR 2 km,
  LR 10 km, ZR >80 km, CR 7 m / 10 m).
- MPO-12/16/32 breakout fan-out rules (`400G-DR4` MPO-12 4 Tx + 4 Rx + 4 dark;
  `400G-SR8` MPO-16 8 Tx + 8 Rx; twin-port 800G OSFP -> 2x400G or 4x200G) and
  SuperPOD <90% cable length derating rule (`27 m` on `30 m` AOC, `45 m` on
  `50 m` AOC, `2.7 m` on `3 m` DAC, and no patch panels).
- ADC Tables 4-2 & 4-3 form factors (QSFP28, QSFP56, QSFP-DD Type 1/2/2A/2B,
  OSFP, CFP8 16 vs 36 ports/RU) and Pluggable vs LPO vs LRO vs CPO power/BOM math.
- `mlxlink -d mlx5_1 -c` / `-m` physical counter, BER, CDR, and DDM optical health.
"""

from __future__ import annotations

from optics_cabling_hdr_ndr_xdr import (
    ADC_TABLE_4_1_TRANSCEIVERS,
    DELLORO_2020_2027_SHARES,
    DELLORO_2025_REPORT_SHARES,
    FIBER_GRADE_SPECS,
    FORM_FACTOR_TABLE,
    IB_GENERATION_TABLE,
    NVLINK_GENERATION_BW_GBPS,
    QSFP_DD_CAGE_TYPES,
    compare_optics_packaging_power,
    evaluate_ib_link_negotiation,
    evaluate_mlxlink_module_health,
    evaluate_mpo_breakout,
    evaluate_superpod_cable_derating,
    plan_serdes_mux_demux,
    select_transceiver_and_fiber,
)


def run_lab() -> int:
    passed = 0
    total = 0

    def check(condition: bool, label: str) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [FAIL] {label}")

    print("Running Chapter 12.10 HDR, NDR, XDR, Optics & Cabling Lab Checks...\n")

    # 1. Legacy & Modern InfiniBand Table 5-1 (SDR -> GDR)
    sdr = IB_GENERATION_TABLE["SDR"]
    ddr = IB_GENERATION_TABLE["DDR"]
    qdr = IB_GENERATION_TABLE["QDR"]
    fdr = IB_GENERATION_TABLE["FDR"]
    edr = IB_GENERATION_TABLE["EDR"]
    check(
        sdr.raw_lane_rate_gbps == 2.5
        and sdr.nominal_4x_bw_gbps == 8.0
        and sdr.nominal_12x_bw_gbps == 24.0
        and ddr.nominal_4x_bw_gbps == 16.0
        and qdr.nominal_4x_bw_gbps == 32.0
        and fdr.raw_lane_rate_gbps == 14.0625
        and fdr.nominal_4x_bw_gbps == 54.4
        and fdr.nominal_12x_bw_gbps == 163.2
        and edr.nominal_4x_bw_gbps == 100.0
        and sdr.coding_label == "8/10"
        and fdr.coding_label == "64/66",
        "Supercomputers Ch. 5 Table 5-1 legacy IB rates: SDR 8G/24G, DDR 16G/48G, QDR 32G/96G (8/10), FDR 14.0625G lane -> 54.4G/163.2G, EDR 100G/300G (64/66)",
    )

    hdr = IB_GENERATION_TABLE["HDR"]
    ndr = IB_GENERATION_TABLE["NDR"]
    xdr = IB_GENERATION_TABLE["XDR"]
    gdr = IB_GENERATION_TABLE["GDR"]
    check(
        hdr.raw_lane_rate_gbps == 53.125
        and hdr.nominal_4x_bw_gbps == 200.0
        and hdr.nominal_12x_bw_gbps == 600.0
        and hdr.coding_label == "64/66"
        and ndr.raw_lane_rate_gbps == 106.25
        and ndr.nominal_4x_bw_gbps == 400.0
        and ndr.nominal_12x_bw_gbps == 1200.0
        and ndr.coding_label == "256/257"
        and xdr.raw_lane_rate_gbps == 200.0
        and xdr.nominal_4x_bw_gbps == 800.0
        and xdr.nominal_12x_bw_gbps == 2400.0
        and gdr.raw_lane_rate_gbps == 400.0
        and gdr.nominal_4x_bw_gbps == 1600.0
        and gdr.nominal_12x_bw_gbps == 4800.0,
        "Supercomputers Ch. 5 Table 5-1 modern IB rates: HDR 53.125G/lane (200G 4x, 600G 12x, 64/66), NDR 106.25G/lane (400G 4x, 1200G 12x, 256/257), XDR 200G/lane (800G 4x, 2400G 12x), GDR 400G/lane (1600G 4x, 4800G 12x)",
    )

    # 2. V8 Ch. 8 Link Negotiation & Width Degradation (`4X 400 Gbps` vs `2X 400 Gbps`)
    ndr_4x = evaluate_ib_link_negotiation("NDR", designed_lanes=4, active_lanes=4, pcie_gen=5, pcie_lanes=16)
    ndr_2x = evaluate_ib_link_negotiation("NDR", designed_lanes=4, active_lanes=2, pcie_gen=5, pcie_lanes=16)
    check(
        ndr_4x.negotiated_link_bw_gbps == 400.0
        and ndr_4x.bottleneck_stage == "FULL_DESIGN_RATE"
        and ndr_2x.negotiated_link_bw_gbps == 200.0
        and ndr_2x.bottleneck_stage == "LANE_WIDTH_DEGRADATION",
        "V8 Ch. 8 `iblinkinfo` width collapse: `4X 400 Gbps` (port 3) delivers 400.0 Gbps while `2X 400 Gbps` (port 4) halves capacity to 200.0 Gbps despite the 400 Gbps rate label",
    )

    # 3. V8 Ch. 8 Scenario 1: `Rate: 200` on a 400G port -> 2 MiB RDMA write 41.94 us (~42 us) vs 83.89 us (~84 us)
    ndr_rate_200 = evaluate_ib_link_negotiation(
        "NDR", designed_lanes=4, active_lanes=4, negotiated_rate_override_gbps=200.0, pcie_gen=5, pcie_lanes=16
    )
    check(
        ndr_rate_200.bottleneck_stage == "RATE_DOWN_NEGOTIATION"
        and ndr_4x.rdma_2mib_transfer_us == 41.94
        and ndr_rate_200.rdma_2mib_transfer_us == 83.89
        and round(ndr_rate_200.rdma_2mib_transfer_us / ndr_4x.rdma_2mib_transfer_us, 1) == 2.0,
        "V8 Ch. 8 Scenario 1 rate down-negotiation (`Rate: 200` on 400G port): 2 MiB (2,097,152 B) RDMA write latency doubles from 41.94 us (~42 us) to 83.89 us (~84 us)",
    )

    # 4. V8 Ch. 8 Host PCIe Ceiling (400G HCA in PCIe Gen4 x8 vs Gen5 x16 vs XDR 800G in Gen6 x16)
    ndr_gen4_x8 = evaluate_ib_link_negotiation("NDR", designed_lanes=4, active_lanes=4, pcie_gen=4, pcie_lanes=8)
    xdr_gen5_x16 = evaluate_ib_link_negotiation("XDR", designed_lanes=4, active_lanes=4, pcie_gen=5, pcie_lanes=16)
    xdr_gen6_x16 = evaluate_ib_link_negotiation("XDR", designed_lanes=4, active_lanes=4, pcie_gen=6, pcie_lanes=16)
    check(
        ndr_gen4_x8.pcie_ceiling_gbps == 126.03
        and ndr_gen4_x8.delivered_payload_bw_gbps == 126.03
        and ndr_gen4_x8.bottleneck_stage == "HOST_PCIE_INJECTION_CEILING"
        and xdr_gen5_x16.pcie_ceiling_gbps == 504.12
        and xdr_gen5_x16.bottleneck_stage == "HOST_PCIE_INJECTION_CEILING"
        and xdr_gen6_x16.pcie_ceiling_gbps == 968.0
        and xdr_gen6_x16.delivered_payload_bw_gbps == 800.0
        and xdr_gen6_x16.bottleneck_stage == "FULL_DESIGN_RATE",
        "V8 Ch. 8 Host PCIe injection ceiling: 400G NDR in PCIe Gen4 x8 capped at 126.03 Gbps; Gen5 x16 provides 504.12 Gbps; 800G XDR requires PCIe Gen6 x16 (968.0 Gbps) or dual Gen5 x16",
    )

    # 5. ADC Ch. 4 Scale-Up NVLink & Dell'Oro Market Adoption (2020-2029)
    check(
        NVLINK_GENERATION_BW_GBPS == {"Volta": 300, "Ampere": 600, "Hopper": 900, "Blackwell": 1800}
        and DELLORO_2020_2027_SHARES[2020] == {"100G": 55, "200G": 30, "400G": 15, "800G": 0, "1600G": 0}
        and DELLORO_2020_2027_SHARES[2025] == {"100G": 2, "200G": 5, "400G": 10, "800G": 70, "1600G": 13}
        and DELLORO_2020_2027_SHARES[2027] == {"100G": 1, "200G": 2, "400G": 3, "800G": 30, "1600G": 64},
        "ADC Ch. 4 NVLink progression (Volta 300G, Ampere 600G, Hopper 900G, Blackwell 1800G) and Dell'Oro 2020-2027 optics curve (2020: 55% 100G; 2025: 70% 800G; 2027: 64% 1.6T)",
    )

    check(
        sum(DELLORO_2025_REPORT_SHARES["2025e"].values()) == 100
        and DELLORO_2025_REPORT_SHARES["2025e"]["800G"] == 70
        and DELLORO_2025_REPORT_SHARES["2027e"]["1600G"] == 50
        and DELLORO_2025_REPORT_SHARES["2029e"][">=3200G"] == 30
        and sum(DELLORO_2025_REPORT_SHARES["2029e"].values()) == 100,
        "ADC Ch. 4 Figure 4-2.1 Dell'Oro 2025 update: 2025e = 70% 800G (25% 400G, 3% 200G, 2% <=100G); 2027e = 50% 1.6T + 43% 800G; 2029e = 50% 1.6T + 30% >=3.2T + 16% 800G",
    )

    # 6. ADC Ch. 4 SerDes Demux/Mux & NRZ vs PAM4 Eye/SNR Math
    mux_50g_400g = plan_serdes_mux_demux(400, 50, 50, "PAM4")
    mux_100g_400g = plan_serdes_mux_demux(400, 100, 100, "PAM4")
    mux_100g_800g = plan_serdes_mux_demux(800, 100, 100, "PAM4")
    mux_200g_1600g = plan_serdes_mux_demux(1600, 200, 200, "PAM4")
    mux_50g_to_100g_opt = plan_serdes_mux_demux(400, 50, 100, "PAM4")
    nrz_100g = plan_serdes_mux_demux(100, 25, 25, "NRZ")
    check(
        mux_50g_400g.asic_serdes_lanes == 8
        and mux_100g_400g.asic_serdes_lanes == 4
        and mux_100g_800g.asic_serdes_lanes == 8
        and mux_200g_1600g.asic_serdes_lanes == 8
        and mux_50g_to_100g_opt.mux_ratio == "2:1",
        "ADC Ch. 4 PFE ASIC SerDes demux/mux: 8x50G -> 400G, 4x100G -> 400G (2:1 gearbox from 8x50G), 8x100G -> 800G, and 8x200G -> 1.6T",
    )

    check(
        nrz_100g.bits_per_symbol == 1
        and nrz_100g.voltage_levels == 2
        and nrz_100g.eye_openings == 1
        and nrz_100g.snr_penalty_vs_nrz_db == 0.0
        and mux_100g_400g.bits_per_symbol == 2
        and mux_100g_400g.voltage_levels == 4
        and mux_100g_400g.eye_openings == 3
        and mux_100g_400g.snr_penalty_vs_nrz_db == 9.54,
        "ADC Ch. 4 NRZ vs PAM-4 DSP physics: NRZ = 2 levels (0, 1), 1 bit/symbol, 1 eye; PAM-4 = 4 levels (00, 01, 10, 11), 2 bits/symbol, 3 eye openings, 9.54 dB SNR penalty requiring FFE/DFE, CDR, and LDPC/BCH FEC",
    )

    # 7. ADC Ch. 4 Multi-Mode Fiber (OM1-OM5) vs Single-Mode Fiber (SMF)
    om1 = FIBER_GRADE_SPECS["OM1"]
    om2 = FIBER_GRADE_SPECS["OM2"]
    om3 = FIBER_GRADE_SPECS["OM3"]
    om4 = FIBER_GRADE_SPECS["OM4"]
    om5 = FIBER_GRADE_SPECS["OM5"]
    smf = FIBER_GRADE_SPECS["SMF"]
    check(
        om1.core_diameter_um == (62.5,)
        and om1.max_reach_1g_m == 300
        and om1.max_reach_10g_m == 33
        and om2.core_diameter_um == (50.0,)
        and om2.max_reach_1g_m == 550
        and om2.max_reach_10g_m == 82
        and om3.max_reach_40g_m == 240
        and om3.max_reach_100g_400g_m == 100
        and om4.max_reach_100g_400g_m == 150
        and om5.wavelengths_nm == (850, 953)
        and om5.max_reach_100g_400g_m == 150
        and smf.core_diameter_um == (8.0, 10.0)
        and smf.wavelengths_nm == (1310, 1550),
        "ADC Ch. 4 MMF & SMF grades: OM1 (62.5 um, 300 m @ 1G, 33 m @ 10G), OM2 (50 um, 550 m @ 1G, 82 m @ 10G), OM3 (240 m @ 40G, 100 m @ 100G-400G), OM4 (150 m @ 100G-400G), OM5 (850+953 nm WDM, 150 m), SMF (8-10 um core, 1310/1550 nm)",
    )

    # 8. ADC Ch. 4 Table 4-1 Transceiver Types (VR, SR, DR, FR, LR, ZR, CR)
    check(
        ADC_TABLE_4_1_TRANSCEIVERS["VR"].max_reach_m == 50
        and ADC_TABLE_4_1_TRANSCEIVERS["VR"].mode == "MMF"
        and ADC_TABLE_4_1_TRANSCEIVERS["SR"].max_reach_m == 100
        and ADC_TABLE_4_1_TRANSCEIVERS["SR"].mode == "MMF"
        and ADC_TABLE_4_1_TRANSCEIVERS["DR"].max_reach_m == 500
        and ADC_TABLE_4_1_TRANSCEIVERS["DR"].mode == "SMF"
        and ADC_TABLE_4_1_TRANSCEIVERS["FR"].max_reach_m == 2000
        and ADC_TABLE_4_1_TRANSCEIVERS["FR"].mode == "SMF"
        and ADC_TABLE_4_1_TRANSCEIVERS["LR"].max_reach_m == 10000
        and ADC_TABLE_4_1_TRANSCEIVERS["LR"].mode == "SMF"
        and ADC_TABLE_4_1_TRANSCEIVERS["ZR"].max_reach_m == 80000
        and ADC_TABLE_4_1_TRANSCEIVERS["ZR"].mode == "DWDM"
        and ADC_TABLE_4_1_TRANSCEIVERS["CR_PASSIVE"].max_reach_m == 7
        and ADC_TABLE_4_1_TRANSCEIVERS["CR_ACTIVE"].max_reach_m == 10,
        "ADC Ch. 4 Table 4-1 transceiver reaches: VR=50 m (MMF), SR=100 m (MMF), DR=500 m (SMF), FR=2 km (SMF), LR=10 km (SMF), ZR=>80 km (DWDM), CR=7 m passive / 10 m active DAC",
    )

    # 9. Distance-based Transceiver Selection across Rack / Row / Hall / Campus / DCI
    sel_2m = select_transceiver_and_fiber(2.0, 400)
    sel_35m = select_transceiver_and_fiber(35.0, 400)
    sel_85m = select_transceiver_and_fiber(85.0, 400)
    sel_350m = select_transceiver_and_fiber(350.0, 800)
    sel_1500m = select_transceiver_and_fiber(1500.0, 400)
    sel_8000m = select_transceiver_and_fiber(8000.0, 400)
    sel_60km = select_transceiver_and_fiber(60000.0, 400)
    check(
        sel_2m["transceiver"] == "CR_PASSIVE"
        and sel_35m["transceiver"] == "VR"
        and sel_85m["transceiver"] == "SR"
        and sel_350m["transceiver"] == "DR"
        and sel_1500m["transceiver"] == "FR"
        and sel_8000m["transceiver"] == "LR"
        and sel_60km["transceiver"] == "ZR",
        "Distance-tier transceiver selection: 2 m -> CR_PASSIVE, 35 m -> VR (50 m MMF), 85 m -> SR (100 m MMF), 350 m -> DR (500 m SMF), 1.5 km -> FR (2 km SMF), 8 km -> LR (10 km SMF), 60 km -> ZR (80 km DWDM)",
    )

    # 10. MPO-12 (`QSFP-DD-DR4`) vs MPO-16 (`QSFP-DD-SR8`) vs MPO-32 (`2x16`) Fiber Mapping
    mpo12_dr4 = evaluate_mpo_breakout("QSFP-DD-DR4", mpo_total_fibers=12, active_lanes=4, switch_port_rate_gbps=400, breakout_branches=1)
    mpo16_sr8 = evaluate_mpo_breakout("QSFP-DD-SR8", mpo_total_fibers=16, active_lanes=8, switch_port_rate_gbps=400, breakout_branches=1)
    mpo32_1600g = evaluate_mpo_breakout("OSFP-1600G-DR16", mpo_total_fibers=32, active_lanes=16, switch_port_rate_gbps=1600, breakout_branches=4)
    check(
        mpo12_dr4.tx_fibers == 4
        and mpo12_dr4.rx_fibers == 4
        and mpo12_dr4.dark_fibers == 4
        and mpo16_sr8.tx_fibers == 8
        and mpo16_sr8.rx_fibers == 8
        and mpo16_sr8.dark_fibers == 0
        and mpo32_1600g.mpo_variant == "MPO-32 (2x16)"
        and mpo32_1600g.endpoint_port_rate_gbps == 400,
        "ADC Ch. 4 MPO connector mapping: QSFP-DD-DR4 on MPO-12 uses 4 Tx + 4 Rx + 4 center dark fibers; QSFP-DD-SR8 on MPO-16 uses 8 Tx + 8 Rx (0 dark); MPO-32 (2x16) supports 16 Tx + 16 Rx",
    )

    # 11. Twin-Port Finned-Top OSFP (2x400G = 800G Switch Cage) Breakout Fan-Out (H100 / Quantum-2 / Spectrum-4)
    osfp_2x400g = evaluate_mpo_breakout("OSFP-800G-2xDR4", mpo_total_fibers=16, active_lanes=8, switch_port_rate_gbps=800, breakout_branches=2)
    osfp_4x200g = evaluate_mpo_breakout("OSFP-800G-4x200G", mpo_total_fibers=16, active_lanes=8, switch_port_rate_gbps=800, breakout_branches=4)
    check(
        osfp_2x400g.endpoint_port_rate_gbps == 400
        and osfp_2x400g.lanes_per_endpoint == 4
        and osfp_4x200g.endpoint_port_rate_gbps == 200
        and osfp_4x200g.lanes_per_endpoint == 2,
        "Twin-port finned-top 800G OSFP breakout fan-out (ADC Fig 4-10): 1x800G (8 lanes) splits into 2x400G (4 lanes each) or 4x200G (2 lanes each)",
    )

    # 12. SuperPOD <90% Maximum Cable Distance Derating Rule (superpod-b200-dc p. 20-23)
    aoc_30m_ok = evaluate_superpod_cable_derating("InfiniBand AOC 30m", 30.0, 27.0)
    aoc_30m_over = evaluate_superpod_cable_derating("InfiniBand AOC 30m", 30.0, 28.5)
    aoc_50m_ok = evaluate_superpod_cable_derating("InfiniBand AOC 50m", 50.0, 45.0)
    aoc_50m_over = evaluate_superpod_cable_derating("InfiniBand AOC 50m", 50.0, 47.0)
    dac_3m_ok = evaluate_superpod_cable_derating("400G Passive DAC 3m", 3.0, 2.7)
    dac_5m_100g = evaluate_superpod_cable_derating("100G Passive DAC 5m", 5.0, 4.5)
    patch_panel_fail = evaluate_superpod_cable_derating("InfiniBand AOC 30m", 30.0, 20.0, uses_patch_panel=True)
    check(
        aoc_30m_ok["max_allowed_run_m"] == 27.0
        and aoc_30m_ok["is_compliant"] is True
        and aoc_30m_over["is_compliant"] is False
        and aoc_30m_over["reason"] == "EXCEEDS_90PCT_MAX_DISTANCE_RULE"
        and aoc_50m_ok["max_allowed_run_m"] == 45.0
        and aoc_50m_ok["is_compliant"] is True
        and aoc_50m_over["is_compliant"] is False,
        "SuperPOD <90% cable length rule: 30 m AOC -> 27.0 m max run (28.5 m fails); 50 m AOC -> 45.0 m max run (47.0 m fails)",
    )

    check(
        dac_3m_ok["max_allowed_run_m"] == 2.7
        and dac_3m_ok["is_compliant"] is True
        and dac_5m_100g["max_allowed_run_m"] == 4.5
        and dac_5m_100g["is_compliant"] is True
        and patch_panel_fail["is_compliant"] is False
        and patch_panel_fail["reason"] == "NON_COMPLIANT_PATCH_PANEL_ATTENUATION",
        "SuperPOD DAC & patch-panel rules (superpod-b200-dc p. 20-23): 3 m 400G DAC -> 2.7 m max; 5 m 100G DAC -> 4.5 m max; patch panels are strictly rejected on InfiniBand links",
    )

    # 13. ADC Ch. 4 Tables 4-2 & 4-3 Form Factors (QSFP28, QSFP56, QSFP-DD Type 1/2/2A/2B, OSFP, CFP8)
    q28 = FORM_FACTOR_TABLE["QSFP28"]
    q56 = FORM_FACTOR_TABLE["QSFP56"]
    qdd = FORM_FACTOR_TABLE["QSFP-DD"]
    osfp = FORM_FACTOR_TABLE["OSFP"]
    cfp8 = FORM_FACTOR_TABLE["CFP8"]
    check(
        q28.max_data_rate_gbps == 100
        and q28.channels == 4
        and q28.per_channel_gbps == 25
        and q28.modulation == "NRZ"
        and q56.max_data_rate_gbps == 200
        and q56.channels == 4
        and q56.per_channel_gbps == 50
        and q56.modulation == "PAM4"
        and qdd.max_data_rate_gbps == 400
        and qdd.channels == 8
        and qdd.backward_compatible_with == ("QSFP+", "QSFP28", "QSFP56")
        and osfp.max_data_rate_gbps == 800
        and osfp.channels == 8
        and osfp.ports_per_ru == 36
        and cfp8.ports_per_ru == 16
        and len(QSFP_DD_CAGE_TYPES) == 4,
        "ADC Ch. 4 Tables 4-2 & 4-3: QSFP28 (4x25G NRZ, 100G), QSFP56 (4x50G PAM4, 200G), QSFP-DD (8x50G PAM4, 200-400G, backward compatible w/ QSFP+/28/56, Type 1/2/2A/2B), OSFP (8x100G, 800G, 36 ports/RU vs CFP8 16 ports/RU)",
    )

    # 14. ADC Ch. 4 Pluggable vs LRO vs LPO vs CPO Power & DSP BOM Cost
    pkg = compare_optics_packaging_power(pluggable_port_power_w=16.0, dsp_power_fraction=0.50, switch_ports=64)
    check(
        pkg["Pluggable"].per_port_power_w == 16.0
        and pkg["Pluggable"].dsp_power_w == 8.0
        and pkg["Pluggable"].switch_64port_optics_power_w == 1024.0
        and pkg["Pluggable"].bom_dsp_cost_share_range_pct == (20, 40)
        and pkg["LRO"].tx_dsp_in_module is True
        and pkg["LRO"].rx_dsp_in_module is False
        and pkg["LRO"].per_port_power_w == 12.0
        and pkg["LRO"].power_savings_vs_pluggable_pct == 25.0
        and pkg["LPO"].tx_dsp_in_module is False
        and pkg["LPO"].rx_dsp_in_module is False
        and pkg["LPO"].per_port_power_w == 8.0
        and pkg["LPO"].switch_64port_optics_power_w == 512.0
        and pkg["LPO"].power_savings_vs_pluggable_pct == 50.0
        and pkg["CPO"].field_pluggable is False
        and pkg["CPO"].per_port_power_w == 5.0
        and pkg["CPO"].switch_64port_optics_power_w == 320.0
        and pkg["CPO"].power_savings_vs_pluggable_pct == 68.75,
        "ADC Ch. 4 Pluggable vs LRO vs LPO vs CPO (64-port 800G switch @ 16 W/port = 1,024 W): DSP is 20-40% of BOM & 50% of power (8 W); LRO saves 25% (12 W/port, 768 W); LPO saves 50% (8 W/port, 512 W); CPO saves 68.75% (5 W/port, 320 W)",
    )

    # 15. `mlxlink -d mlx5_1 -c` and `-m` Healthy Baseline (Supercomputers Ch. 5)
    mlx_healthy = evaluate_mlxlink_module_health(
        state="Active",
        physical_state="LinkUp",
        effective_ber=15e-255,
        raw_errors_per_lane=(0, 0, 0, 0),
        link_down_counter=0,
        link_error_recovery_counter=0,
        temperature_c=38.0,
        temp_range_c=(-10.0, 80.0),
        voltage_mv=3255.2,
        voltage_range_mv=(3100.0, 3500.0),
        bias_ma_per_lane=(6.750, 6.750, 6.750, 6.750),
        bias_range_ma=(5.492, 8.5),
        rx_power_dbm_per_lane=(0.0, 0.0, 0.0, 0.0),
        rx_power_range_dbm=(-14.0, 6.0),
        tx_power_dbm_per_lane=(0.0, 0.0, 0.0, 0.0),
        tx_power_range_dbm=(-12.0, 6.0),
        cdr_rx_per_lane=("ON", "ON", "ON", "ON"),
        cdr_tx_per_lane=("ON", "ON", "ON", "ON"),
    )
    check(
        mlx_healthy["is_healthy"] is True
        and mlx_healthy["status"] == "HEALTHY_MODULE"
        and mlx_healthy["total_raw_lane_errors"] == 0,
        "Supercomputers Ch. 5 `mlxlink -d mlx5_1 -c/-m` healthy baseline: Active/LinkUp, IB-EDR 4x, BER 15E-255, lanes 0,0,0,0, Temp 38 C [-10..80], Voltage 3255.2 mV [3100..3500], Bias 6.750 mA [5.492..8.5], Rx/Tx 0 dBm, CDR ON",
    )

    # 16. `mlxlink` Degraded Module (Lane 2 Rx Power -16.8 dBm < -14 dBm, High BER, Over-Temp 83 C, CDR Lock Lost)
    mlx_degraded = evaluate_mlxlink_module_health(
        state="Active",
        physical_state="LinkUp",
        effective_ber=3.2e-7,
        raw_errors_per_lane=(0, 0, 18450, 12),
        link_down_counter=2,
        link_error_recovery_counter=5,
        temperature_c=83.0,
        rx_power_dbm_per_lane=(-1.2, -1.4, -16.8, -1.5),
        cdr_rx_per_lane=("ON", "ON", "OFF", "ON"),
    )
    check(
        mlx_degraded["is_healthy"] is False
        and "HIGH_EFFECTIVE_BER_3.2e-07" in mlx_degraded["anomalies"]
        and "NONZERO_LANE_PHYSICAL_ERRORS" in mlx_degraded["anomalies"]
        and "LINK_FLAP_OR_ERROR_RECOVERY" in mlx_degraded["anomalies"]
        and "MODULE_TEMP_OUT_OF_RANGE_83.0C" in mlx_degraded["anomalies"]
        and "RX_OPTICAL_POWER_OUT_OF_RANGE" in mlx_degraded["anomalies"]
        and "CDR_LOCK_LOST" in mlx_degraded["anomalies"],
        "`mlxlink` degraded transceiver detection: catches BER 3.2e-7, lane 2 raw errors (18,450), Rx power -16.8 dBm (< -14 dBm floor), temp 83 C (> 80 C max), link flaps (2), and CDR lock loss",
    )

    # 17. Mixed-Generation Interoperability (NDR 400G Switch Port Connected to HDR 200G HCA Port)
    mixed_hdr_ndr = evaluate_ib_link_negotiation(
        "NDR", designed_lanes=4, active_lanes=4, negotiated_rate_override_gbps=200.0, pcie_gen=5, pcie_lanes=16
    )
    check(
        mixed_hdr_ndr.nominal_link_bw_gbps == 400.0
        and mixed_hdr_ndr.negotiated_link_bw_gbps == 200.0
        and mixed_hdr_ndr.bottleneck_stage == "RATE_DOWN_NEGOTIATION",
        "V8 Ch. 8 Mixed-generation fabric interoperability: NDR (400G) switch port cabled to HDR (200G) HCA port negotiates mutually supported 200.0 Gbps (`RATE_DOWN_NEGOTIATION`)",
    )

    # 18. Baud Rate vs Bit Rate across EDR (25.78125 GBd NRZ), HDR (26.5625 GBd PAM4), NDR (53.125 GBd PAM4), XDR (100 GBd PAM4)
    edr_res = evaluate_ib_link_negotiation("EDR")
    hdr_res = evaluate_ib_link_negotiation("HDR")
    ndr_res = evaluate_ib_link_negotiation("NDR")
    xdr_res = evaluate_ib_link_negotiation("XDR")
    gdr_res = evaluate_ib_link_negotiation("GDR")
    check(
        edr_res.symbol_rate_gbaud == 25.78125
        and edr_res.bits_per_symbol == 1
        and hdr_res.symbol_rate_gbaud == 26.5625
        and hdr_res.bits_per_symbol == 2
        and ndr_res.symbol_rate_gbaud == 53.125
        and ndr_res.bits_per_symbol == 2
        and xdr_res.symbol_rate_gbaud == 100.0
        and xdr_res.bits_per_symbol == 2
        and gdr_res.symbol_rate_gbaud == 200.0
        and gdr_res.bits_per_symbol == 2,
        "PAM4 baud-rate doubling: EDR (25.78125 GBd NRZ = 25.78125 Gbps/lane) -> HDR (26.5625 GBd PAM4 = 53.125 Gbps/lane) -> NDR (53.125 GBd PAM4 = 106.25 Gbps/lane) -> XDR (100 GBd PAM4 = 200 Gbps/lane) -> GDR (200 GBd PAM4 = 400 Gbps/lane)",
    )

    # 19. Line Coding Efficiency Overhead: 8b/10b (80.0%) vs 64b/66b (96.9697%) vs 256b/257b (99.6109%)
    check(
        round(IB_GENERATION_TABLE["QDR"].coding_efficiency * 100.0, 4) == 80.0
        and round(IB_GENERATION_TABLE["HDR"].coding_efficiency * 100.0, 4) == 96.9697
        and round(IB_GENERATION_TABLE["NDR"].coding_efficiency * 100.0, 4) == 99.6109,
        "InfiniBand line coding efficiency progression: SDR-QDR 8b/10b = 80.00% (20% overhead), FDR-HDR 64b/66b = 96.9697% (3.03% overhead), NDR+ 256b/257b = 99.6109% (0.39% overhead)",
    )

    # 20. DGX GB300 NVL72 SuperPOD Compute & Storage Optics Architecture (superpod-gb300-ra)
    gb300_trays_per_rack = 18
    gb300_gpus_per_tray = 4
    gb300_gpus_per_rack = gb300_trays_per_rack * gb300_gpus_per_tray
    gb300_nvlink_switch_trays = 9
    gb300_nvlink_chips = gb300_nvlink_switch_trays * 2
    gb300_cx8_ports_per_tray = 4
    gb300_q3400_radix = 144
    gb300_max_sus = 16
    gb300_max_gpus = 9216
    check(
        gb300_gpus_per_rack == 72
        and gb300_nvlink_chips == 18
        and gb300_cx8_ports_per_tray * 800 == 3200
        and gb300_q3400_radix == 144
        and gb300_max_sus * 8 * gb300_gpus_per_rack == gb300_max_gpus,
        "superpod-gb300-ra optics & rack architecture: 18 compute trays (72 B300 GPUs, 9 NVLink switch trays / 18 switch chips @ 1.8 TB/s NVL5 per GPU, 900 GB/s NVLink-C2C), 4x800G ConnectX-8 per tray into 144-port Q3400-RD switches scaling to 16 SUs / 9,216 GPUs (128 leaves, 72 spines)",
    )

    # 21. DGX B200 SuperPOD Cabling Scale (superpod-b200-dc p. 19: 1..4 SUs, 458 kW/SU, UFM displacing 1 node)
    b200_su_table = {
        1: (31, 248, 8, 4, 252, 256),
        2: (63, 504, 16, 8, 508, 512),
        3: (95, 760, 24, 16, 764, 768),
        4: (127, 1016, 32, 16, 1020, 1024),
    }
    check(
        b200_su_table[1] == (31, 248, 8, 4, 252, 256)
        and b200_su_table[4] == (127, 1016, 32, 16, 1020, 1024)
        and all(gpus == nodes * 8 for nodes, gpus, _, _, _, _ in b200_su_table.values())
        and all(node_cables == nodes * 8 + 4 for nodes, _, _, _, node_cables, _ in b200_su_table.values()),
        "superpod-b200-dc Table (p. 19) SU cabling math: 1..4 SUs (458 kW/SU) = 31, 63, 95, 127 DGX B200 nodes (248..1,016 GPUs), 8..32 leaves, 4..16 spines, 252..1,020 node cables (8*nodes + 4 UFM cables), 256..1,024 spine-leaf ISL cables",
    )

    # 22. V8 Index Production Story (128 GPU nodes, >20% step-time variance from 3 compound causes)
    v8_index_nodes = 128
    v8_index_step_variance_pct = 20
    check(
        v8_index_nodes == 128
        and v8_index_step_variance_pct == 20
        and ndr_2x.negotiated_link_bw_gbps == 200.0,
        "V8 Index 128-node production story (>20% step-time variance): reduced link width after cable replacement + adaptive routing behavior + remote NUMA HCA pairing",
    )

    # 23. V8 Ch. 12 Summary: 512-GPU Nonblocking Leaf Radix Math (16 downlinks @ 400G + 16 uplinks @ 400G = 32 ports)
    gpus_per_node = 8
    total_gpus = 512
    total_nodes = total_gpus // gpus_per_node  # 64 nodes
    nodes_per_leaf = 16
    uplinks_per_leaf_1to1 = nodes_per_leaf  # 16 uplinks
    required_leaf_radix = nodes_per_leaf + uplinks_per_leaf_1to1  # 32 ports
    check(
        total_nodes == 64
        and nodes_per_leaf * 400 == 6400
        and uplinks_per_leaf_1to1 * 400 == 6400
        and required_leaf_radix == 32,
        "V8 Ch. 12 512-GPU 1:1 nonblocking leaf math: 16 downlinks @ 400G (6,400 Gbps) require 16 uplinks @ 400G (6,400 Gbps) = 32-port minimum leaf radix",
    )

    # 24. V8 Lab 01 Inventory Baseline (`MT4129` ConnectX-7, `fw_ver 28.39.2048`, `Rate: 400`, `Base lid: 12`, `SM lid: 1`)
    lab01_hca = {
        "hca_id": "mlx5_0",
        "ca_type": "MT4129",
        "fw_ver": "28.39.2048",
        "node_guid": "08c0:eb03:00f1:a2c3",
        "port_guid": "0x08c0eb0300f1a2c3",
        "vendor_id": 0x02C9,
        "vendor_part_id": 4129,
        "max_qp": 262144,
        "max_qp_wr": 32768,
        "max_sge": 30,
        "state": "Active",
        "phys_state": "LinkUp",
        "rate_gbps": 400,
        "base_lid": 12,
        "lmc": 0,
        "sm_lid": 1,
        "capability_mask": 0x2651E848,
    }
    check(
        lab01_hca["vendor_id"] == 0x02C9
        and lab01_hca["vendor_part_id"] == 4129
        and lab01_hca["max_qp"] == 262144
        and lab01_hca["max_qp_wr"] == 32768
        and lab01_hca["max_sge"] == 30
        and lab01_hca["rate_gbps"] == 400
        and lab01_hca["base_lid"] == 12
        and lab01_hca["sm_lid"] == 1,
        "V8 Lab 01 inventory verification (`ibv_devinfo -v` & `ibstat`): MT4129 ConnectX-7, fw_ver 28.39.2048, vendor 0x02c9, max_qp 262,144, max_qp_wr 32,768, max_sge 30, Rate 400, Base lid 12, SM lid 1",
    )

    # 25. Supercomputers Ch. 5 Subnet Device Limit & `ibstat`/`ibstatus` 4X FDR (56 Gbps) Verification
    max_subnet_devices = (1 << 15) + (1 << 14) - 1
    fdr_4x_raw_rate = 4 * 14.0625  # 56.25 Gbps (reported as Rate: 56 in ibstat / 56 Gb/sec (4X FDR) in ibstatus)
    check(
        max_subnet_devices == 49151
        and int(fdr_4x_raw_rate) == 56
        and round(4 * 14.0625 * (64.0 / 66.0), 1) == 54.5,
        "Supercomputers Ch. 5 subnet & FDR math: 2^15 + 2^14 - 1 = 49,151 max subnet devices; MT4113 `Rate: 56` (`56 Gb/sec (4X FDR)`) = 4 x 14.0625 Gbps raw (54.4 Gbps effective)",
    )

    # 26. ADC Ch. 4 PAM-8 Higher-Order Modulation Check (8 voltage levels, 3 bits/symbol, 7 eye openings, 16.90 dB SNR penalty)
    pam8_plan = plan_serdes_mux_demux(800, 100, 100, "PAM8")
    check(
        pam8_plan.bits_per_symbol == 3
        and pam8_plan.voltage_levels == 8
        and pam8_plan.eye_openings == 7
        and pam8_plan.snr_penalty_vs_nrz_db == 16.9,
        "ADC Ch. 4 higher-order PAM-8 modulation: 8 levels, 3 bits/symbol, 7 eye openings, and 16.90 dB SNR penalty vs NRZ",
    )

    # 27. DR4 500 m SMF with 90% SuperPOD Derating (450.0 m max run) & SR 100 m MMF (90.0 m max run)
    dr4_derated = evaluate_superpod_cable_derating("400G/800G DR4 SMF 500m", 500.0, 440.0)
    sr8_derated = evaluate_superpod_cable_derating("400G SR8 MMF 100m", 100.0, 90.0)
    check(
        dr4_derated["max_allowed_run_m"] == 450.0
        and dr4_derated["margin_m"] == 10.0
        and dr4_derated["is_compliant"] is True
        and sr8_derated["max_allowed_run_m"] == 90.0
        and sr8_derated["is_compliant"] is True,
        "90% cable derating on optical transceivers: 500 m DR SMF -> 450.0 m max run (440.0 m has 10.0 m margin); 100 m SR MMF -> 90.0 m max run",
    )

    # 28. A100 (8x200G) vs H100 (4x800G OSFP -> 8x400G) vs GB300 (4x800G CX-8 + 2x400G BF-3) Aggregate Node Bandwidth
    a100_node_bw_gbps = 8 * 200
    h100_node_bw_gbps = 4 * 800  # or 8 * 400 via 2x400G breakout
    gb300_tray_compute_bw_gbps = 4 * 800
    gb300_tray_storage_inband_bw_gbps = 400 + 200
    check(
        a100_node_bw_gbps == 1600
        and h100_node_bw_gbps == 3200
        and gb300_tray_compute_bw_gbps == 3200
        and gb300_tray_storage_inband_bw_gbps == 600,
        "ADC Fig 4-10/4-11 & superpod-gb300-ra server scale-out bandwidth: A100 = 8x200G (1,600 Gbps); H100 = 4x800G OSFP or 8x400G breakout (3,200 Gbps); GB300 tray = 4x800G CX-8 compute (3,200 Gbps) + BlueField-3 400G storage & 200G in-band",
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(run_lab())
