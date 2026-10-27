#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.16: NCCL: topology, channels, transports and environment variables."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nccl_topology_channels_env import (
    NCCL_TRANSPORTS,
    TOPOLOGY_PATH_LEVELS,
    NCCLTopologyEnvError,
    calculate_channels_and_buffers,
    evaluate_500mb_nvlink_vs_sys_step,
    evaluate_numa_and_k8s_topology_manager,
    filter_nccl_interfaces,
    normalize_topo_label,
    parse_nccl_topo_xml,
    score_topology_path,
    select_nccl_transport,
    validate_socket_transport_limits,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}"
        if detail:
            msg += f" -> {detail}"
        print(msg)


def main() -> int:
    print("=== Chapter 12.16 Lab: NCCL Topology, Channels, Transports, and Environment Variables ===")

    # 1. NCCL Topology Path Cost Ordering (LOC < NVL < C2C < PIX < PXB < PHB < SYS)
    check(
        "All 7 NCCL topology path levels (LOC, NVL, C2C, PIX, PXB, PHB, SYS) are cataloged",
        set(TOPOLOGY_PATH_LEVELS.keys()) == {"LOC", "NVL", "C2C", "PIX", "PXB", "PHB", "SYS"},
    )
    check(
        "Strict NCCL topology path cost ordering: NVL (10) < C2C (15) < PIX (30) < PXB (50) < PHB (80) < SYS (200)",
        TOPOLOGY_PATH_LEVELS["NVL"].cost_weight
        < TOPOLOGY_PATH_LEVELS["C2C"].cost_weight
        < TOPOLOGY_PATH_LEVELS["PIX"].cost_weight
        < TOPOLOGY_PATH_LEVELS["PXB"].cost_weight
        < TOPOLOGY_PATH_LEVELS["PHB"].cost_weight
        < TOPOLOGY_PATH_LEVELS["SYS"].cost_weight,
    )
    check(
        "normalize_topo_label maps NV4, NV12, NV18 to NVL and X to LOC",
        normalize_topo_label("NV4") == "NVL"
        and normalize_topo_label("NV12") == "NVL"
        and normalize_topo_label("NV18") == "NVL"
        and normalize_topo_label("X") == "LOC",
    )
    path_cmp = score_topology_path("NV4", "SYS")
    check(
        "score_topology_path ranks NV4 (NVL, 900 GB/s) strictly faster than SYS (28 GB/s)",
        path_cmp["a_strictly_faster_than_b"] is True
        and path_cmp["bottleneck_level"] == "SYS"
        and path_cmp["bw_a_gbps"] == 900.0
        and path_cmp["bw_b_gbps"] == 28.0,
    )

    # 2. 500 MB NVLink vs SYS Transfer & ASP Ch 4 Table 4-2 Overlap/Topology Metrics
    step_500 = evaluate_500mb_nvlink_vs_sys_step()
    print(
        f"  [INFO] 500 MB transfer: NVLink (900 GB/s)={step_500['nvlink_time_ms']} ms vs "
        f"SYS (28 GB/s)={step_500['sys_time_ms']} ms ({step_500['sys_vs_nvlink_slowdown_x']}x slower); "
        f"Table 4-2 SM busy: {step_500['table_4_2_before_sm_busy_pct']}% -> {step_500['table_4_2_after_sm_busy_pct']}%, "
        f"iter time: {step_500['table_4_2_before_iter_ms']} ms -> {step_500['table_4_2_after_iter_ms']} ms"
    )
    check(
        "V2 Ch10: 500 MB (0.5 GB) transfer takes 0.56 ms on NVLink (900 GB/s) vs 17.86 ms (~18 ms, 32.14x slower) on SYS (28 GB/s)",
        step_500["nvlink_time_ms"] == 0.56
        and step_500["sys_time_ms"] == 17.86
        and step_500["sys_vs_nvlink_slowdown_x"] == 32.14,
    )
    check(
        "ASP Ch4 Table 4-2: Topology-aware + overlapped NCCL raises SM busy from 60% to 90% and cuts iteration time from 100 ms to 70 ms (-30%)",
        step_500["table_4_2_before_sm_busy_pct"] == 60.0
        and step_500["table_4_2_after_sm_busy_pct"] == 90.0
        and step_500["table_4_2_before_iter_ms"] == 100.0
        and step_500["table_4_2_after_iter_ms"] == 70.0
        and step_500["table_4_2_iter_reduction_pct"] == 30.0,
    )

    # 3. NCCL XML Topology Parser (`NCCL_TOPO_FILE` / `NCCL_TOPO_DUMP_FILE`)
    sample_xml = """<system version="1">
      <cpu numaid="0">
        <pci busid="0000:00:00.0">
          <pci busid="0000:01:00.0" class="0x060400">
            <gpu dev="0" sm="80" rank="0" gdr="1"/>
            <nic>
              <net name="mlx5_0" dev="0" speed="400000" port="1" gdr="1"/>
            </nic>
          </pci>
          <pci busid="0000:02:00.0" class="0x060400">
            <gpu dev="1" sm="80" rank="1" gdr="1"/>
          </pci>
        </pci>
      </cpu>
      <cpu numaid="1">
        <pci busid="0000:80:00.0">
          <pci busid="0000:81:00.0" class="0x060400">
            <gpu dev="2" sm="80" rank="2" gdr="1"/>
            <nic>
              <net name="mlx5_1" dev="1" speed="800000" port="1" gdr="1"/>
            </nic>
          </pci>
        </pci>
      </cpu>
    </system>"""
    topo_parsed = parse_nccl_topo_xml(sample_xml)
    paths = topo_parsed["gpu_nic_paths"]
    print(f"  [INFO] Parsed topology.xml GPU-to-NIC paths: {paths}")
    check(
        "V6 Ch2 & ASP Ch4: topology.xml parser identifies GPU0<->mlx5_0 as PIX (same switch 0000:01:00.0, 400000 Mbps / 800000 Mbps, gdr=1)",
        paths[(0, "mlx5_0")] == "PIX"
        and paths[(2, "mlx5_1")] == "PIX"
        and topo_parsed["nics"][0]["speed_mbps"] == 400000
        and topo_parsed["nics"][1]["speed_mbps"] == 800000,
    )
    check(
        "topology.xml parser identifies GPU1<->mlx5_0 as PXB (same root 0000:00:00.0, different switch) and GPU0<->mlx5_1 as SYS (cross NUMA 0->1)",
        paths[(1, "mlx5_0")] == "PXB"
        and paths[(0, "mlx5_1")] == "SYS"
        and paths[(2, "mlx5_0")] == "SYS",
    )

    # 4. Channel Count Calculation, SM Block Consumption, and NCCL_BUFFSIZE Footprint
    ch_default = calculate_channels_and_buffers(
        detected_channels=16,
        min_nchannels=None,
        max_nchannels=None,
        buffsize_bytes=4_194_304,
        peers_per_channel=2,
        total_gpu_sms=132,
        zero_copy_registered=False,
    )
    ch_clamped = calculate_channels_and_buffers(
        detected_channels=16,
        min_nchannels=4,
        max_nchannels=8,
        buffsize_bytes=8_388_608,
        peers_per_channel=2,
        total_gpu_sms=132,
        zero_copy_registered=False,
    )
    ch_32 = calculate_channels_and_buffers(
        detected_channels=32,
        min_nchannels=None,
        max_nchannels=None,
        buffsize_bytes=16_777_216,
        peers_per_channel=2,
        total_gpu_sms=132,
        zero_copy_registered=False,
    )
    ch_zerocopy = calculate_channels_and_buffers(
        detected_channels=16,
        min_nchannels=None,
        max_nchannels=None,
        buffsize_bytes=4_194_304,
        peers_per_channel=2,
        total_gpu_sms=132,
        zero_copy_registered=True,
    )
    print(
        f"  [INFO] Channels & buffers: 16 ch @ 4 MiB = {ch_default['total_channel_buffer_mib']} MiB "
        f"({ch_default['sm_blocks_consumed']} SM blocks = {ch_default['sm_percentage_of_gpu']}% of 132 H100 SMs, "
        f"leaving 116 SMs / 87.88%); 8 ch = {ch_clamped['sm_percentage_of_gpu']}%; "
        f"32 ch @ 16 MiB = {ch_32['total_channel_buffer_mib']} MiB ({ch_32['sm_percentage_of_gpu']}%); "
        f"zero-copy registered = {int(ch_zerocopy['effective_channels'])} ch "
        f"(saved {int(ch_zerocopy['sm_blocks_saved_by_zero_copy'])} SM blocks)"
    )
    check(
        "ASP Ch4: Default NCCL_BUFFSIZE=4,194,304 B (4 MiB) across 16 channels (2 peers/ch) uses 16 SM blocks (12.12% of 132 H100 SMs, leaving 87.88%) and 128 MiB buffer memory",
        ch_default["effective_channels"] == 16.0
        and ch_default["subrings_count"] == 16.0
        and ch_default["sm_blocks_consumed"] == 16.0
        and ch_default["sm_percentage_of_gpu"] == 12.12
        and round(100.0 - ch_default["sm_percentage_of_gpu"], 2) == 87.88
        and ch_default["buffsize_mib"] == 4.0
        and ch_default["total_channel_buffer_mib"] == 128.0,
    )
    check(
        "ASP Ch4: NCCL_MIN_NCHANNELS=4 and NCCL_MAX_NCHANNELS=8 clamp 16 detected channels to 8 channels (6.06% of 132 SMs, 128 MiB at 8 MiB NCCL_BUFFSIZE); 32 channels @ 16 MiB uses 24.24% SMs and 1024.0 MiB",
        ch_clamped["clamped_channels"] == 8.0
        and ch_clamped["effective_channels"] == 8.0
        and ch_clamped["sm_percentage_of_gpu"] == 6.06
        and ch_clamped["buffsize_mib"] == 8.0
        and ch_clamped["total_channel_buffer_mib"] == 128.0
        and ch_32["sm_percentage_of_gpu"] == 24.24
        and ch_32["total_channel_buffer_mib"] == 1024.0,
    )
    check(
        "ASP Ch4: Persistent zero-copy buffer registration (ncclCommRegister) cuts NVLS channels from 16 to 4, saving 12 SM blocks (3.03% of 132 SMs)",
        ch_zerocopy["effective_channels"] == 4.0
        and ch_zerocopy["sm_blocks_saved_by_zero_copy"] == 12.0
        and ch_zerocopy["sm_percentage_of_gpu"] == 3.03
        and ch_zerocopy["total_channel_buffer_mib"] == 32.0,
    )

    # 5. NCCL Transport Selection Logic (P2P, SHM, NET_IB, NET_SOCKET, NVLS, COLLNET)
    check(
        "All 6 NCCL transport classes (P2P, SHM, NET_IB, NET_SOCKET, NVLS, COLLNET) are cataloged",
        set(NCCL_TRANSPORTS.keys()) == {"P2P", "SHM", "NET_IB", "NET_SOCKET", "NVLS", "COLLNET"},
    )
    t_p2p = select_nccl_transport(same_node=True, gpu_to_gpu_path="NV18", p2p_disable=0)
    t_nvls = select_nccl_transport(
        same_node=True, gpu_to_gpu_path="NV18", nvswitch_nvls_available=True, nvls_enable=1
    )
    t_mnnvl = select_nccl_transport(
        same_node=False,
        gpu_to_gpu_path="NV18",
        mnnvl_domain=True,
        mnnvl_enable=1,
        nvswitch_nvls_available=True,
        nvls_enable=1,
    )
    t_shm_fallback = select_nccl_transport(
        same_node=True, gpu_to_gpu_path="NV18", p2p_disable=1, shm_disable=0
    )
    t_sys_shm = select_nccl_transport(
        same_node=True, gpu_to_gpu_path="SYS", p2p_disable=0, p2p_level=None, shm_disable=0
    )
    t_sys_forced_p2p = select_nccl_transport(
        same_node=True, gpu_to_gpu_path="SYS", p2p_disable=0, p2p_level="SYS", shm_disable=0
    )
    check(
        "Intra-node NV18 selects P2P/IPC by default and NVLS when NVSwitch + NCCL_NVLS_ENABLE=1 are present",
        t_p2p["selected_transport"] == "P2P"
        and t_p2p["host_staging_required"] is False
        and t_nvls["selected_transport"] == "NVLS",
    )
    check(
        "ASP Ch4: Multi-Node NVLink (NCCL_MNNVL_ENABLE=1) on GB200/GB300 NVL72 selects MNNVL NVLS/P2P across trays",
        t_mnnvl["selected_transport"] == "NVLS" and t_mnnvl["mnnvl_active"] is True,
    )
    check(
        "ASP Ch4: Setting NCCL_P2P_DISABLE=1 (or crossing SYS without NCCL_P2P_LEVEL=SYS) forces fallback to SHM (/dev/shm host staging)",
        t_shm_fallback["selected_transport"] == "SHM"
        and t_shm_fallback["host_staging_required"] is True
        and t_sys_shm["selected_transport"] == "SHM"
        and t_sys_forced_p2p["selected_transport"] == "P2P",
    )

    t_ib_gdr = select_nccl_transport(
        same_node=False,
        gpu_to_gpu_path="SYS",
        gpu_to_nic_path="PIX",
        ib_disable=0,
        net_gdr_level="PIX",
        nvidia_peermem_loaded=True,
    )
    t_ib_no_gdr_sys = select_nccl_transport(
        same_node=False,
        gpu_to_gpu_path="SYS",
        gpu_to_nic_path="SYS",
        ib_disable=0,
        net_gdr_level="PIX",
        nvidia_peermem_loaded=True,
    )
    t_ib_no_peermem = select_nccl_transport(
        same_node=False,
        gpu_to_gpu_path="SYS",
        gpu_to_nic_path="PIX",
        ib_disable=0,
        net_gdr_level="PIX",
        nvidia_peermem_loaded=False,
    )
    t_collnet = select_nccl_transport(
        same_node=False,
        gpu_to_gpu_path="SYS",
        gpu_to_nic_path="PIX",
        ib_disable=0,
        net_gdr_level="PIX",
        nvidia_peermem_loaded=True,
        sharp_switch_available=True,
        collnet_enable=1,
        sharp_disable=0,
    )
    t_collnet_disabled = select_nccl_transport(
        same_node=False,
        gpu_to_gpu_path="SYS",
        gpu_to_nic_path="PIX",
        ib_disable=0,
        net_gdr_level="PIX",
        nvidia_peermem_loaded=True,
        sharp_switch_available=True,
        collnet_enable=1,
        sharp_disable=1,
    )
    t_tcp = select_nccl_transport(
        same_node=False,
        gpu_to_gpu_path="SYS",
        gpu_to_nic_path="PIX",
        ib_disable=1,
    )
    check(
        "V6 Ch2 & ASP Ch4: Inter-node PIX GPU-NIC with nvidia_peermem loaded enables NET/IB/GDRDMA (GPUDirect RDMA)",
        t_ib_gdr["selected_transport"] == "NET_IB"
        and t_ib_gdr["gpudirect_rdma_active"] is True
        and t_ib_gdr["log_prefix"] == "NET/IB/GDRDMA",
    )
    check(
        "V6 Ch2 & ASP Ch4: Missing nvidia_peermem or SYS GPU-NIC path disables GPUDirect RDMA and forces host-staged NET/IB",
        t_ib_no_gdr_sys["selected_transport"] == "NET_IB"
        and t_ib_no_gdr_sys["gpudirect_rdma_active"] is False
        and t_ib_no_gdr_sys["host_staging_required"] is True
        and t_ib_no_peermem["gpudirect_rdma_active"] is False,
    )
    check(
        "ASP Ch4: NCCL_COLLNET_ENABLE=1 enables CollNet/SHARP on Quantum IB switches, while NCCL_SHARP_DISABLE=1 forces fallback to NET/IB",
        t_collnet["selected_transport"] == "COLLNET"
        and t_collnet_disabled["selected_transport"] == "NET_IB",
    )
    check(
        "V6 Ch2 & ASP Ch4: NCCL_IB_DISABLE=1 (or missing /dev/infiniband) falls back to NET/Socket (TCP)",
        t_tcp["selected_transport"] == "NET_SOCKET"
        and t_tcp["log_prefix"] == "NET/Socket"
        and t_tcp["host_staging_required"] is True,
    )

    # 6. NCCL_SOCKET_IFNAME and NCCL_IB_HCA Prefix/Exact Filter Evaluators (=, ^, ^=)
    ifaces = ["lo", "docker0", "eth0", "eth0.100", "eth1", "ib0", "ib1"]
    check(
        "NCCL_SOCKET_IFNAME prefix match: 'ib' selects ['ib0', 'ib1'] and 'eth0' selects ['eth0', 'eth0.100']",
        filter_nccl_interfaces(ifaces, "ib") == ["ib0", "ib1"]
        and filter_nccl_interfaces(ifaces, "eth0") == ["eth0", "eth0.100"],
    )
    check(
        "NCCL_SOCKET_IFNAME exact match ('='): '=eth0' selects only ['eth0'] and excludes 'eth0.100'",
        filter_nccl_interfaces(ifaces, "=eth0") == ["eth0"],
    )
    check(
        "NCCL_SOCKET_IFNAME exclude prefix ('^'): '^docker,lo,eth' leaves only ['ib0', 'ib1']",
        filter_nccl_interfaces(ifaces, "^docker,lo,eth") == ["ib0", "ib1"],
    )
    check(
        "NCCL_SOCKET_IFNAME exclude exact ('^='): '^=lo,docker0,eth0' excludes exact 'eth0' but keeps 'eth0.100' and 'eth1'",
        filter_nccl_interfaces(ifaces, "^=lo,docker0,eth0") == ["eth0.100", "eth1", "ib0", "ib1"],
    )

    hcas = ["mlx5_0:1", "mlx5_1:1", "mlx5_2:1", "mlx5_3:1", "mlx5_bond_0:1"]
    check(
        "NCCL_IB_HCA filter: 'mlx5_0,mlx5_1' selects rails 0-1, '=mlx5_0:1' matches exact port, and '^mlx5_bond' excludes bond devices",
        filter_nccl_interfaces(hcas, "mlx5_0,mlx5_1") == ["mlx5_0:1", "mlx5_1:1"]
        and filter_nccl_interfaces(hcas, "=mlx5_0:1") == ["mlx5_0:1"]
        and filter_nccl_interfaces(hcas, "^mlx5_bond") == ["mlx5_0:1", "mlx5_1:1", "mlx5_2:1", "mlx5_3:1"],
    )

    # 7. Socket Transport 64-Connection Cap & Multirail 800G Bandwidth Math
    sock_2x2 = validate_socket_transport_limits(
        nsocks_perthread=2, socket_nthreads=2, num_nics=2, single_nic_bw_gbps=800.0
    )
    sock_8x8 = validate_socket_transport_limits(
        nsocks_perthread=8, socket_nthreads=8, num_nics=4, single_nic_bw_gbps=800.0
    )
    sock_over = validate_socket_transport_limits(
        nsocks_perthread=16, socket_nthreads=8, num_nics=4, single_nic_bw_gbps=800.0
    )
    print(
        f"  [INFO] Socket transport limits: 2x2={sock_2x2['total_sockets']} sockets "
        f"(2x800G={sock_2x2['aggregate_bw_tbps']} Tbps); 8x8={sock_8x8['total_sockets']} sockets "
        f"(4x800G={sock_8x8['aggregate_bw_tbps']} Tbps); 16x8={sock_over['total_sockets']} "
        f"(within_64={sock_over['within_nccl_64_limit']})"
    )
    check(
        "ASP Ch4 p.223 & p.299: 2 threads * 2 sockets = 4 connections; 2x 800 Gbps NICs yield 1.6 Tbps and 4x 800 Gbps NICs yield 3.2 Tbps",
        sock_2x2["total_sockets"] == 4
        and sock_2x2["within_nccl_64_limit"] is True
        and sock_2x2["aggregate_bw_tbps"] == 1.6
        and sock_8x8["aggregate_bw_tbps"] == 3.2,
    )
    check(
        "ASP Ch4 p.299 & p.617-618: NCCL_NSOCKS_PERTHREAD * NCCL_SOCKET_NTHREADS <= 64 passes for 8*8=64 and flags 16*8=128",
        sock_8x8["total_sockets"] == 64
        and sock_8x8["within_nccl_64_limit"] is True
        and sock_over["total_sockets"] == 128
        and sock_over["within_nccl_64_limit"] is False
        and sock_over["effective_sockets"] == 64,
    )

    # 8. Dual-Socket NUMA Affinity & K8s Topology Manager (`single-numa-node`) Incident
    k8s_fail = evaluate_numa_and_k8s_topology_manager(
        num_numa_nodes=2,
        cores_per_numa=64,
        gpus_per_numa=4,
        os_reserved_cores_on_numa1=2,
        pod_cpu_request=16,
        pod_gpu_request=1,
        num_pods_to_schedule=8,
        policy="single-numa-node",
        nccl_ignore_cpu_affinity=1,
    )
    k8s_fixed = evaluate_numa_and_k8s_topology_manager(
        num_numa_nodes=2,
        cores_per_numa=64,
        gpus_per_numa=4,
        os_reserved_cores_on_numa1=2,
        pod_cpu_request=12,
        pod_gpu_request=1,
        num_pods_to_schedule=8,
        policy="single-numa-node",
        nccl_ignore_cpu_affinity=1,
    )
    print(
        f"  [INFO] K8s Topology Manager (single-numa-node, 128 cores, 8 GPUs): "
        f"16 cores/pod -> status={k8s_fail['status']}, free_cores={k8s_fail['remaining_free_cores_per_numa']}; "
        f"12 cores/pod -> status={k8s_fixed['status']} ({k8s_fixed['admitted_pods']}/8 pods admitted)"
    )
    check(
        "V7 Ch8: On a 128-core (2x64), 8-GPU (2x4) server with 2 OS cores used on NUMA 1, requesting 16 cores/pod triggers TopologyAffinityError when 14 cores remain",
        k8s_fail["status"] == "TopologyAffinityError"
        and k8s_fail["remaining_free_cores_per_numa"] == [0, 14]
        and k8s_fail["remaining_free_gpus_per_numa"] == [0, 1],
    )
    check(
        "V7 Ch8 & ASP Ch4: Reducing request to 12 cores/pod schedules all 8 pods within strict single-numa-node bounds with NCCL_IGNORE_CPU_AFFINITY=1",
        k8s_fixed["status"] == "AllPodsRunning"
        and k8s_fixed["admitted_pods"] == 8
        and k8s_fixed["rejected_pods"] == 0
        and k8s_fixed["nccl_ignore_cpu_affinity"] is True,
    )

    # 9. Input validation checks
    raised_bad_label = False
    try:
        normalize_topo_label("INVALID_LINK")
    except NCCLTopologyEnvError:
        raised_bad_label = True
    check("Invalid topology path label raises NCCLTopologyEnvError", raised_bad_label)

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
