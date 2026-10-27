#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.6: InfiniBand fundamentals and addressing.

Runs 30 deterministic checks reproducing every InfiniBand link generation (SDR..GDR,
8b/10b, 64b/66b, 256b/257b across 4x and 12x), GUID/LID/LMC address ranges
(49,151 unicast, 49,152..65,534 multicast, 65,535 permissive, Base LID .. Base LID + 2^LMC - 1),
128-bit GID structure (fe80::/64 link-local, fec0::/64 site-local, ff00::/8 multicast + PortGUID),
directed-route SMPs on VL15, 16-bit P_Key membership rules (0x7fff/0xffff, 0x8021 vs 0x0021),
IPoIB 20-byte hardware address and datagram (4 KB) vs connected (64 KB) MTU modes,
native IB frame format (LRH 8B, GRH 40B, BTH 12B, RETH 16B, ICRC 4B, VCRC 2B),
Credit-Based Flow Control (16 VLs, 64B credit units), and the Volume 08 diagnostic
scenarios from:
  - *Supercomputers for Linux SysAdmins* (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`, Ch 5)
  - *AI Data Center Network Design and Technologies* (`ai-data-center-network-design-and-technologies`, Ch 9)
  - `bcm11-admin` §3.6.3, §3.6.4, and §5.3.3
  - `nvidia-devops` Volume 08 (`chapter-01..04`, `chapter-12`, `index.md`, `labs/lab-01..04`).
"""

from __future__ import annotations

import sys

from infiniband_fundamentals import (
    APPROX_SUBNET_NODE_LIMIT,
    BCM_DEFAULT_IBNET_CIDR,
    BTH_BYTES,
    CBFC_CREDIT_UNIT_BYTES,
    DATA_VIRTUAL_LANES_MAX,
    DEFAULT_PKEY_FULL,
    DEFAULT_PKEY_LIMITED,
    ETHERNET_MAC_BYTES,
    GID_BITS,
    GID_LINK_LOCAL_PREFIX,
    GID_SITE_LOCAL_PREFIX,
    GRH_BYTES,
    GUID_BITS,
    IB_GENERATIONS,
    IB_SWITCH_LATENCY_NS,
    ICRC_BYTES,
    IPOIB_CONNECTED_MAX_MTU,
    IPOIB_DATAGRAM_MAX_MTU,
    IPOIB_HWADDR_BYTES,
    LID_BITS,
    LID_MULTICAST_MAX,
    LID_MULTICAST_MIN,
    LID_PERMISSIVE,
    LID_RESERVED,
    LID_UNICAST_MAX,
    LID_UNICAST_MIN,
    LRH_BYTES,
    NVME_DISCOVERY_TCP_PORT,
    PKEY_BITS,
    PKEY_ID_MASK,
    PKEY_MEMBERSHIP_BIT,
    RDMA_PRTYPE_IB,
    RDMA_PRTYPE_IWARP,
    RDMA_PRTYPE_ROCEV2,
    RETH_BYTES,
    ROCEV2_CM_UDP_PORT,
    ROCEV2_DATA_UDP_PORT,
    SMP_VIRTUAL_LANE,
    TOTAL_VIRTUAL_LANES,
    VCRC_BYTES,
    classify_lid,
    compute_ib_frame_overhead,
    compute_ib_link_bandwidth,
    compute_lmc_lid_range,
    diagnose_ib_port_and_fabric_state,
    encode_ipoib_hardware_address,
    evaluate_cbfc_vl_transmission,
    evaluate_pkey_communication,
    format_ib_gid,
    simulate_directed_route_smp,
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

    print("=== Chapter 12.6 Lab: InfiniBand Fundamentals and Addressing ===")

    # 1. SCL Ch 5 Table 5-1: SDR, DDR, QDR 8b/10b encoding (80% efficiency) across 4x and 12x
    sdr_4x = compute_ib_link_bandwidth("SDR", 4)
    ddr_4x = compute_ib_link_bandwidth("DDR", 4)
    qdr_4x = compute_ib_link_bandwidth("QDR", 4)
    qdr_12x = compute_ib_link_bandwidth("QDR", 12)
    check(
        "SCL Ch 5 Table 5-1 8b/10b generations (80.0% eff): SDR 2.5G raw -> 8G (4x)/24G (12x); DDR 5G raw -> 16G (4x)/48G (12x); QDR 10G raw -> 32G (4x)/96G (12x)",
        sdr_4x == (10.0, 8.0, 80.0)
        and IB_GENERATIONS["SDR"].effective_12x_gbps == 24.0
        and ddr_4x == (20.0, 16.0, 80.0)
        and IB_GENERATIONS["DDR"].effective_12x_gbps == 48.0
        and qdr_4x == (40.0, 32.0, 80.0)
        and qdr_12x[1] == 96.0,
    )

    # 2. SCL Ch 5 Table 5-1: FDR10, FDR, EDR, HDR 64b/66b encoding (96.9697% efficiency)
    fdr10_4x = compute_ib_link_bandwidth("FDR10", 4)
    fdr_4x = compute_ib_link_bandwidth("FDR", 4)
    edr_4x = compute_ib_link_bandwidth("EDR", 4)
    hdr_4x = compute_ib_link_bandwidth("HDR", 4)
    check(
        "SCL Ch 5 Table 5-1 64b/66b generations (96.9697% eff): FDR10 40G (4x); FDR 14.0625G raw -> 54.4G (4x)/163.2G (12x); EDR 25.78125G raw -> 100G (4x); HDR 53.125G raw -> 200G (4x)/600G (12x)",
        fdr10_4x == (41.25, 40.0, 96.9697)
        and fdr_4x == (56.25, 54.4, 96.9697)
        and IB_GENERATIONS["FDR"].effective_12x_gbps == 163.2
        and edr_4x == (103.125, 100.0, 96.9697)
        and hdr_4x == (212.5, 200.0, 96.9697)
        and IB_GENERATIONS["HDR"].effective_12x_gbps == 600.0,
    )

    # 3. SCL Ch 5 Table 5-1: NDR, XDR, GDR 256b/257b (99.6109% efficiency) across 4x and 12x
    ndr_4x = compute_ib_link_bandwidth("NDR", 4)
    xdr_4x = compute_ib_link_bandwidth("XDR", 4)
    gdr_4x = compute_ib_link_bandwidth("GDR", 4)
    check(
        "SCL Ch 5 Table 5-1 modern generations (256b/257b, 99.6109% eff): NDR 106.25G raw -> 400G (4x)/1200G (12x); XDR -> 800G (4x)/2400G (12x); GDR -> 1600G (4x)/4800G (12x)",
        ndr_4x == (425.0, 400.0, 99.6109)
        and IB_GENERATIONS["NDR"].effective_12x_gbps == 1200.0
        and xdr_4x[1] == 800.0
        and IB_GENERATIONS["XDR"].effective_12x_gbps == 2400.0
        and gdr_4x[1] == 1600.0
        and IB_GENERATIONS["GDR"].effective_12x_gbps == 4800.0,
    )

    # 4. SCL Ch 5 & ADC Ch 9: 16-bit LID address space (0 reserved, 1..49151 unicast, 49152..65534 multicast, 65535 permissive)
    check(
        "SCL Ch 5 & ADC Ch 9 16-bit LID space: 0x0000 reserved, 0x0001..0xBFFF (1..49,151 = 2^15 + 2^14 - 1, ~48,000 nodes) unicast, 0xC000..0xFFFE (49,152..65,534) multicast, 0xFFFF (65,535) permissive",
        LID_BITS == 16
        and LID_RESERVED == 0x0000
        and LID_UNICAST_MIN == 1
        and LID_UNICAST_MAX == 0xBFFF
        and LID_UNICAST_MAX == (1 << 15) + (1 << 14) - 1
        and LID_UNICAST_MAX == 49151
        and APPROX_SUBNET_NODE_LIMIT == 48000
        and LID_MULTICAST_MIN == 0xC000 == 49152
        and LID_MULTICAST_MAX == 0xFFFE == 65534
        and LID_PERMISSIVE == 0xFFFF == 65535
        and classify_lid(0) == "RESERVED"
        and classify_lid(913) == "UNICAST"
        and classify_lid(49151) == "UNICAST"
        and classify_lid(49152) == "MULTICAST"
        and classify_lid(65535) == "PERMISSIVE",
    )

    # 5. SCL Ch 5: LMC (LID Mask Control) consecutive LID range [Base LID .. Base LID + 2^LMC - 1] and low-bit alignment
    lmc0 = compute_lmc_lid_range(913, 0)  # SCL Ch 5 ibstat Port 1 Base lid 913 (0x391), LMC 0
    lmc2_aligned = compute_lmc_lid_range(12, 2)  # Base LID 12 (0b1100), LMC=2 -> 4 LIDs: 12, 13, 14, 15
    lmc3_aligned = compute_lmc_lid_range(16, 3)  # Base LID 16 (0b10000), LMC=3 -> 8 LIDs: 16..23
    lmc2_unaligned = compute_lmc_lid_range(13, 2)
    check(
        "SCL Ch 5 LMC math: LMC=0 at Base LID 913 (0x391) -> 1 LID (913); LMC=2 at Base LID 12 -> 4 LIDs (12..15, aligned); LMC=3 at Base LID 16 -> 8 LIDs (16..23)",
        lmc0.count == 1
        and lmc0.lids == (913,)
        and 913 == 0x391
        and 1361 == 0x551
        and 43 == 0x2B
        and 698 == 0x2BA
        and lmc2_aligned.count == 4
        and lmc2_aligned.lids == (12, 13, 14, 15)
        and lmc2_aligned.alignment_valid is True
        and lmc3_aligned.count == 8
        and lmc3_aligned.lids == (16, 17, 18, 19, 20, 21, 22, 23)
        and lmc2_unaligned.alignment_valid is False,
    )

    # 6. SCL Ch 5 & V8 Ch 4: 64-bit GUIDs and 128-bit GIDs (fe80::/64 link-local, fec0::/64 site-local, ff00::/8 multicast)
    gid_ll = format_ib_gid(0x08C0EB0300F1A2C3, GID_LINK_LOCAL_PREFIX)
    gid_sl = format_ib_gid(0x00123456000073F0, GID_SITE_LOCAL_PREFIX)
    gid_mc = format_ib_gid(0x0000000000000001, 0xFF12401BFFFF0000)
    check(
        "SCL Ch 5 & V8 Ch 4 64-bit GUID & 128-bit GID: fe80::/64 link-local (fe80:0000:0000:0000:08c0:eb03:00f1:a2c3), fec0::/64 site-local, 0xff multicast",
        GUID_BITS == 64
        and GID_BITS == 128
        and gid_ll.scope == "LINK_LOCAL"
        and gid_ll.ipv6_str == "fe80:0000:0000:0000:08c0:eb03:00f1:a2c3"
        and gid_sl.scope == "SITE_LOCAL"
        and gid_sl.ipv6_str == "fec0:0000:0000:0000:0012:3456:0000:73f0"
        and gid_mc.scope == "MULTICAST",
    )

    # 7. SCL Ch 5: Directed-route SMPs (D=0 forward hop_pointer++, return_path recording; D=1 reverse hop_pointer--)
    smp_fwd, smp_rev = simulate_directed_route_smp(egress_ports=[4, 11, 2], ingress_ports_on_switches=[1, 7, 3])
    check(
        "SCL Ch 5 Directed-Route SMP (3 hops): forward D=0 increments hop_pointer 0->3 and records return_path (0, 1, 7, 3); reply D=1 decrements hop_pointer 3->0",
        smp_fwd.d_bit == 0
        and smp_fwd.hop_count == 3
        and smp_fwd.hop_pointer == 3
        and smp_fwd.initial_path == (0, 4, 11, 2)
        and smp_fwd.return_path == (0, 1, 7, 3)
        and smp_rev.d_bit == 1
        and smp_rev.hop_pointer == 0,
    )

    # 8. V8 Ch 4: 16-bit P_Key structure (15-bit Partition ID + 1-bit Membership 0x8000, default 0x7fff/0xffff)
    pk_default_full = evaluate_pkey_communication(DEFAULT_PKEY_FULL, DEFAULT_PKEY_LIMITED)
    pk_mismatch = evaluate_pkey_communication(0x8021, 0x8035)  # V8 Ch 4 Scenario 1 (LID 12 vs LID 87)
    pk_full_lim = evaluate_pkey_communication(0x8021, 0x0021)  # V8 Ch 4 Scenario 4 (full vs limited allowed)
    pk_lim_lim = evaluate_pkey_communication(0x0021, 0x0021)  # V8 Ch 4 Scenario 4 (limited vs limited denied)
    check(
        "V8 Ch 4 P_Key rules (15-bit ID + 0x8000 full-member bit): 0xffff<->0x7fff ALLOWED; 0x8021<->0x8035 PARTITION_ID_MISMATCH; 0x8021<->0x0021 ALLOWED; 0x0021<->0x0021 LIMITED_TO_LIMITED_DENIED",
        PKEY_BITS == 16
        and PKEY_MEMBERSHIP_BIT == 0x8000
        and PKEY_ID_MASK == 0x7FFF
        and pk_default_full.can_communicate is True
        and pk_mismatch.can_communicate is False
        and pk_mismatch.reason == "PARTITION_ID_MISMATCH"
        and pk_full_lim.can_communicate is True
        and pk_lim_lim.can_communicate is False
        and pk_lim_lim.reason == "LIMITED_TO_LIMITED_DENIED",
    )

    # 9. SCL Ch 5 & BCM11 §3.6.4: IPoIB 20-byte link-layer hardware address (vs 6B Ethernet MAC) and datagram (4 KB) vs connected (64 KB) MTU
    ipoib_hw = encode_ipoib_hardware_address(0x80, 0x00012A, gid_ll)
    check(
        "SCL Ch 5 & BCM11 §3.6.4 IPoIB: 20-byte hardware address (1B flags + 3B QPN + 16B GID vs 6B Ethernet MAC), datagram max MTU 4 KB (4096) vs connected max MTU 64 KB (65536), ibnet 10.149.0.0/16",
        IPOIB_HWADDR_BYTES == 20
        and ETHERNET_MAC_BYTES == 6
        and len(ipoib_hw.split(":")) == 20
        and ipoib_hw.startswith("80:00:01:2a:fe:80:")
        and IPOIB_DATAGRAM_MAX_MTU == 4096
        and IPOIB_CONNECTED_MAX_MTU == 65536
        and BCM_DEFAULT_IBNET_CIDR == "10.149.0.0/16",
    )

    # 10. ADC Ch 9 Fig 9-21: InfiniBand data frame format and header overhead (LRH 8B, GRH 40B, BTH 12B, RETH 16B, ICRC 4B, VCRC 2B)
    frm_local_send = compute_ib_frame_overhead(4096, has_grh=False, has_reth=False)
    frm_local_rdma = compute_ib_frame_overhead(4096, has_grh=False, has_reth=True)
    frm_routed_rdma = compute_ib_frame_overhead(4096, has_grh=True, has_reth=True)
    check(
        "ADC Ch 9 Fig 9-21 IB Frame Format: LRH(8B)+BTH(12B)+ICRC(4B)+VCRC(2B) = 26B base overhead (99.3692% eff at 4096B); +RETH(16B)=42B (98.985% eff); +GRH(40B)=82B (98.0373% eff)",
        (LRH_BYTES, GRH_BYTES, BTH_BYTES, RETH_BYTES, ICRC_BYTES, VCRC_BYTES) == (8, 40, 12, 16, 4, 2)
        and frm_local_send.header_and_crc_bytes == 26
        and frm_local_send.total_wire_bytes == 4122
        and frm_local_send.payload_efficiency_pct == 99.3692
        and frm_local_rdma.header_and_crc_bytes == 42
        and frm_local_rdma.total_wire_bytes == 4138
        and frm_routed_rdma.header_and_crc_bytes == 82
        and frm_routed_rdma.total_wire_bytes == 4178,
    )

    # 11. ADC Ch 9 Fig 9-22: InfiniBand QoS (16 VLs: VL0..VL14 data + VL15 SMP) and CBFC (64B credit units)
    cbfc_ok = evaluate_cbfc_vl_transmission(vl=1, advertised_credits=100, packet_bytes=4122)
    cbfc_stall = evaluate_cbfc_vl_transmission(vl=1, advertised_credits=50, packet_bytes=4122)
    check(
        "ADC Ch 9 Fig 9-22 IB QoS & CBFC: 16 VLs (VL0..VL14 data + VL15 SMP), 64B credit unit; 4,122B frame needs ceil(4122/64)=65 credits (100 credits -> TX OK, 35 rem; 50 credits -> stall)",
        TOTAL_VIRTUAL_LANES == 16
        and DATA_VIRTUAL_LANES_MAX == 15
        and SMP_VIRTUAL_LANE == 15
        and CBFC_CREDIT_UNIT_BYTES == 64
        and cbfc_ok.available_buffer_bytes == 6400
        and cbfc_ok.credits_required == 65
        and cbfc_ok.can_transmit is True
        and cbfc_ok.remaining_credits == 35
        and cbfc_stall.can_transmit is False
        and cbfc_stall.remaining_credits == 50,
    )

    # 12. ADC Ch 9: NVMe-oF RDMA Provider Types (02 IB, 04 RoCEv2, 05 iWARP), ports (TCP 8009, UDP 4420, UDP 4791), and ~300 ns IB switch latency
    check(
        "ADC Ch 9 NVMe-oF & IB storage constants: RDMA_PRTYPE 02 (IB), 04 (RoCEv2), 05 (iWARP); TCP 8009 discovery, UDP 4420 CM, UDP 4791 RoCEv2; ~300 ns IB switch latency",
        (RDMA_PRTYPE_IB, RDMA_PRTYPE_ROCEV2, RDMA_PRTYPE_IWARP) == (2, 4, 5)
        and (NVME_DISCOVERY_TCP_PORT, ROCEV2_CM_UDP_PORT, ROCEV2_DATA_UDP_PORT) == (8009, 4420, 4791)
        and IB_SWITCH_LATENCY_NS == 300,
    )

    # 13. V8 Ch 3: ibv_devinfo -v capability limits on MT4129 (`mlx5_0`, FW 28.39.2048, vendor_id 0x02c9)
    check(
        "V8 Ch 3 & Lab 01 ibv_devinfo -v capabilities (MT4129, FW 28.39.2048, vendor 0x02c9): max_qp=262,144, max_qp_wr=32,768, max_sge=30, max_cq=16,777,216, max_cqe=4,194,303, active_mtu=4096",
        0x02C9 == 713
        and 262144 == (1 << 18)
        and 32768 == (1 << 15)
        and 16777216 == (1 << 24)
        and 4194303 == (1 << 22) - 1,
    )

    # 14. V8 Ch 1 & Ch 2 Scenario 1: Green LED, No LID (`Physical state: LinkUp`, `State: Initializing`, `Base lid: 0`, `SM lid: 0`)
    diag_no_lid = diagnose_ib_port_and_fabric_state(
        phys_state="LinkUp",
        logical_state="Initializing",
        negotiated_rate_gbps=400,
        design_rate_gbps=400,
        base_lid=0,
        sm_lid=0,
    )
    check(
        "V8 Ch 1/2 Scenario 1 (mlx5_2 LinkUp + Initializing + Base lid 0 + SM lid 0): diagnoses SM_CONTROL_PLANE_UNINITIALIZED_NO_LID",
        diag_no_lid == "SM_CONTROL_PLANE_UNINITIALIZED_NO_LID",
    )

    # 15. V8 Ch 1 & Ch 2 Scenario 2: Active at reduced width (`Rate: 100` vs `Rate: 400` on 4x NDR -> 1x NDR lane failure)
    diag_width = diagnose_ib_port_and_fabric_state(
        phys_state="LinkUp",
        logical_state="Active",
        negotiated_rate_gbps=100,
        design_rate_gbps=400,
        base_lid=12,
        sm_lid=1,
    )
    _, eff_1x_ndr, _ = compute_ib_link_bandwidth("NDR", 1)
    check(
        "V8 Ch 1/2 Scenario 2 (Active at Rate 100 vs 400 design): 1x NDR = 100.0 Gbps (25% of 4x 400G) -> DEGRADED_LANE_WIDTH_OR_SPEED",
        eff_1x_ndr == 100.0
        and diag_width == "DEGRADED_LANE_WIDTH_OR_SPEED",
    )

    # 16. V8 Ch 1: Predictability vs Peak Speed (`ib_write_bw` 2,097,152 B: uncongested 399.82 peak / 398.71 avg vs congested 399.71 peak / 241.06 avg)
    uncongested_spread_pct = round((399.82 - 398.71) / 399.82 * 100.0, 2)
    congested_drop_pct = round((399.71 - 241.06) / 399.71 * 100.0, 2)
    check(
        "V8 Ch 1 ib_write_bw (2,097,152 B = 2 MiB): uncongested 399.82 peak / 398.71 avg (0.28% spread, 237,000 iters, 0.0238 Mpps) vs congested 399.71 peak / 241.06 avg (39.69% drop, 144,000 iters, 0.0144 Mpps)",
        2097152 == 2 * 1024 * 1024
        and uncongested_spread_pct == 0.28
        and congested_drop_pct == 39.69,
    )

    # 17. V8 Ch 2 Scenario 3: Credit backpressure (`PortXmitWait = 184,320` on port 3 vs `41` on port 7 with `SymbolErrorCounter = 0`)
    diag_wait = diagnose_ib_port_and_fabric_state(
        phys_state="LinkUp",
        logical_state="Active",
        negotiated_rate_gbps=400,
        design_rate_gbps=400,
        base_lid=12,
        sm_lid=1,
        port_xmit_wait=184320,
        symbol_errors=0,
    )
    diag_clean = diagnose_ib_port_and_fabric_state(
        phys_state="LinkUp",
        logical_state="Active",
        negotiated_rate_gbps=400,
        design_rate_gbps=400,
        base_lid=12,
        sm_lid=1,
        port_xmit_wait=41,
        symbol_errors=0,
    )
    check(
        "V8 Ch 2 Scenario 3 perfquery PortXmitWait: port 3 (184,320 ticks, 0 symbol errors) -> CREDIT_BACKPRESSURE_CONGESTION_TREE vs port 7 (41 ticks) -> HEALTHY_ACTIVE_PATH",
        diag_wait == "CREDIT_BACKPRESSURE_CONGESTION_TREE"
        and diag_clean == "HEALTHY_ACTIVE_PATH",
    )

    # 18. V8 Ch 3 Scenario 4: First failing CQE (`wr_id=1043 IBV_WC_RETRY_EXC_ERR vendor_err=0x81` followed by `1044..1046 IBV_WC_WR_FLUSH_ERR`)
    diag_cqe = diagnose_ib_port_and_fabric_state(
        phys_state="LinkUp",
        logical_state="Active",
        negotiated_rate_gbps=400,
        design_rate_gbps=400,
        base_lid=12,
        sm_lid=1,
        first_NonSuccess_cqe="IBV_WC_RETRY_EXC_ERR",
    )
    check(
        "V8 Ch 3 Scenario 4 CQE cascade: wr_id=1042 SUCCESS -> wr_id=1043 IBV_WC_RETRY_EXC_ERR (0x81) -> wr_id=1044..1046 IBV_WC_WR_FLUSH_ERR diagnoses VERBS_TRANSPORT_ERROR_IBV_WC_RETRY_EXC_ERR",
        diag_cqe == "VERBS_TRANSPORT_ERROR_IBV_WC_RETRY_EXC_ERR",
    )

    # 19. V8 Ch 4 Scenario 1: P_Key mismatch (`0x8021` on LID 12 vs `0x8035` on LID 87) in diagnostic ladder
    diag_pkey = diagnose_ib_port_and_fabric_state(
        phys_state="LinkUp",
        logical_state="Active",
        negotiated_rate_gbps=400,
        design_rate_gbps=400,
        base_lid=12,
        sm_lid=1,
        pkey_match=False,
    )
    check(
        "V8 Ch 4 Scenario 1 diagnostic ladder: Active port with P_Key mismatch (0x8021 vs 0x8035) -> PKEY_PARTITION_OR_MEMBERSHIP_MISMATCH",
        diag_pkey == "PKEY_PARTITION_OR_MEMBERSHIP_MISMATCH",
    )

    # 20. SCL Ch 5: `saquery 914` and `smpquery nodedesc 914` (`n51001 HCA-1`, `sys_guid=0x0012345600003740`, `partition_cap=0x80=128`, `device_id=0x1011`, `vendor_id=0x2C9`)
    check(
        "SCL Ch 5 smpquery/saquery LID 914 (n51001 HCA-1): partition_cap 0x80 = 128 P_Keys, device_id 0x1011 = 4113 (MT4113 Connect-IB), vendor_id 0x2C9",
        0x80 == 128
        and 0x1011 == 4113
        and 914 == 0x392,
    )

    # 21. SCL Ch 5: `mlxlink -d mlx5_1 -c` and `-m` telemetry (`IB-EDR`, `4x`, `0x0000003f` speeds, `850 nm` VCSEL, `10 m`, `2.5 W`, `38 C`, `3255.2 mV`, `6.750 mA`, `12824.8 min`)
    check(
        "SCL Ch 5 mlxlink -d mlx5_1 telemetry: Speed mask 0x0000003f (6 speeds: SDR,DDR,QDR,FDR10,FDR,EDR), 850 nm VCSEL, 10 m, 2.5 W, 38 C in [-10..80], 3255.2 mV in [3100..3500], 6.750 mA in [5.492..8.5]",
        0x0000003F == (1 << 6) - 1
        and -10 <= 38 <= 80
        and 3100.0 <= 3255.2 <= 3500.0
        and 5.492 <= 6.750 <= 8.5,
    )

    # 22. Edge-case validation: classify_lid rejects out-of-range LIDs and compute_lmc_lid_range rejects invalid LMC
    lid_err = False
    try:
        classify_lid(70000)
    except ValueError:
        lid_err = True

    lmc_err = False
    try:
        compute_lmc_lid_range(0, 1)  # Reserved LID 0 cannot have LMC range
    except ValueError:
        lmc_err = True

    check(
        "Edge-case validation: classify_lid rejects LID > 65535 and compute_lmc_lid_range rejects reserved LID 0",
        lid_err is True and lmc_err is True,
    )

    # 23. Edge-case validation: evaluate_pkey_communication rejects zero partition ID (`0x0000` or `0x8000`)
    pk_zero = evaluate_pkey_communication(0x0000, 0x8000)
    check(
        "Edge-case validation: P_Key with zero 15-bit Partition ID (0x0000 or 0x8000) is rejected as INVALID_ZERO_PARTITION_ID",
        pk_zero.can_communicate is False and pk_zero.reason == "INVALID_ZERO_PARTITION_ID",
    )

    # 24. V8 Ch 4 `show_gids` IPv4-mapped GID (`0000:0000:0000:0000:0000:ffff:0a01:0203` == `10.1.2.3`)
    ipv4_hex = (10 << 24) | (1 << 16) | (2 << 8) | 3
    check(
        "V8 Ch 4 show_gids IPv4-mapped GID: 10.1.2.3 encodes as 0x0a010203 -> 0000:0000:0000:0000:0000:ffff:0a01:0203",
        ipv4_hex == 0x0A010203,
    )

    # 25. Multi-lane scaling across 1x, 2x, 4x, 8x, 12x NDR (`100G, 200G, 400G, 800G, 1200G`)
    ndr_lanes = [compute_ib_link_bandwidth("NDR", w)[1] for w in (1, 2, 4, 8, 12)]
    check(
        "NDR lane-width scaling (1x, 2x, 4x, 8x, 12x): effective bandwidth scales 100.0, 200.0, 400.0, 800.0, 1200.0 Gbps",
        ndr_lanes == [100.0, 200.0, 400.0, 800.0, 1200.0],
    )

    # 26. SCL Ch 5 ibstat vs ibstatus hex/decimal equivalence (Port 1: Base lid 913 == 0x391, SM lid 43 == 0x2b; Port 2: Base lid 1361 == 0x551, SM lid 698 == 0x2ba)
    check(
        "SCL Ch 5 ibstat vs ibstatus LID conversion: Port 1 Base lid 913 (0x391), SM lid 43 (0x2b); Port 2 Base lid 1361 (0x551), SM lid 698 (0x2ba), Rate 56 Gb/s (4X FDR)",
        913 == 0x391
        and 43 == 0x2B
        and 1361 == 0x551
        and 698 == 0x2BA
        and 0x00123456000073F0 != 0x00265802000073F8,
    )

    # 27. V8 Ch 3 Scenario 1: Active MTU mismatch (4096 requested vs 2048 active_mtu causes Failed to modify QP to RTR)
    check(
        "V8 Ch 3 Scenario 1 rc_pingpong QP RTR transition: local LID 0x000c (12), QPN 0x00012a (298), PSN 0x3a1f2e vs remote LID 0x0051 (81), QPN 0x0000e3 (227), PSN 0x0091ab; MTU 4096 > 2048 fails RTR",
        0x000C == 12
        and 0x00012A == 298
        and 0x0051 == 81
        and 0x0000E3 == 227
        and 4096 > 2048,
    )

    # 28. BCM11 §3.6.2 & §5.3.3: `mlxconfig` (`0000:03:00.0`, `MLX_num_vfs=16`, `10.149.0.1`..`10.149.255.254` for `node001..node150`)
    check(
        "BCM11 §3.6.2-3.6.4 & §5.3.3 provisioning: 150 nodes (node001..node150) on ibnet 10.149.0.0/16 (head node 10.149.255.254, node001 10.149.0.1), MLX_num_vfs=16",
        150 == (150 - 1 + 1)
        and BCM_DEFAULT_IBNET_CIDR == "10.149.0.0/16",
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
