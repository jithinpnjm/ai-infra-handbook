#!/usr/bin/env python3
"""Self-checking verification lab for Chapter 12.22: AI network telemetry and KPIs.

Runs 30 deterministic checks covering:
  - ADC Ch. 10 AI Data Center KPIs & MLCommons / MLPerf benchmarking:
    * Model vs data KPIs, numeric precision byte widths (`1, 2, 4, 8, 16, 32` bytes), and
      OpenAI ChatGPT training scale (`1,023` A100 GPUs in `34` days)
    * Strong vs weak scaling speedup and efficiency (`128 -> 1,024` GPUs, `8.0x` scale factor)
    * JCT communication fraction and collective tail-latency amplification (`100,000` steps,
      `120 ms` compute + `30 ms -> 90 ms` collective tail stall = `1.40x` JCT slowdown, `17,066.67`
      wasted GPU-hours on `1,024` GPUs)
    * Power and efficiency KPIs (`PUE = Total Facility Power / IT Equipment Power`, `FLOPS/Watt`,
      `Throughput/Watt`, `QPS/Watt`)
    * MLCommons (`2020`, `MLPerf`, `MLCube`, `PAIR`), `MLPerf Training` / `Inference` / `Storage`
      suites, `Closed` vs `Open` divisions, and `LoadGen` `Offline` vs `Server` (Poisson arrival)
      validation
  - ADC Ch. 11 Network Monitoring, In-Band Flow Analyzer (`IFA`), and Corrective Actions:
    * `draft-kumar-ippm-ifa-08` packet header sequence (`L2 -> L3 -> IFA Header -> L4 -> IFA Metadata
      Header -> IFA Metadata Stack -> Payload`), `4`-byte (`32`-bit) IFA Header field layout, and
      `32`-byte (`256`-bit, `8 x 32-bit` rows) per-hop IFA Metadata Stack layout
    * `3`-stage (`104` B overhead) and `5`-stage (`168` B overhead) Clos fabric IFA trace analysis,
      per-hop residence time (`tx_ns - rx_ns`) + wire propagation latency, ECN congestion-bit gating,
      and `IPFIX` export from the `Terminator` leaf
  - `nvidia-devops` Volume 08 (`Ch. 9`, `Ch. 12`, `index.md`, `Labs 01-04`), Volume 09, and Legacy Volume 07:
    * State vs cumulative counters vs rates/deltas (`SymbolErrorCounter` `12,034 -> 12,034` over
      `300 s` historical scar tissue vs `Day 1: 4 -> Day 4: 890 [+886, 295.33/day] -> Day 7: 41,200
      [+40,310, 13,436.67/day, 45.5x acceleration]` with `LinkDownedCounter: 0 -> 3 -> 11`)
    * InfiniBand `PortXmitWait` credit backpressure (`port 3` `998,432` or `184,320` vs `41` on
      `port 7` with `SymbolErrorCounter = 0`), `PortXmitDiscards` (`10 -> 260`), and `PortXmitData`
      `4`-octet words (`5,368,709,120` words = `21,474,836,480` B vs `268,435,456` words =
      `1,073,741,824` B `20:1` spine imbalance)
    * RoCEv2 ECN / CNP / PFC storm / FEC correlation (`swp9` `312` ECN marks vs `298` CNPs healthy
      loop, `Lab 03` `47,829` ECN marks / `412` RX PFC / `14` TX PFC, `swp3` relay hop `41,823` RX /
      `41,810` TX PFC vs `swp7` `2,200` ECN marks, weak RP `412,880` ECN / `93,100` PFC at `98 Gbps`,
      broken `0` CNP loop, and `swp17` `fec_uncorrected_blocks = 3 == rx_crc_errors = 3`)
    * Multi-rail bandwidth skew (`max/min` ratio across `8` rails; balanced `1.03x` vs degraded `1x`
      lane width `4.00x` skew and dead rail `inf` skew) and `1,000`-switch telemetry cardinality math.
"""

from __future__ import annotations

import sys

from ai_network_telemetry_kpis import (
    FABRIC_JUMBO_MTU_BYTES,
    IB_DATA_WORD_BYTES,
    IFA_3_STAGE_HOPS,
    IFA_5_STAGE_HOPS,
    IFA_HEADER_BYTES,
    IFA_HEADER_FIELD_BITS,
    IFA_METADATA_HEADER_BYTES,
    IFA_METADATA_STACK_ROW_BITS,
    IFA_PACKET_HEADER_SEQUENCE,
    IFA_PER_HOP_METADATA_BITS,
    IFA_PER_HOP_METADATA_BYTES,
    MLCOMMONS_FOUNDED_YEAR,
    MLCOMMONS_INITIATIVES,
    MLPERF_DIVISIONS,
    MLPERF_INFERENCE_DOMAINS,
    MLPERF_SUITES,
    NUMERIC_PRECISION_BYTES,
    OPENAI_CHATGPT_A100_GPUS,
    OPENAI_CHATGPT_TRAINING_DAYS,
    analyze_ifa_flow_trace,
    compute_jct_and_tail_latency_impact,
    compute_power_and_efficiency_kpis,
    compute_strong_and_weak_scaling,
    estimate_telemetry_scale_and_cardinality,
    evaluate_infiniband_port_telemetry,
    evaluate_mlperf_submission,
    evaluate_rail_bandwidth_skew,
    evaluate_rocev2_congestion_and_fec,
    evaluate_symbol_error_acceleration,
)


def main() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label}")

    print("=== Chapter 12.22 Lab: AI Network Telemetry and KPIs ===")

    # ------------------------------------------------------------------
    # Group 1: ADC Ch. 10 AI Data Center KPIs & MLCommons / MLPerf
    # ------------------------------------------------------------------
    check(
        "ADC Ch 10 Historical & Precision Constants: MLCommons founded 2020 (MLPerf, MLCube, PAIR), OpenAI ChatGPT 1,023 A100 GPUs in 34 days, precision bytes 1/2/4/8/16/32",
        MLCOMMONS_FOUNDED_YEAR == 2020
        and OPENAI_CHATGPT_A100_GPUS == 1023
        and OPENAI_CHATGPT_TRAINING_DAYS == 34
        and MLCOMMONS_INITIATIVES == ("MLPerf", "MLCube", "PAIR")
        and MLPERF_SUITES == ("MLPerf Training", "MLPerf Inference", "MLPerf Storage")
        and MLPERF_INFERENCE_DOMAINS == ("Data Center", "Edge", "Mobile", "Tiny")
        and tuple(NUMERIC_PRECISION_BYTES.values()) == (1, 2, 4, 8, 16, 32),
    )

    scaling_good = compute_strong_and_weak_scaling(
        base_gpus=128,
        scaled_gpus=1024,
        strong_base_time_s=800.0,
        strong_scaled_time_s=112.0,
        weak_base_step_time_s=0.450,
        weak_scaled_step_time_s=0.480,
    )
    check(
        "ADC Ch 10 Strong & Weak Scaling (128 -> 1,024 GPUs, 8.0x scale): strong speedup 7.1429x (89.29% eff), weak scaling 93.75% eff",
        scaling_good.scale_factor == 8.0
        and scaling_good.strong_speedup == 7.1429
        and scaling_good.strong_efficiency == 0.8929
        and scaling_good.weak_efficiency == 0.9375,
    )

    scaling_poor = compute_strong_and_weak_scaling(
        base_gpus=128,
        scaled_gpus=1024,
        strong_base_time_s=800.0,
        strong_scaled_time_s=200.0,
        weak_base_step_time_s=0.450,
        weak_scaled_step_time_s=0.750,
    )
    check(
        "ADC Ch 10 Network-Bottlenecked Scaling (128 -> 1,024 GPUs on 2:1 oversubscribed fabric): strong speedup 4.0x (50.0% eff), weak scaling 60.0% eff",
        scaling_poor.strong_speedup == 4.0
        and scaling_poor.strong_efficiency == 0.50
        and scaling_poor.weak_efficiency == 0.60,
    )

    jct_impact = compute_jct_and_tail_latency_impact(
        num_steps=100_000,
        compute_ms_per_step=120.0,
        ideal_comm_ms_per_step=30.0,
        degraded_comm_ms_per_step=90.0,
        non_overlapped_fraction=1.0,
        cluster_gpus=1024,
    )
    check(
        "ADC Ch 10 JCT & Tail-Latency Amplification (100,000 steps on 1,024 GPUs): 3.0x collective tail stall (30 -> 90 ms) inflates comm fraction 20.0% -> 42.86% and JCT 4.1667 -> 5.8333 h (1.40x slowdown, 1,706.67 wasted GPU-hours)",
        jct_impact.ideal_step_ms == 150.0
        and jct_impact.degraded_step_ms == 210.0
        and jct_impact.ideal_comm_fraction == 0.20
        and jct_impact.degraded_comm_fraction == 0.4286
        and jct_impact.comm_tail_inflation_ratio == 3.0
        and jct_impact.ideal_jct_hours == 4.1667
        and jct_impact.degraded_jct_hours == 5.8333
        and jct_impact.jct_slowdown_ratio == 1.40
        and jct_impact.wasted_gpu_hours == 1706.67,
    )

    pue_kpis = compute_power_and_efficiency_kpis(
        total_facility_power_kw=549.6,
        it_equipment_power_kw=458.0,
        achieved_tflops=229_000.0,
        samples_per_sec=18_320.0,
        queries_per_sec=91_600.0,
    )
    check(
        "ADC Ch 10 & App A Power & Efficiency KPIs (549.6 kW facility / 458.0 kW IT): PUE = 1.20, FPW = 500.0 GFLOPS/W IT (416.6667 GFLOPS/W facility), TPW = 0.04 samples/W, QPW = 0.20 QPS/W",
        pue_kpis.pue == 1.20
        and pue_kpis.gflops_per_watt_it == 500.0
        and pue_kpis.gflops_per_watt_facility == 416.6667
        and pue_kpis.tpw_samples_per_watt == 0.04
        and pue_kpis.qpw_queries_per_watt == 0.20,
    )

    mlperf_train = evaluate_mlperf_submission(
        suite="MLPerf Training",
        division="Closed",
        scenario="SingleStream-Training",
        achieved_accuracy=0.769,
        target_accuracy=0.768,
        primary_metric_value=14.25,
    )
    mlperf_offline = evaluate_mlperf_submission(
        suite="MLPerf Inference",
        division="Closed",
        scenario="Offline",
        achieved_accuracy=0.991,
        target_accuracy=0.990,
        primary_metric_value=38_400.0,
    )
    mlperf_server_pass = evaluate_mlperf_submission(
        suite="MLPerf Inference",
        division="Closed",
        scenario="Server",
        achieved_accuracy=0.991,
        target_accuracy=0.990,
        primary_metric_value=29_500.0,
        achieved_p99_latency_ms=14.2,
        target_p99_latency_ms=15.0,
    )
    mlperf_server_fail_sla = evaluate_mlperf_submission(
        suite="MLPerf Inference",
        division="Open",
        scenario="Server",
        achieved_accuracy=0.992,
        target_accuracy=0.990,
        primary_metric_value=34_000.0,
        achieved_p99_latency_ms=18.4,
        target_p99_latency_ms=15.0,
    )
    check(
        "ADC Ch 10 MLPerf Benchmarking Suites & LoadGen Scenarios: Closed/Open divisions, Training time-to-train, Inference Offline (all queries at once) vs Server (Poisson stream with p99 SLA)",
        "Closed" in MLPERF_DIVISIONS
        and "Open" in MLPERF_DIVISIONS
        and mlperf_train.valid_submission is True
        and mlperf_offline.valid_submission is True
        and mlperf_server_pass.valid_submission is True
        and mlperf_server_fail_sla.latency_sla_passed is False
        and mlperf_server_fail_sla.valid_submission is False,
    )

    # ------------------------------------------------------------------
    # Group 2: ADC Ch. 11 In-Band Flow Analyzer (IFA, draft-kumar-ippm-ifa-08)
    # ------------------------------------------------------------------
    check(
        "ADC Ch 11 Fig 11-2 & 11-3 IFA Header Format: L2 -> L3 -> IFA Header (32 bits = 4B: Ver 4b, Global NS 4b, Proto 8b, Flags 8b, MaxLen 8b) -> L4 -> IFA Metadata Header (4B) -> Stack -> Payload",
        IFA_PACKET_HEADER_SEQUENCE
        == (
            "L2 Header",
            "L3 Header",
            "IFA Header",
            "L4 Header",
            "IFA Metadata Header",
            "IFA Metadata Stack",
            "Payload",
        )
        and IFA_HEADER_FIELD_BITS
        == {
            "IFA_Version": 4,
            "Global_Namespace": 4,
            "Protocol_Type": 8,
            "Flags": 8,
            "Max_Length": 8,
        }
        and IFA_HEADER_BYTES == 4
        and IFA_METADATA_HEADER_BYTES == 4,
    )

    check(
        "ADC Ch 11 Fig 11-4 IFA Metadata Stack Format: 8 x 32-bit rows = 256 bits (32 bytes) per hop (Local NS 4b, Device ID 20b, TTL 8b, Speed 4b, Congestion 2b, Queue ID 6b, RX_s 20b, Ports 16b+16b, RX_ns 32b, Residence_ns 32b, Opaque 96b)",
        len(IFA_METADATA_STACK_ROW_BITS) == 8
        and all(sum(row[1].values()) == 32 for row in IFA_METADATA_STACK_ROW_BITS)
        and IFA_PER_HOP_METADATA_BITS == 256
        and IFA_PER_HOP_METADATA_BYTES == 32,
    )

    ifa_3stage = analyze_ifa_flow_trace(
        hops=[
            {
                "role": "Initiator",
                "device_id": 101,
                "rx_timestamp_ns": 1_000_000,
                "tx_timestamp_ns": 1_000_650,  # 650 ns residence
                "wire_propagation_ns": 150,
                "ecn_enabled_on_egress": True,
                "congestion_bits": 0,
            },
            {
                "role": "Transit",
                "device_id": 201,
                "rx_timestamp_ns": 1_000_800,
                "tx_timestamp_ns": 1_015_200,  # 14,400 ns (14.4 us) spine microburst queue delay
                "wire_propagation_ns": 150,
                "ecn_enabled_on_egress": True,
                "congestion_bits": 3,
            },
            {
                "role": "Terminator",
                "device_id": 102,
                "rx_timestamp_ns": 1_015_350,
                "tx_timestamp_ns": 1_016_050,  # 700 ns residence
                "wire_propagation_ns": 0,
                "ecn_enabled_on_egress": True,
                "congestion_bits": 0,
            },
        ],
        base_packet_bytes=4200,
        mtu_bytes=FABRIC_JUMBO_MTU_BYTES,
    )
    check(
        "ADC Ch 11 3-Stage Clos IFA Trace: 8B fixed + 3x32B stack = 104B overhead (4,304B <= 9,000B MTU), residence 15,750 ns + wire 300 ns = 16,050 ns (16.05 us), Transit Spine 201 isolated (14,400 ns), exported via IPFIX",
        ifa_3stage.hop_count == IFA_3_STAGE_HOPS
        and ifa_3stage.ifa_fixed_headers_bytes == 8
        and ifa_3stage.ifa_metadata_stack_bytes == 96
        and ifa_3stage.total_ifa_overhead_bytes == 104
        and ifa_3stage.tagged_packet_bytes == 4304
        and ifa_3stage.fits_within_mtu is True
        and ifa_3stage.total_residence_time_ns == 15_750
        and ifa_3stage.total_wire_time_ns == 300
        and ifa_3stage.end_to_end_latency_ns == 16_050
        and ifa_3stage.end_to_end_latency_us == 16.05
        and ifa_3stage.bottleneck_device_id == 201
        and ifa_3stage.bottleneck_role == "Transit"
        and ifa_3stage.bottleneck_residence_ns == 14_400
        and ifa_3stage.congested_hops == (201,)
        and ifa_3stage.collector_export_format == "IPFIX",
    )

    ifa_5stage = analyze_ifa_flow_trace(
        hops=[
            {"role": "Initiator", "device_id": 11, "rx_timestamp_ns": 0, "tx_timestamp_ns": 600, "wire_propagation_ns": 100, "ecn_enabled_on_egress": True, "congestion_bits": 0},
            {"role": "Transit", "device_id": 21, "rx_timestamp_ns": 700, "tx_timestamp_ns": 1400, "wire_propagation_ns": 200, "ecn_enabled_on_egress": True, "congestion_bits": 0},
            {"role": "Transit", "device_id": 31, "rx_timestamp_ns": 1600, "tx_timestamp_ns": 9600, "wire_propagation_ns": 200, "ecn_enabled_on_egress": False, "congestion_bits": 3},
            {"role": "Transit", "device_id": 22, "rx_timestamp_ns": 9800, "tx_timestamp_ns": 10500, "wire_propagation_ns": 100, "ecn_enabled_on_egress": True, "congestion_bits": 2},
            {"role": "Terminator", "device_id": 12, "rx_timestamp_ns": 10600, "tx_timestamp_ns": 11200, "wire_propagation_ns": 0, "ecn_enabled_on_egress": True, "congestion_bits": 0},
        ],
        base_packet_bytes=8900,
        mtu_bytes=FABRIC_JUMBO_MTU_BYTES,
    )
    check(
        "ADC Ch 11 5-Stage Clos IFA Trace & ECN Prerequisite: 8B + 5x32B = 168B overhead (8,900B + 168B = 9,068B > 9,000B MTU warning), hop 31 congestion bits ignored when ECN disabled on egress",
        ifa_5stage.hop_count == IFA_5_STAGE_HOPS
        and ifa_5stage.ifa_metadata_stack_bytes == 160
        and ifa_5stage.total_ifa_overhead_bytes == 168
        and ifa_5stage.tagged_packet_bytes == 9068
        and ifa_5stage.fits_within_mtu is False
        and ifa_5stage.bottleneck_device_id == 31
        and ifa_5stage.bottleneck_residence_ns == 8000
        and ifa_5stage.congested_hops == (22,),
    )

    # ------------------------------------------------------------------
    # Group 3: InfiniBand Telemetry, Counter Deltas & PortXmitWait (V8 Ch. 9, 12, Labs 01-04)
    # ------------------------------------------------------------------
    ib_scar = evaluate_infiniband_port_telemetry(
        port_label="sw-lid44-port9",
        window_s=300.0,
        xmit_data_words_t0=0,
        xmit_data_words_t1=5_368_709_120,  # 21,474,836,480 bytes
        xmit_pkts_t0=0,
        xmit_pkts_t1=5_242_880,
        xmit_wait_t0=100,
        xmit_wait_t1=140,
        symbol_err_t0=12_034,
        symbol_err_t1=12_034,
    )
    check(
        "V8 Ch 9 Scenario 1 Historical Scar Tissue (`perfquery <lid> 9` over 300s): SymbolErrorCounter 12,034 -> 12,034 (delta 0) with 21,474,836,480 B (57.2662 Gbps) classified as HISTORICAL_SCAR_TISSUE",
        ib_scar.xmit_bytes_delta == 21_474_836_480
        and ib_scar.symbol_error_delta == 0
        and ib_scar.classification == "HISTORICAL_SCAR_TISSUE"
        and ib_scar.alert_severity == "NONE",
    )

    ib_slow_fail = evaluate_symbol_error_acceleration(
        port_label="sw-lid44-port12",
        day1_errors=4,
        day4_errors=890,
        day7_errors=41_200,
        window1_days=3.0,
        window2_days=3.0,
        link_downed_total=11,
    )
    check(
        "V8 Ch 9 'The Fabric Failed Slowly' (`perfquery <switch-lid> 12`): Day 1 (4) -> Day 4 (890, +886 = 295.33/day) -> Day 7 (41,200, +40,310 = 13,436.67/day), 45.5x rate acceleration, LinkDowned=11",
        ib_slow_fail.window1_delta == 886
        and ib_slow_fail.window2_delta == 40_310
        and ib_slow_fail.window1_rate_per_day == 295.33
        and ib_slow_fail.window2_rate_per_day == 13_436.67
        and ib_slow_fail.acceleration_ratio == 45.50
        and ib_slow_fail.link_downed_total == 11
        and ib_slow_fail.alert_triggered is True,
    )

    ib_cong_port3 = evaluate_infiniband_port_telemetry(
        port_label="sw-lid44-port3",
        window_s=60.0,
        xmit_data_words_t0=0,
        xmit_data_words_t1=3_000_000_000,  # 12,000,000,000 B = 160 Gbps
        xmit_pkts_t0=0,
        xmit_pkts_t1=3_000_000,
        xmit_wait_t0=0,
        xmit_wait_t1=998_432,
        symbol_err_t0=0,
        symbol_err_t1=0,
        link_downed_t0=0,
        link_downed_t1=0,
    )
    ib_cong_port3_ch2 = evaluate_infiniband_port_telemetry(
        port_label="sw-lid44-port3-ch2",
        window_s=60.0,
        xmit_data_words_t0=0,
        xmit_data_words_t1=1_807_950_000,
        xmit_pkts_t0=0,
        xmit_pkts_t1=1_440_000,
        xmit_wait_t0=0,
        xmit_wait_t1=184_320,
        symbol_err_t0=0,
        symbol_err_t1=0,
    )
    ib_healthy_port7 = evaluate_infiniband_port_telemetry(
        port_label="sw-lid44-port7",
        window_s=60.0,
        xmit_data_words_t0=0,
        xmit_data_words_t1=2_990_000_000,
        xmit_pkts_t0=0,
        xmit_pkts_t1=2_370_000,
        xmit_wait_t0=0,
        xmit_wait_t1=41,
        symbol_err_t0=0,
        symbol_err_t1=0,
    )
    check(
        "V8 Ch 2, 7, 9, 10 & Lab 03 PortXmitWait Credit Backpressure: port 3 (998,432 and 184,320 wait ticks, 0 symbol errors) -> CREDIT_BACKPRESSURE_CONGESTION vs port 7 (41 ticks) -> HEALTHY_ACTIVE",
        ib_cong_port3.classification == "CREDIT_BACKPRESSURE_CONGESTION"
        and ib_cong_port3.wait_ticks_per_sec == 16_640.53
        and ib_cong_port3.wait_to_pkt_ratio == 0.3328
        and ib_cong_port3_ch2.classification == "CREDIT_BACKPRESSURE_CONGESTION"
        and ib_cong_port3_ch2.wait_ticks_per_sec == 3072.0
        and ib_healthy_port7.classification == "HEALTHY_ACTIVE",
    )

    ib_flap_port4 = evaluate_infiniband_port_telemetry(
        port_label="sw-lid44-port4",
        window_s=60.0,
        xmit_data_words_t0=0,
        xmit_data_words_t1=500_000_000,
        xmit_pkts_t0=0,
        xmit_pkts_t1=500_000,
        xmit_wait_t0=0,
        xmit_wait_t1=2109,
        symbol_err_t0=0,
        symbol_err_t1=41,
        link_downed_t0=0,
        link_downed_t1=2,
    )
    ib_discard_port11 = evaluate_infiniband_port_telemetry(
        port_label="sw-lid44-port11",
        window_s=60.0,
        xmit_data_words_t0=0,
        xmit_data_words_t1=100_000_000,
        xmit_pkts_t0=0,
        xmit_pkts_t1=100_000,
        xmit_wait_t0=0,
        xmit_wait_t1=12,
        symbol_err_t0=0,
        symbol_err_t1=0,
        xmit_discards_t0=10,
        xmit_discards_t1=260,
    )
    check(
        "V8 Ch 7 & Ch 9 Physical Flap vs Routing Discard: port 4 (SymbolError +41, LinkDowned +2) -> PHYSICAL_LINK_DEGRADATION vs port 11 (PortXmitDiscards +250) -> ROUTING_OR_POLICY_DISCARD",
        ib_flap_port4.classification == "PHYSICAL_LINK_DEGRADATION"
        and ib_flap_port4.alert_severity == "PAGE"
        and ib_discard_port11.classification == "ROUTING_OR_POLICY_DISCARD"
        and ib_discard_port11.xmit_discards_delta == 250,
    )

    ib_uplink_hot = evaluate_infiniband_port_telemetry(
        port_label="leaf1-uplink5",
        window_s=10.0,
        xmit_data_words_t0=0,
        xmit_data_words_t1=5_368_709_120,  # 21,474,836,480 B
        xmit_pkts_t0=0,
        xmit_pkts_t1=5_000_000,
        xmit_wait_t0=0,
        xmit_wait_t1=45_000,
        symbol_err_t0=0,
        symbol_err_t1=0,
    )
    ib_uplink_cold = evaluate_infiniband_port_telemetry(
        port_label="leaf1-uplink7",
        window_s=10.0,
        xmit_data_words_t0=0,
        xmit_data_words_t1=268_435_456,    # 1,073,741,824 B
        xmit_pkts_t0=0,
        xmit_pkts_t1=250_000,
        xmit_wait_t0=0,
        xmit_wait_t1=20,
        symbol_err_t0=0,
        symbol_err_t1=0,
    )
    check(
        "V8 Ch 6 & Lab 03 Spine Uplink Imbalance (`PortXmitData` 4-octet words): port 5 (21,474,836,480 B = 171.7987 Gbps) vs port 7 (1,073,741,824 B = 8.5899 Gbps) = 20.0x static route imbalance",
        IB_DATA_WORD_BYTES == 4
        and ib_uplink_hot.xmit_bytes_delta == 21_474_836_480
        and ib_uplink_cold.xmit_bytes_delta == 1_073_741_824
        and round(ib_uplink_hot.xmit_bytes_delta / ib_uplink_cold.xmit_bytes_delta, 1) == 20.0,
    )

    # ------------------------------------------------------------------
    # Group 4: RoCEv2 ECN / CNP / PFC Storm / FEC Triage (ADC Ch. 11, Ch. 2.31, V9)
    # ------------------------------------------------------------------
    roce_healthy_swp9 = evaluate_rocev2_congestion_and_fec(
        interface="swp9",
        window_s=5.0,
        rx_ecn_marked_delta=312,       # 84,200 -> 84,512
        np_cnp_sent_or_handled_delta=298,
        rx_pfc_pause_delta=0,
        tx_pfc_pause_delta=0,
        rp_current_rate_gbps=62.5,
        line_rate_gbps=100.0,
    )
    roce_lab03_contention = evaluate_rocev2_congestion_and_fec(
        interface="ens1f0",
        window_s=60.0,
        rx_ecn_marked_delta=47_829,
        np_cnp_sent_or_handled_delta=45_100,
        rx_pfc_pause_delta=412,
        tx_pfc_pause_delta=14,
        fec_corrected_delta=412,
        fec_uncorrected_delta=0,
        rp_current_rate_gbps=89.2,
        line_rate_gbps=400.0,
    )
    check(
        "RoCEv2 Proactive ECN Contained (`swp9` +312 ECN / +298 CNP, 0 PFC; `Lab 03` +47,829 ECN / 412 RX PFC / 14 TX PFC over 60s): classified as PROACTIVE_ECN_CONTAINED",
        roce_healthy_swp9.classification == "PROACTIVE_ECN_CONTAINED"
        and roce_healthy_swp9.cnp_to_ecn_ratio == 0.9551
        and roce_lab03_contention.classification == "PROACTIVE_ECN_CONTAINED"
        and roce_lab03_contention.pfc_pause_rate_per_sec == 6.87,
    )

    roce_relay_swp3 = evaluate_rocev2_congestion_and_fec(
        interface="swp3",
        window_s=10.0,
        rx_ecn_marked_delta=190,
        np_cnp_sent_or_handled_delta=180,
        rx_pfc_pause_delta=41_823,
        tx_pfc_pause_delta=41_810,
    )
    roce_weak_rp = evaluate_rocev2_congestion_and_fec(
        interface="swp9-weak-rp",
        window_s=60.0,
        rx_ecn_marked_delta=412_880,
        np_cnp_sent_or_handled_delta=409_500,
        rx_pfc_pause_delta=93_100,
        tx_pfc_pause_delta=0,
        rp_current_rate_gbps=98.0,
        line_rate_gbps=100.0,
    )
    roce_broken_cnp = evaluate_rocev2_congestion_and_fec(
        interface="swp12-no-cnp",
        window_s=10.0,
        rx_ecn_marked_delta=15_000,
        np_cnp_sent_or_handled_delta=0,
        rx_pfc_pause_delta=4200,
        tx_pfc_pause_delta=0,
    )
    roce_fec_corrupt = evaluate_rocev2_congestion_and_fec(
        interface="swp17",
        window_s=60.0,
        rx_ecn_marked_delta=1850,
        np_cnp_sent_or_handled_delta=1800,
        rx_pfc_pause_delta=0,
        tx_pfc_pause_delta=0,
        fec_corrected_delta=41_200,
        fec_uncorrected_delta=3,
        rx_crc_errors_delta=3,
    )
    roce_lossless_drop = evaluate_rocev2_congestion_and_fec(
        interface="swp19",
        window_s=10.0,
        rx_ecn_marked_delta=0,
        np_cnp_sent_or_handled_delta=0,
        rx_pfc_pause_delta=0,
        tx_pfc_pause_delta=0,
        lossless_queue_drops_delta=18_402,
    )
    check(
        "RoCEv2 Anomaly Detection: PFC_PAUSE_RELAY_HOP (`swp3` 41,823 RX / 41,810 TX), WEAK_RP_OR_PFC_STORM (412,880 ECN / 93,100 PFC @ 98 Gbps), BROKEN_DCQCN_CNP_LOOP (15,000 ECN / 0 CNP), PHYSICAL_FEC_CRC_CORRUPTION (`swp17` 3 uncorrected == 3 CRC), LOSSLESS_QUEUE_BUFFER_DROP (18,402 WJH drops)",
        roce_relay_swp3.classification == "PFC_PAUSE_RELAY_HOP"
        and roce_weak_rp.classification == "WEAK_RP_OR_PFC_STORM"
        and roce_broken_cnp.classification == "BROKEN_DCQCN_CNP_LOOP"
        and roce_fec_corrupt.classification == "PHYSICAL_FEC_CRC_CORRUPTION"
        and roce_lossless_drop.classification == "LOSSLESS_QUEUE_BUFFER_DROP",
    )

    # ------------------------------------------------------------------
    # Group 5: Multi-Rail Bandwidth Skew & Telemetry Scale / Cardinality
    # ------------------------------------------------------------------
    rails_balanced = evaluate_rail_bandwidth_skew(
        node_name="dgx-h100-01",
        rail_rates_gbps=[388.0, 392.0, 390.5, 385.0, 391.0, 389.0, 395.0, 387.5],
    )
    rails_warn = evaluate_rail_bandwidth_skew(
        node_name="dgx-h100-02",
        rail_rates_gbps=[390.0, 388.0, 392.0, 285.0, 389.0, 391.0, 387.0, 390.0],
    )
    rails_1x_degraded = evaluate_rail_bandwidth_skew(
        node_name="dgx-h100-03",
        rail_rates_gbps=[392.0, 390.0, 98.0, 388.0, 391.0, 389.0, 390.0, 387.0],
    )
    rails_idle_one_rail = evaluate_rail_bandwidth_skew(
        node_name="dgx-h100-04",
        rail_rates_gbps=[390.0, 388.0, 391.0, 389.0, 392.0, 0.0, 387.0, 390.0],
    )
    rails_idle_node = evaluate_rail_bandwidth_skew(
        node_name="dgx-h100-idle",
        rail_rates_gbps=[1.2, 0.4, 0.8, 1.1, 0.5, 0.9, 0.6, 1.0],
    )
    check(
        "Multi-Rail Bandwidth Skew (`max/min` across 8 rails, Ch. 2.31 & V8 Ch. 9 Scenario 3): balanced 1.026x -> BALANCED_RAILS, 1.3754x -> WARNING_RAIL_SKEW (>1.3), 1x lane fallback 4.00x (392/98 Gbps) & dead rail (inf) -> CRITICAL_RAIL_SKEW (>1.5), idle node (<40 Gbps) suppressed",
        rails_balanced.max_to_min_ratio == 1.026
        and rails_balanced.skew_status == "BALANCED_RAILS"
        and rails_warn.max_to_min_ratio == 1.3754
        and rails_warn.skew_status == "WARNING_RAIL_SKEW"
        and rails_1x_degraded.max_to_min_ratio == 4.0
        and rails_1x_degraded.skew_status == "CRITICAL_RAIL_SKEW"
        and rails_idle_one_rail.max_to_min_ratio == float("inf")
        and rails_idle_one_rail.skew_status == "CRITICAL_RAIL_SKEW"
        and rails_idle_node.skew_status == "IDLE_BELOW_LOAD_FLOOR",
    )

    scale_est = estimate_telemetry_scale_and_cardinality(
        num_switches=1000,
        ports_per_switch=64,
        queues_per_port=8,
        port_metrics_count=36,
        queue_metrics_count=8,
        sample_interval_s=10.0,
        distinct_5tuples_per_port=500,
    )
    check(
        "Streaming Telemetry Scale & Cardinality Math (1,000 switches x 64 ports x 100 counters @ 10s): 6,400 series/switch (640 samples/s/switch), 6,400,000 total series (640,000 samples/s), 500x cardinality explosion (3.2B series) if 5-tuples added to Prometheus",
        scale_est.active_series_per_switch == 6400
        and scale_est.total_active_series == 6_400_000
        and scale_est.samples_per_sec_per_switch == 640.0
        and scale_est.total_samples_per_sec == 640_000.0
        and scale_est.per_flow_high_cardinality_series == 3_200_000_000
        and scale_est.cardinality_explosion_multiplier == 500.0,
    )

    # ------------------------------------------------------------------
    # Group 6: V8 Lab 01-04 & Ch 10/12 End-to-End Baseline & Latency Verification
    # ------------------------------------------------------------------
    # V8 Ch 10 Step 6 ib_write_lat 2-byte 1000 iterations: typical 1.58 vs 1.55 us (1.0194x),
    # p99 2.90 vs 1.71 us (1.6959x), p99.9 5.77 vs 1.98 us (2.9141x)
    typ_ratio = round(1.58 / 1.55, 4)
    p99_ratio = round(2.90 / 1.71, 4)
    p999_ratio = round(5.77 / 1.98, 4)
    check(
        "V8 Ch 10 & Lab 02 `ib_write_lat` Tail-Latency Percentile Drift (2B, 1000 iters): typical 1.58 vs 1.55 us (1.0194x), p99 2.90 vs 1.71 us (1.6959x), p99.9 5.77 vs 1.98 us (2.9141x)",
        typ_ratio == 1.0194 and p99_ratio == 1.6959 and p999_ratio == 2.9141,
    )

    # V8 Ch 1 & Lab 02 ib_write_bw 2,097,152 B: uncongested peak 399.82 / avg 398.71 Gbps (0.28% spread)
    # vs congested peak 399.71 / avg 241.06 Gbps (39.69% drop)
    uncong_drop_pct = round((399.82 - 398.71) / 399.82 * 100.0, 2)
    cong_drop_pct = round((399.71 - 241.06) / 399.71 * 100.0, 2)
    check(
        "V8 Ch 1 & Lab 02 `ib_write_bw` Peak vs Average Spread (2,097,152 B): uncongested 399.82/398.71 Gbps (0.28% spread, 0.0238 Mpps) vs credit-congested 399.71/241.06 Gbps (39.69% drop, 0.0144 Mpps)",
        uncong_drop_pct == 0.28 and cong_drop_pct == 39.69,
    )

    # V8 Ch 6 & Lab 02 same-leaf vs 2:1 oversubscribed cross-rack ib_write_bw: 397.62 vs 201.18 Gbps
    # and 2 GB AllReduce 40 ms (at 50 GB/s) vs 80 ms (at 25 GB/s)
    check(
        "V8 Ch 6 & Ch 12 Leaf Oversubscription Impact (16x400G=6,400G down vs 8x400G=3,200G up = 2:1): cross-rack `ib_write_bw` drops 397.62 -> 201.18 Gbps (1.9764x) and 2 GB AllReduce doubles 40.0 -> 80.0 ms; 512-GPU nonblocking leaf requires 16 down + 16 up = 32 ports",
        round(397.62 / 201.18, 4) == 1.9764
        and (16 * 400) // (8 * 400) == 2
        and 16 + 16 == 32,
    )

    # V8 Ch 11 Shared vs Separated VL inference p99 latency: 1.8 ms -> 14.2 ms (7.89x) -> 3.1 ms
    check(
        "V8 Ch 11 Shared vs Separated Virtual Lane Inference Tail Latency: p99 spikes 1.8 ms -> 14.2 ms (7.8889x) when sharing VL with training/storage, restored to 3.1 ms on dedicated SL/VL",
        round(14.2 / 1.8, 4) == 7.8889 and round(14.2 / 3.1, 4) == 4.5806,
    )

    # V9 Lab 04 RoCEv2 device/rail misalignment: mlx5_0 392 Gbps in 2.1s vs mlx5_1 156 Gbps in 8.2s
    check(
        "V9 Lab 04 RoCEv2 Evidence Ladder (`mlx5_0` vs `mlx5_1`): 392.0 Gbps in 2.1s (0 retries) degrades to 156.0 Gbps in 8.2s (2.5128x slower, 3.9048x duration) with 24 RETRY_EXC_ERR and rx_ecn_marked_prio3=142",
        round(392.0 / 156.0, 4) == 2.5128 and round(8.2 / 2.1, 4) == 3.9048,
    )

    # ADC Ch 11 Historical linear trend: +10% bandwidth growth over 2 weeks from 65% utilization
    # reaches 85% threshold in 4 weeks (2 intervals of +10%)
    u0_pct = 65.0
    biweekly_growth_pct = 10.0
    weeks_to_85pct = ((85.0 - u0_pct) / biweekly_growth_pct) * 2.0
    check(
        "ADC Ch 11 Historical Trend Forecasting (+10% bandwidth utilization growth per 2 weeks): 65.0% baseline crosses 85.0% uplink threshold in 4.0 weeks",
        weeks_to_85pct == 4.0,
    )

    # Additional Exercise Verification Checks (Checks 25-30)
    ex1_jct = compute_jct_and_tail_latency_impact(
        num_steps=50_000,
        compute_ms_per_step=160.0,
        ideal_comm_ms_per_step=40.0,
        degraded_comm_ms_per_step=100.0,
        non_overlapped_fraction=1.0,
        cluster_gpus=512,
    )
    check(
        "Exercise 1 Verification (50,000 steps on 512 GPUs, 160 ms compute, 40 -> 100 ms comm): JCT rises 2.7778 -> 3.6111 h (1.30x slowdown, 426.67 wasted GPU-hours)",
        ex1_jct.ideal_jct_hours == 2.7778
        and ex1_jct.degraded_jct_hours == 3.6111
        and ex1_jct.jct_slowdown_ratio == 1.30
        and ex1_jct.wasted_gpu_hours == 426.67,
    )

    ex2_scale = compute_strong_and_weak_scaling(
        base_gpus=64,
        scaled_gpus=512,
        strong_base_time_s=640.0,
        strong_scaled_time_s=100.0,
        weak_base_step_time_s=0.500,
        weak_scaled_step_time_s=0.550,
    )
    check(
        "Exercise 2 Verification (64 -> 512 GPUs, 8.0x scale): strong speedup 6.40x (80.0% eff), weak scaling 90.91% eff",
        ex2_scale.scale_factor == 8.0
        and ex2_scale.strong_speedup == 6.40
        and ex2_scale.strong_efficiency == 0.80
        and ex2_scale.weak_efficiency == 0.9091,
    )

    ex3_ifa = analyze_ifa_flow_trace(
        hops=[
            {"role": "Initiator", "device_id": 10, "rx_timestamp_ns": 500, "tx_timestamp_ns": 1100, "wire_propagation_ns": 120, "ecn_enabled_on_egress": True, "congestion_bits": 0},
            {"role": "Transit", "device_id": 20, "rx_timestamp_ns": 1220, "tx_timestamp_ns": 19720, "wire_propagation_ns": 120, "ecn_enabled_on_egress": True, "congestion_bits": 3},
            {"role": "Terminator", "device_id": 30, "rx_timestamp_ns": 19840, "tx_timestamp_ns": 20440, "wire_propagation_ns": 0, "ecn_enabled_on_egress": True, "congestion_bits": 0},
        ],
        base_packet_bytes=4096,
        mtu_bytes=9000,
    )
    check(
        "Exercise 3 Verification (3-stage IFA on 4,096B packet): 104B overhead -> 4,200B packet, residence 19,700 ns + wire 240 ns = 19,940 ns (19.94 us), bottleneck Transit 20 (18,500 ns)",
        ex3_ifa.total_ifa_overhead_bytes == 104
        and ex3_ifa.tagged_packet_bytes == 4200
        and ex3_ifa.total_residence_time_ns == 19_700
        and ex3_ifa.total_wire_time_ns == 240
        and ex3_ifa.end_to_end_latency_ns == 19_940
        and ex3_ifa.bottleneck_device_id == 20
        and ex3_ifa.bottleneck_residence_ns == 18_500,
    )

    check(
        "Exercise 4 Verification (InfiniBand 4-port triage): port 9 SCAR_TISSUE, port 3 CREDIT_BACKPRESSURE, port 4 PHYSICAL_LINK_DEGRADATION, port 11 ROUTING_OR_POLICY_DISCARD",
        ib_scar.classification == "HISTORICAL_SCAR_TISSUE"
        and ib_cong_port3.classification == "CREDIT_BACKPRESSURE_CONGESTION"
        and ib_flap_port4.classification == "PHYSICAL_LINK_DEGRADATION"
        and ib_discard_port11.classification == "ROUTING_OR_POLICY_DISCARD",
    )

    check(
        "Exercise 5 Verification (RoCEv2 5-port triage): swp9 PROACTIVE_ECN_CONTAINED, swp3 PFC_PAUSE_RELAY_HOP, swp9-weak-rp WEAK_RP_OR_PFC_STORM, swp12-no-cnp BROKEN_DCQCN_CNP_LOOP, swp17 PHYSICAL_FEC_CRC_CORRUPTION",
        roce_healthy_swp9.classification == "PROACTIVE_ECN_CONTAINED"
        and roce_relay_swp3.classification == "PFC_PAUSE_RELAY_HOP"
        and roce_weak_rp.classification == "WEAK_RP_OR_PFC_STORM"
        and roce_broken_cnp.classification == "BROKEN_DCQCN_CNP_LOOP"
        and roce_fec_corrupt.classification == "PHYSICAL_FEC_CRC_CORRUPTION",
    )

    check(
        "Exercise 6 Verification (Rail skew & cardinality): 4.00x skew on 1x lane fallback, 6,400,000 series (640k samples/s) across 1,000 64-port switches",
        rails_1x_degraded.max_to_min_ratio == 4.0
        and scale_est.total_active_series == 6_400_000
        and scale_est.total_samples_per_sec == 640_000.0,
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
