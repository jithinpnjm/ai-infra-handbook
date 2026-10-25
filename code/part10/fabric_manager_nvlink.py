#!/usr/bin/env python3
"""Chapter 10.10 model: Fabric Manager, NVSM, and NVLink Domains (plus Volume 07 GPU Data Paths).

Encodes the verifiable NVLink domain architectures, NVIDIA Fabric Manager
(`nvidia-fabricmanager`) lifecycle & systemd ordering rules, NVSM (`nvsm`) and
NVDebug (`nvdebug`) diagnostic workflows, ConnectX / GPUDirect RDMA / GDS /
Kubernetes Topology Manager (`single-numa-node`) sizing rules, and the 3-step
benchmarking hierarchy (`nvbandwidth` -> `ib_write_bw` -> `nccl-tests`) from:
- BCM 11 Administrator Manual §10.4.4, §10.13 & §10.14 (pp. 596, 606, 668-674):
  `nvsm` (`alerts`, `health` `--quick`, `info` `--history`, `status`, `stop`,
  `versions` showing `nvidia-driver 570.59`, `datacenter-gpu-manager-fabricmanager
  570.59-1`, `/cm/shared/nvsm/node001_YYYY-MM-DD-HH-MM-SS.tar.xz` ~15 min / 417 MiB)
  and `nvdebug` (`start/stop/status/history`, `/cm/shared/nvdebug/<hostname>`,
  `cm-nvdebug@<node>.service`).
- nvidia-devops Volume 01 Ch 4, Volume 04 Ch 1, Volume 05 Ch 3, Volume 06 Ch 2/7,
  Volume 07 Chapters 1-12 & Labs 01-04, Volume 13 Ch 8, and ASP Ch 2:
  Fabric Manager (`nv-fabricmanager -c /usr/share/nvidia/nvswitch/fabricmanager.cfg`,
  driver version lock, `After=nvidia-fabricmanager.service` + `Wants=` for
  `containerd`/`kubelet`, 800 GB/s -> 90 GB/s PCIe fallback when FM stops, Xid 74),
  NVLink domains (2-GPU PCIe bridge vs 8-GPU HGX baseboard vs 72-GPU NVL72 rack
  managed by NMX-M), ConnectX-6/7/8 specs, K8s Topology Manager `single-numa-node`
  CPU exhaustion math (128 cores, 8 GPUs, 16 cores/pod -> 5th pod fails with
  TopologyAffinityError when 2 OS cores reserved on NUMA 1; 12 cores/pod succeeds),
  and the 3-step benchmark isolation hierarchy (`nvbandwidth`, `ib_write_bw`,
  `nccl-tests` + DDP `bucket_cap_mb`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


class FabricDomainError(ValueError):
    """Raised when invalid NVLink domain, Fabric Manager, or data-path parameters are supplied."""


@dataclass(frozen=True)
class NVLinkDomainSpec:
    domain_type: str
    max_gpus_in_domain: int
    nvswitch_asics: int
    per_gpu_bidirectional_gbps: float
    aggregate_domain_tbps: float
    fabric_control_plane: str
    supports_nvls_sharp: bool


NVLINK_DOMAINS: Dict[str, NVLinkDomainSpec] = {
    "PCIE_2WAY_BRIDGE": NVLinkDomainSpec(
        domain_type="PCIe 2-Way NVLink Bridge Pair (e.g. H100 NVL)",
        max_gpus_in_domain=2,
        nvswitch_asics=0,
        per_gpu_bidirectional_gbps=600.0,
        aggregate_domain_tbps=1.2,
        fabric_control_plane="Direct point-to-point NVLink in GPU driver (no NVSwitch / no Fabric Manager required)",
        supports_nvls_sharp=False,
    ),
    "HGX_8GPU_H100": NVLinkDomainSpec(
        domain_type="8-GPU HGX / DGX H100 or H200 Baseboard (NVLink 4)",
        max_gpus_in_domain=8,
        nvswitch_asics=4,
        per_gpu_bidirectional_gbps=900.0,
        aggregate_domain_tbps=7.2,
        fabric_control_plane="Host systemd daemon: nvidia-fabricmanager (nv-fabricmanager)",
        supports_nvls_sharp=True,
    ),
    "HGX_8GPU_B200": NVLinkDomainSpec(
        domain_type="8-GPU HGX / DGX B200 Baseboard (NVLink 5)",
        max_gpus_in_domain=8,
        nvswitch_asics=4,
        per_gpu_bidirectional_gbps=1800.0,
        aggregate_domain_tbps=14.4,
        fabric_control_plane="Host systemd daemon: nvidia-fabricmanager (nv-fabricmanager)",
        supports_nvls_sharp=True,
    ),
    "NVL72_RACK_GB200_GB300": NVLinkDomainSpec(
        domain_type="72-GPU GB200 / GB300 NVL72 Rack (18 Compute Trays + 9 Switch Trays)",
        max_gpus_in_domain=72,
        nvswitch_asics=18,
        per_gpu_bidirectional_gbps=1800.0,
        aggregate_domain_tbps=129.6,
        fabric_control_plane="NVOS on Switch Trays + NMX-M (Network Manager eXperience) & Cluster Fabric Manager",
        supports_nvls_sharp=True,
    ),
}


@dataclass(frozen=True)
class ConnectXGenSpec:
    model: str
    max_rate_gbps: int
    unidirectional_line_rate_gb_per_s: float
    pcie_gen: int
    pcie_x16_unidirectional_gb_per_s: float
    optics_form_factor: str
    paired_gpu_era: str


CONNECTX_GENERATIONS: Dict[str, ConnectXGenSpec] = {
    "CONNECTX_6": ConnectXGenSpec("ConnectX-6", 200, 25.0, 4, 32.0, "QSFP56", "Ampere A100"),
    "CONNECTX_7": ConnectXGenSpec("ConnectX-7", 400, 50.0, 5, 64.0, "OSFP", "Hopper H100 / H200"),
    "CONNECTX_8": ConnectXGenSpec("ConnectX-8", 800, 100.0, 6, 128.0, "OSFP / CPO", "Blackwell B200 / GB300"),
}


def audit_fabric_manager_and_nvlink_domain(
    has_nvswitch: bool,
    driver_version: str,
    fabricmanager_version: str,
    fm_service_active: bool,
    kubelet_ordered_after_fm: bool,
    topo_gpu_pair_label: str = "NV18",
    nvlink_inactive_links: int = 0,
    xid_74_count: int = 0,
) -> Dict[str, object]:
    """Audit NVIDIA Fabric Manager (`nvidia-fabricmanager`) and NVSwitch domain health.

    Rules from V1 Ch 4 (§2.1-2.2), V4 Ch 1 (§5.3), V6 Ch 2, V13 Ch 8, V16 Ch 4, and BCM 11 §10.13:
    1. On NVSwitch systems (HGX/DGX 8-GPU or multi-node NVLink), `nvidia-fabricmanager` must be
       installed and locked to the exact driver version (e.g. `nvidia-driver 570.59` matches
       `datacenter-gpu-manager-fabricmanager 570.59-1`).
    2. If `nvidia-fabricmanager` is stopped or failed on an NVSwitch node, GPUs cannot route across
       NVSwitch; `nvidia-smi topo -m` or NCCL silently falls back to PCIe (`SYS`/`NODE`/`PIX`),
       dropping collective bus bandwidth from ~800 GB/s to ~90 GB/s (or hanging).
    3. `containerd.service` and `kubelet.service` must declare `After=nvidia-fabricmanager.service`
       and `Wants=nvidia-fabricmanager.service` so pods are not scheduled before NVLink is initialized.
    4. `Xid 74` indicates a hardware NVLink error requiring `nvidia-smi nvlink --status` /
       `--errorcounters`, `nvsm show health` / `dcgmi diag -r 2`, and baseboard/GPU inspection.
    """
    if not driver_version or not fabricmanager_version:
        raise FabricDomainError("driver_version and fabricmanager_version must be non-empty")

    findings: List[str] = []
    drv_clean = driver_version.strip().split("-")[0]
    fm_clean = fabricmanager_version.strip().split("-")[0]

    if has_nvswitch:
        if drv_clean != fm_clean:
            findings.append(
                f"Driver / Fabric Manager version mismatch: driver is '{driver_version}' "
                f"but nvidia-fabricmanager is '{fabricmanager_version}'."
            )
        if not fm_service_active:
            findings.append(
                "nvidia-fabricmanager.service is NOT active: NVSwitch fabric is uninitialized; "
                "NCCL will fail or silently fall back to PCIe (~800 GB/s -> ~90 GB/s)."
            )
        if not kubelet_ordered_after_fm:
            findings.append(
                "Missing systemd ordering: containerd/kubelet lack 'After=nvidia-fabricmanager.service' "
                "and 'Wants=nvidia-fabricmanager.service' drop-in; boot race condition possible."
            )
        if not topo_gpu_pair_label.strip().upper().startswith("NV"):
            findings.append(
                f"nvidia-smi topo -m reports '{topo_gpu_pair_label}' instead of 'NV#' on an NVSwitch node; "
                "NVSwitch routing is down."
            )

    if nvlink_inactive_links > 0:
        findings.append(f"{nvlink_inactive_links} NVLink sub-link(s) are inactive (0.000 GB/s).")

    if xid_74_count > 0:
        findings.append(
            f"Xid 74 (NVLink Error) detected ({xid_74_count} event(s)): run 'nvidia-smi nvlink --errorcounters', "
            "'nvsm alerts', and 'dcgmi diag -r 2'."
        )

    return {
        "has_nvswitch": has_nvswitch,
        "healthy": len(findings) == 0,
        "driver_version": driver_version,
        "fabricmanager_version": fabricmanager_version,
        "findings": findings,
    }


def simulate_k8s_single_numa_pod_admission(
    numa_nodes: int = 2,
    total_cpus: int = 128,
    total_gpus: int = 8,
    system_reserved_cpus_numa0: int = 0,
    system_reserved_cpus_numa1: int = 2,
    pod_cpu_request: int = 16,
    pod_gpu_request: int = 1,
    pods_requested: int = 8,
) -> Dict[str, object]:
    """Simulate kubelet Topology Manager `single-numa-node` pod admission per V7 Ch 8 Customer Scenario.

    In V7 Ch 8 (lines 91-115):
    - Dual-socket server has 128 CPU cores (64 per NUMA node) and 8 GPUs (4 per NUMA node).
    - Each Triton pod requests 16 integer CPU cores and 1 GPU (Guaranteed QoS).
    - NUMA 0 has 64 free cores and admits 4 pods (4 * 16 = 64 cores, 4 GPUs).
    - On NUMA 1, OS/daemonsets reserve 2 cores (leaving 62 free cores) while 4 GPUs are free.
    - Pods 5, 6, 7 take 3 * 16 = 48 cores (leaving 14 free cores and 1 free GPU on NUMA 1),
      or if 2 cores are already consumed before the 4th pod on that socket, the pod needing
      16 contiguous cores on that NUMA node is rejected with `TopologyAffinityError` because
      only 14 cores remain on NUMA 1.
    - Reducing `pod_cpu_request` from 16 to 12 cores (4 * 12 = 48 <= 62) allows all 8 pods
      to schedule cleanly within strict `single-numa-node` boundaries.
    """
    if numa_nodes <= 0 or total_cpus <= 0 or total_gpus <= 0 or pod_cpu_request <= 0 or pod_gpu_request <= 0:
        raise FabricDomainError("Cluster and pod resource counts must be positive")
    if total_cpus % numa_nodes != 0 or total_gpus % numa_nodes != 0:
        raise FabricDomainError("total_cpus and total_gpus must be evenly divisible by numa_nodes")

    cpus_per_numa = total_cpus // numa_nodes
    gpus_per_numa = total_gpus // numa_nodes
    reserved = [system_reserved_cpus_numa0, system_reserved_cpus_numa1] + [0] * max(0, numa_nodes - 2)

    free_cpus = [cpus_per_numa - reserved[i] for i in range(numa_nodes)]
    free_gpus = [gpus_per_numa for _ in range(numa_nodes)]

    admitted_pods = 0
    rejected_pods = 0
    rejection_reasons: List[str] = []

    for pod_idx in range(1, pods_requested + 1):
        placed = False
        for nid in range(numa_nodes):
            if free_gpus[nid] >= pod_gpu_request and free_cpus[nid] >= pod_cpu_request:
                free_gpus[nid] -= pod_gpu_request
                free_cpus[nid] -= pod_cpu_request
                admitted_pods += 1
                placed = True
                break
        if not placed:
            rejected_pods += 1
            rejection_reasons.append(
                f"Pod {pod_idx}: TopologyAffinityError (remaining per-NUMA free CPUs={free_cpus}, "
                f"free GPUs={free_gpus}, requested={pod_cpu_request} CPUs + {pod_gpu_request} GPU on single NUMA node)."
            )

    return {
        "pod_cpu_request": pod_cpu_request,
        "pod_gpu_request": pod_gpu_request,
        "pods_requested": pods_requested,
        "admitted_pods": admitted_pods,
        "rejected_pods": rejected_pods,
        "remaining_free_cpus_per_numa": free_cpus,
        "remaining_free_gpus_per_numa": free_gpus,
        "all_admitted": rejected_pods == 0,
        "rejection_reasons": rejection_reasons,
    }


def diagnose_three_step_data_path_benchmarks(
    nvbandwidth_d2h_gbps: float = 56.0,
    ib_port_state: str = "Active",
    ib_physical_state: str = "LinkUp",
    ib_symbol_or_rcv_errors: int = 0,
    ib_write_bw_gbps: float = 392.0,
    nccl_bus_bw_gbps: float = 45.0,
    nccl_debug_transport: str = "NET/IB",
    nccl_gdr_enabled: bool = True,
    app_allreduce_msg_kb: float = 25600.0,
    ddp_bucket_cap_mb: int = 25,
) -> Dict[str, object]:
    """Run the 3-step hardware-to-application benchmark triage from V7 Ch 10 & Labs 03-04.

    Hierarchy (V7 Ch 10 Fig & Steps 1-3, Lab 03 Steps 1-7):
    - Step 0 (IB Link & Counters): `ibstat` must show `State: Active` and `Physical state: LinkUp`
      (if `Physical state: LinkUp` but `State: Initializing`, the InfiniBand Subnet Manager is down/unreachable),
      and `/sys/class/infiniband/*/ports/*/counters` (`symbol_error`, `link_error_recovery`, `port_rcv_errors`,
      `VL15_dropped`) must remain 0.
    - Step 1 (`nvbandwidth`): On PCIe Gen5 x16, `device_to_host_memcpy_ce` should deliver ~50-60 GB/s;
      if it drops to ~25-30 GB/s, the PCIe link downtrained (e.g. x16 -> x8).
    - Step 2 (`ib_write_bw`): On 400G NDR, raw host RDMA should deliver ~390 Gbps; if half rate,
      check `mlxlink` / optics / cable.
    - Step 3 (`nccl-tests` `all_reduce_perf`): If `nvbandwidth` and `ib_write_bw` pass, but `nccl-tests`
      is slow, check `NCCL_DEBUG=INFO`: `NET/Socket` means TCP fallback; `NET/IB` without GDR (`nvidia-peermem`
      missing / ACS enabled / no Large BAR) means Host Bounce Buffer fallback (~50 Gbps on 400G IB, V7 Ch 5).
    - Step 4 (Application message size): If `nccl-tests` passes at large buffers, but PyTorch training is
      40% slower due to thousands of tiny 256 KB AllReduces, increase DDP `bucket_cap_mb` (default 25 MB -> 50 MB).
    """
    if nvbandwidth_d2h_gbps <= 0 or ib_write_bw_gbps < 0 or nccl_bus_bw_gbps < 0 or app_allreduce_msg_kb <= 0:
        raise FabricDomainError("Bandwidth and message size values must be valid")

    if ib_physical_state == "LinkUp" and ib_port_state != "Active":
        return {
            "healthy": False,
            "bottleneck_stage": "STEP_0_SUBNET_MANAGER_INIT",
            "diagnosis": (
                f"ibstat shows Physical state '{ib_physical_state}' (cable/optics good) but logical State "
                f"'{ib_port_state}': InfiniBand Subnet Manager (OpenSM / UFM) has not initialized the port."
            ),
        }

    if ib_symbol_or_rcv_errors > 0:
        return {
            "healthy": False,
            "bottleneck_stage": "STEP_0_FABRIC_ERROR_COUNTERS",
            "diagnosis": (
                f"InfiniBand port error counters increased by {ib_symbol_or_rcv_errors} "
                "(symbol_error / port_rcv_errors / link_error_recovery): dirty fiber optic connector or degraded cable."
            ),
        }

    if nvbandwidth_d2h_gbps < 40.0:
        return {
            "healthy": False,
            "bottleneck_stage": "STEP_1_MOTHERBOARD_PCIE_DOWNTRAIN",
            "diagnosis": (
                f"nvbandwidth reported {nvbandwidth_d2h_gbps} GB/s (expected 50-60 GB/s on PCIe Gen5 x16): "
                "GPU or NIC PCIe link downtrained (e.g. x16 -> x8 at 25-30 GB/s); check lspci -vv LnkSta."
            ),
        }

    if ib_write_bw_gbps < 350.0:
        return {
            "healthy": False,
            "bottleneck_stage": "STEP_2_PHYSICAL_RDMA_WIRE",
            "diagnosis": (
                f"ib_write_bw reported {ib_write_bw_gbps} Gbps (expected ~390 Gbps on 400G NDR): "
                "physical link or RoCE PFC/ECN degradation; inspect ibstat and mlxlink."
            ),
        }

    if nccl_debug_transport.strip().upper() == "NET/SOCKET":
        return {
            "healthy": False,
            "bottleneck_stage": "STEP_3A_NCCL_TCP_SOCKET_FALLBACK",
            "diagnosis": (
                "ib_write_bw is healthy, but NCCL_DEBUG=INFO shows 'NET/Socket': NCCL fell back to "
                "host kernel TCP/IP sockets; check container RDMA device exposure (/dev/infiniband) and NCCL_IB_HCA."
            ),
        }

    if not nccl_gdr_enabled or nccl_bus_bw_gbps < 20.0:
        return {
            "healthy": False,
            "bottleneck_stage": "STEP_3B_GPUDIRECT_RDMA_BOUNCE_BUFFER",
            "diagnosis": (
                "ib_write_bw is healthy, but GPUDirect RDMA is inactive (transfers bounce through host CPU RAM): "
                "verify 'lsmod | grep nvidia_peermem', PCIe PIX locality, ACS disabled, and BIOS Large BAR / Above 4G Decoding."
            ),
        }

    if app_allreduce_msg_kb < 1024.0:
        return {
            "healthy": False,
            "bottleneck_stage": "STEP_4_APPLICATION_SMALL_MESSAGE_LATENCY",
            "diagnosis": (
                f"nvbandwidth, ib_write_bw, and nccl-tests are healthy, but application issues tiny "
                f"{app_allreduce_msg_kb} KB AllReduce calls: increase PyTorch DDP bucket_cap_mb "
                f"(from default {ddp_bucket_cap_mb} MB to e.g. 50 MB) to batch gradients."
            ),
        }

    return {
        "healthy": True,
        "bottleneck_stage": "NONE",
        "diagnosis": "All 3 hardware benchmark tiers (nvbandwidth, ib_write_bw, nccl-tests) and application bucket sizing are healthy.",
    }
