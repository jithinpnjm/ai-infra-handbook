#!/usr/bin/env python3
"""Chapter 12.16 model: NCCL: topology, channels, transports and environment variables.

Encodes the verifiable mathematical and graph models for:
1. NCCL XML topology path cost scoring (`NVL` < `PIX` < `PXB` < `PHB` < `SYS`),
   PCIe/NVLink/NIC graph parsing, and hierarchical vs flat ring routing.
2. NCCL channel count calculation (`NCCL_MIN_NCHANNELS`, `NCCL_MAX_NCHANNELS`),
   subring mapping, SM thread-block consumption per channel, and zero-copy
   `ncclCommRegister` channel reduction (`16 -> 4` channels, saving `12` SM blocks).
3. NCCL transport selection logic (`P2P` NVLink/PCIe BAR1, `SHM` host shared memory,
   `NET/IB` RDMA & `IBGDA`, `NET/Socket` TCP, `NVLS` NVSwitch SHARP, and `CollNet`
   InfiniBand SHARP) controlled by `NCCL_P2P_LEVEL`, `NCCL_NET_GDR_LEVEL`,
   `NCCL_P2P_DISABLE`, `NCCL_SHM_DISABLE`, `NCCL_IB_DISABLE`, `NCCL_MNNVL_ENABLE`,
   `NCCL_COLLNET_ENABLE`, `NCCL_NVLS_ENABLE`, and `NCCL_SHARP_DISABLE`.
4. `NCCL_SOCKET_IFNAME` and `NCCL_IB_HCA` prefix/exact filter evaluators (`=`, `^`, `^=`)
   and port specifiers (`mlx5_0:1`).
5. `NCCL_NSOCKS_PERTHREAD * NCCL_SOCKET_NTHREADS <= 64` socket limit validator and
   `NCCL_BUFFSIZE` (starting at `4 MiB` = `4,194,304 B`) channel memory footprint calculator.
6. Dual-socket NUMA affinity & Kubernetes `Topology Manager` (`single-numa-node`)
   validator (`128` cores, `8` GPUs, `16` cores/pod vs `14` free cores -> `TopologyAffinityError`)
   and `NCCL_IGNORE_CPU_AFFINITY=1` thread spreading.

Grounded in:
- *AI Systems Performance Engineering* (`ai-systems-performance-engineering`), Chapter 4.
- `nvidia-devops` Volume 07 Chapter 8 (`chapter-08-topology-aware-placement.md`),
  Volume 07 Chapter 9 (`chapter-09-multi-node-collectives-and-nccl-paths.md`),
  Volume 06 Chapter 2 (`02-gpudirect-fabric-operator-masterclass.md` / `02-nccl-topology-and-gpudirect-rdma.md`),
  Volume 02 Chapter 10 (`GPU Topology, Peer Access, and Data Paths`), and
  Volume 13 Chapter 8 (`NCCL Collectives and Communication Paths`).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


class NCCLTopologyEnvError(ValueError):
    """Raised when invalid topology, channel, transport, or environment parameters are given."""


@dataclass(frozen=True)
class TopologyPathLevelSpec:
    level_token: str
    numeric_rank: int
    cost_weight: int
    typical_bw_gbps: float
    typical_latency_us: float
    hardware_meaning: str
    gpudirect_p2p_or_rdma_viable: bool


TOPOLOGY_PATH_LEVELS: Dict[str, TopologyPathLevelSpec] = {
    "LOC": TopologyPathLevelSpec(
        level_token="LOC",
        numeric_rank=0,
        cost_weight=0,
        typical_bw_gbps=3000.0,
        typical_latency_us=0.1,
        hardware_meaning="Self (same device / loopback)",
        gpudirect_p2p_or_rdma_viable=True,
    ),
    "NVL": TopologyPathLevelSpec(
        level_token="NVL",
        numeric_rank=1,
        cost_weight=10,
        typical_bw_gbps=900.0,
        typical_latency_us=0.5,
        hardware_meaning="Direct NVLink or NVSwitch fabric (e.g., NV4, NV12, NV18; 900 GB/s Hopper, 1,800 GB/s Blackwell)",
        gpudirect_p2p_or_rdma_viable=True,
    ),
    "C2C": TopologyPathLevelSpec(
        level_token="C2C",
        numeric_rank=2,
        cost_weight=15,
        typical_bw_gbps=900.0,
        typical_latency_us=0.6,
        hardware_meaning="NVLink-C2C coherent chip-to-chip interconnect (900 GB/s on Grace Hopper GH200 / Grace Blackwell GB200)",
        gpudirect_p2p_or_rdma_viable=True,
    ),
    "PIX": TopologyPathLevelSpec(
        level_token="PIX",
        numeric_rank=3,
        cost_weight=30,
        typical_bw_gbps=64.0,
        typical_latency_us=1.2,
        hardware_meaning="Connection traversing at most a single PCIe bridge/switch (ideal GPU-to-NIC rail locality)",
        gpudirect_p2p_or_rdma_viable=True,
    ),
    "PXB": TopologyPathLevelSpec(
        level_token="PXB",
        numeric_rank=4,
        cost_weight=50,
        typical_bw_gbps=48.0,
        typical_latency_us=1.8,
        hardware_meaning="Connection traversing multiple PCIe bridges/switches without crossing the PCIe Host Bridge",
        gpudirect_p2p_or_rdma_viable=True,
    ),
    "PHB": TopologyPathLevelSpec(
        level_token="PHB",
        numeric_rank=5,
        cost_weight=80,
        typical_bw_gbps=32.0,
        typical_latency_us=3.0,
        hardware_meaning="Connection traversing a PCIe Host Bridge / Root Complex within a single CPU NUMA node",
        gpudirect_p2p_or_rdma_viable=False,
    ),
    "SYS": TopologyPathLevelSpec(
        level_token="SYS",
        numeric_rank=6,
        cost_weight=200,
        typical_bw_gbps=28.0,
        typical_latency_us=8.0,
        hardware_meaning="Connection traversing PCIe as well as the inter-socket NUMA link (Intel UPI / AMD Infinity Fabric)",
        gpudirect_p2p_or_rdma_viable=False,
    ),
}


@dataclass(frozen=True)
class NCCLTransportSpec:
    transport_id: str
    internal_prefix: str
    scope: str
    data_path_mechanism: str
    controlling_env_vars: Tuple[str, ...]
    fallback_when_disabled: str


NCCL_TRANSPORTS: Dict[str, NCCLTransportSpec] = {
    "P2P": NCCLTransportSpec(
        transport_id="P2P",
        internal_prefix="P2P/IPC / P2P/CUMEM",
        scope="Intra-node (or MNNVL intra-rack NVL72)",
        data_path_mechanism="Direct GPU-to-GPU peer memory reads/writes over NVLink/NVSwitch or PCIe BAR1 P2P (CUDA IPC / cuMem + fabric handles)",
        controlling_env_vars=("NCCL_P2P_LEVEL", "NCCL_P2P_DISABLE", "NCCL_MNNVL_ENABLE"),
        fallback_when_disabled="SHM (host shared memory staging in /dev/shm) or NET",
    ),
    "SHM": NCCLTransportSpec(
        transport_id="SHM",
        internal_prefix="SHM/direct",
        scope="Intra-node",
        data_path_mechanism="Host pinned shared-memory staging buffers in /dev/shm when direct GPU P2P is disabled or across PHB/SYS",
        controlling_env_vars=("NCCL_SHM_DISABLE",),
        fallback_when_disabled="NET/IB (loopback) or NET/Socket (TCP loopback)",
    ),
    "NET_IB": NCCLTransportSpec(
        transport_id="NET_IB",
        internal_prefix="NET/IB",
        scope="Inter-node (and intra-node fallback / PXN)",
        data_path_mechanism="InfiniBand or RoCEv2 RDMA Verbs via mlx5_core; GPUDirect RDMA via nvidia-peermem / DMA-BUF or GPU-initiated IBGDA",
        controlling_env_vars=(
            "NCCL_IB_DISABLE",
            "NCCL_IB_HCA",
            "NCCL_NET_GDR_LEVEL",
            "NCCL_IB_GID_INDEX",
            "NCCL_IB_TC",
            "NCCL_IB_QPS_PER_CONNECTION",
            "NCCL_CROSS_NIC",
        ),
        fallback_when_disabled="NET/Socket (kernel TCP/IP stack over Ethernet/IPoIB)",
    ),
    "NET_SOCKET": NCCLTransportSpec(
        transport_id="NET_SOCKET",
        internal_prefix="NET/Socket",
        scope="Bootstrap out-of-band handshake + Inter-node TCP fallback",
        data_path_mechanism="POSIX TCP sockets via CPU proxy threads and host RAM bounce buffers",
        controlling_env_vars=("NCCL_SOCKET_IFNAME", "NCCL_SOCKET_NTHREADS", "NCCL_NSOCKS_PERTHREAD"),
        fallback_when_disabled="Communicator initialization fails if no usable bootstrap interface remains",
    ),
    "NVLS": NCCLTransportSpec(
        transport_id="NVLS",
        internal_prefix="NVLS",
        scope="Intra-node HGX/DGX and intra-rack GB200/GB300 NVL72 (72 GPUs)",
        data_path_mechanism="NVLink SHARP in-switch reduction and hardware multicast across NVSwitch 3.0/4.0 domains",
        controlling_env_vars=("NCCL_NVLS_ENABLE",),
        fallback_when_disabled="P2P Ring / Tree over NVLink",
    ),
    "COLLNET": NCCLTransportSpec(
        transport_id="COLLNET",
        internal_prefix="CollNet/SHARP",
        scope="Multi-node InfiniBand fabrics with Quantum switches",
        data_path_mechanism="In-network switch-ASIC reduction via Quantum InfiniBand switches + SHARP Aggregation Manager + CollNet plugin",
        controlling_env_vars=("NCCL_COLLNET_ENABLE", "NCCL_SHARP_DISABLE"),
        fallback_when_disabled="NET/IB hierarchical Tree or Ring",
    ),
}


def normalize_topo_label(label: str) -> str:
    """Normalize `nvidia-smi topo -m` labels (`NV4`, `NV12`, `NV18`, `X`) to canonical path levels."""
    tok = label.strip().upper()
    if tok == "X" or tok == "LOC":
        return "LOC"
    if tok.startswith("NV"):
        return "NVL"
    if tok in TOPOLOGY_PATH_LEVELS:
        return tok
    raise NCCLTopologyEnvError(f"Unknown topology path label: {label!r}")


def score_topology_path(label_a: str, label_b: str = "LOC") -> Dict[str, object]:
    """Compare two topology path labels (`NVL` < `C2C` < `PIX` < `PXB` < `PHB` < `SYS`)."""
    norm_a = normalize_topo_label(label_a)
    norm_b = normalize_topo_label(label_b)
    spec_a = TOPOLOGY_PATH_LEVELS[norm_a]
    spec_b = TOPOLOGY_PATH_LEVELS[norm_b]
    return {
        "label_a": label_a,
        "normalized_a": norm_a,
        "rank_a": spec_a.numeric_rank,
        "cost_a": spec_a.cost_weight,
        "bw_a_gbps": spec_a.typical_bw_gbps,
        "label_b": label_b,
        "normalized_b": norm_b,
        "rank_b": spec_b.numeric_rank,
        "cost_b": spec_b.cost_weight,
        "bw_b_gbps": spec_b.typical_bw_gbps,
        "a_strictly_faster_than_b": spec_a.cost_weight < spec_b.cost_weight,
        "bottleneck_level": norm_a if spec_a.cost_weight >= spec_b.cost_weight else norm_b,
    }


def evaluate_500mb_nvlink_vs_sys_step() -> Dict[str, float]:
    """Reproduce V2 Ch 10 / ASP Ch 4 comparison: 500 MB (0.5 GB) over NVLink (900 GB/s) vs SYS (28 GB/s) and overlap."""
    payload_gb = 0.5
    nvlink_bw_gbps = 900.0
    sys_bw_gbps = 28.0
    nvlink_ms = (payload_gb / nvlink_bw_gbps) * 1000.0
    sys_ms = (payload_gb / sys_bw_gbps) * 1000.0
    slowdown_factor = sys_ms / nvlink_ms
    return {
        "payload_gb": payload_gb,
        "nvlink_bw_gbps": nvlink_bw_gbps,
        "sys_bw_gbps": sys_bw_gbps,
        "nvlink_time_ms": round(nvlink_ms, 2),
        "sys_time_ms": round(sys_ms, 2),
        "sys_vs_nvlink_slowdown_x": round(slowdown_factor, 2),
        "table_4_2_before_sm_busy_pct": 60.0,
        "table_4_2_after_sm_busy_pct": 90.0,
        "table_4_2_before_iter_ms": 100.0,
        "table_4_2_after_iter_ms": 70.0,
        "table_4_2_iter_reduction_pct": 30.0,
    }


def parse_nccl_topo_xml(xml_text: str) -> Dict[str, object]:
    """Parse an `NCCL_TOPO_FILE` / `NCCL_TOPO_DUMP_FILE` XML document and score GPU-to-NIC paths.

    Determines whether each GPU and NIC share a PCIe switch (`PIX`), share a CPU NUMA node
    across different PCIe root ports (`PHB`), or cross NUMA nodes (`SYS`).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise NCCLTopologyEnvError(f"Invalid topology XML: {exc}") from exc

    if root.tag != "system":
        raise NCCLTopologyEnvError(f"Root tag must be <system>, got <{root.tag}>")

    gpus: List[Dict[str, object]] = []
    nics: List[Dict[str, object]] = []

    def walk_pci(node: ET.Element, numaid: int, root_busid: str, switch_chain: Tuple[str, ...]) -> None:
        for child in node:
            if child.tag == "pci":
                busid = child.attrib.get("busid", "")
                new_root = root_busid or busid
                new_chain = switch_chain + (busid,)
                walk_pci(child, numaid, new_root, new_chain)
            elif child.tag == "gpu":
                gpus.append(
                    {
                        "dev": int(child.attrib["dev"]),
                        "rank": int(child.attrib.get("rank", child.attrib["dev"])),
                        "sm": int(child.attrib.get("sm", 80)),
                        "gdr": int(child.attrib.get("gdr", 0)),
                        "numaid": numaid,
                        "root_busid": root_busid,
                        "switch_busid": switch_chain[-1] if switch_chain else root_busid,
                        "switch_chain": switch_chain,
                    }
                )
            elif child.tag == "nic":
                for net in child.findall("net"):
                    nics.append(
                        {
                            "name": net.attrib["name"],
                            "dev": int(net.attrib.get("dev", 0)),
                            "speed_mbps": int(net.attrib.get("speed", 100000)),
                            "port": int(net.attrib.get("port", 1)),
                            "gdr": int(net.attrib.get("gdr", 0)),
                            "numaid": numaid,
                            "root_busid": root_busid,
                            "switch_busid": switch_chain[-1] if switch_chain else root_busid,
                            "switch_chain": switch_chain,
                        }
                    )

    for cpu in root.findall("cpu"):
        numaid = int(cpu.attrib.get("numaid", 0))
        walk_pci(cpu, numaid, "", ())

    pair_paths: Dict[Tuple[int, str], str] = {}
    for g in gpus:
        for n in nics:
            if g["numaid"] != n["numaid"]:
                level = "SYS"
            elif g["switch_busid"] == n["switch_busid"] and len(g["switch_chain"]) >= 2:
                level = "PIX"
            elif g["root_busid"] == n["root_busid"] and g[" root_busid" if False else "root_busid"] != "":
                level = "PXB"
            else:
                level = "PHB"
            pair_paths[(int(g["dev"]), str(n["name"]))] = level

    return {
        "version": int(root.attrib.get("version", 1)),
        "gpus": gpus,
        "nics": nics,
        "gpu_nic_paths": pair_paths,
    }


def calculate_channels_and_buffers(
    *,
    detected_channels: int,
    min_nchannels: int | None = None,
    max_nchannels: int | None = None,
    buffsize_bytes: int = 4_194_304,
    peers_per_channel: int = 2,
    total_gpu_sms: int = 132,
    zero_copy_registered: bool = False,
) -> Dict[str, float]:
    """Compute active NCCL channels, SM thread blocks consumed, and channel buffer footprint.

    - Each active channel launches 1 CUDA thread block (using 1 SM) per direction/ring.
    - `NCCL_MIN_NCHANNELS` and `NCCL_MAX_NCHANNELS` clamp the auto-detected channel count.
    - `NCCL_BUFFSIZE` defaults to 4 MiB (`4,194,304` bytes) per channel peer slot.
    - Persistent user buffer registration (`ncclCommRegister` + `ncclMemAlloc`) drops
      NVLS/zero-copy channel count (e.g., from `16` to `4`, saving `12` SM blocks).
    """
    if detected_channels < 1:
        raise NCCLTopologyEnvError("detected_channels must be >= 1")
    if buffsize_bytes <= 0:
        raise NCCLTopologyEnvError("buffsize_bytes must be > 0")
    if total_gpu_sms < 1:
        raise NCCLTopologyEnvError("total_gpu_sms must be >= 1")

    lo = min_nchannels if min_nchannels is not None else 1
    hi = max_nchannels if max_nchannels is not None else 64
    if lo < 1 or hi < lo:
        raise NCCLTopologyEnvError(f"Invalid channel bounds: min={lo}, max={hi}")

    active = max(lo, min(hi, detected_channels))
    effective_channels = max(1, active // 4) if zero_copy_registered and active >= 4 else active
    sm_blocks_saved = active - effective_channels
    sm_occupancy_pct = (effective_channels / float(total_gpu_sms)) * 100.0
    total_buffer_bytes = effective_channels * peers_per_channel * buffsize_bytes
    total_buffer_mib = total_buffer_bytes / float(1024 * 1024)

    return {
        "detected_channels": float(detected_channels),
        "clamped_channels": float(active),
        "effective_channels": float(effective_channels),
        "subrings_count": float(effective_channels),
        "sm_blocks_consumed": float(effective_channels),
        "sm_blocks_saved_by_zero_copy": float(sm_blocks_saved),
        "sm_percentage_of_gpu": round(sm_occupancy_pct, 2),
        "buffsize_bytes": float(buffsize_bytes),
        "buffsize_mib": round(buffsize_bytes / float(1024 * 1024), 2),
        "total_channel_buffer_bytes": float(total_buffer_bytes),
        "total_channel_buffer_mib": round(total_buffer_mib, 2),
    }


def select_nccl_transport(
    *,
    same_node: bool,
    gpu_to_gpu_path: str,
    gpu_to_nic_path: str = "PIX",
    p2p_disable: int = 0,
    p2p_level: str | None = None,
    shm_disable: int = 0,
    ib_disable: int = 0,
    net_gdr_level: str = "PIX",
    nvidia_peermem_loaded: bool = True,
    nvswitch_nvls_available: bool = False,
    nvls_enable: int = 1,
    mnnvl_domain: bool = False,
    mnnvl_enable: int = 0,
    sharp_switch_available: bool = False,
    collnet_enable: int = 0,
    sharp_disable: int = 0,
) -> Dict[str, object]:
    """Determine the active NCCL transport and data path from topology and environment variables."""
    g2g = normalize_topo_label(gpu_to_gpu_path)
    g2n = normalize_topo_label(gpu_to_nic_path)
    gdr_cutoff = normalize_topo_label(net_gdr_level)

    # Multi-Node NVLink (MNNVL, e.g., GB200/GB300 NVL72 across compute trays)
    if not same_node and mnnvl_domain and mnnvl_enable == 1 and p2p_disable == 0:
        if nvswitch_nvls_available and nvls_enable == 1:
            return {
                "selected_transport": "NVLS",
                "log_prefix": "NVLS",
                "gpudirect_rdma_active": False,
                "mnnvl_active": True,
                "host_staging_required": False,
                "reason": "Multi-Node NVLink (NCCL_MNNVL_ENABLE=1) + NVSwitch NVLS offload across NVL72 rack",
            }
        return {
            "selected_transport": "P2P",
            "log_prefix": "P2P/CUMEM",
            "gpudirect_rdma_active": False,
            "mnnvl_active": True,
            "host_staging_required": False,
            "reason": "Multi-Node NVLink (NCCL_MNNVL_ENABLE=1) direct P2P over NVLink Switch fabric",
        }

    if same_node:
        if nvswitch_nvls_available and nvls_enable == 1 and p2p_disable == 0 and g2g == "NVL":
            return {
                "selected_transport": "NVLS",
                "log_prefix": "NVLS",
                "gpudirect_rdma_active": False,
                "mnnvl_active": False,
                "host_staging_required": False,
                "reason": "Intra-node NVSwitch domain with NCCL_NVLS_ENABLE=1",
            }

        # Determine maximum allowed P2P path rank
        if p2p_disable == 1 or (p2p_level is not None and p2p_level.upper() == "LOC"):
            max_p2p_rank = 0
        elif p2p_level is not None:
            max_p2p_rank = TOPOLOGY_PATH_LEVELS[normalize_topo_label(p2p_level)].numeric_rank
        else:
            # Default: allow NVL, C2C, PIX, PXB (not PHB/SYS unless forced via NCCL_P2P_LEVEL=PHB/SYS)
            max_p2p_rank = TOPOLOGY_PATH_LEVELS["PXB"].numeric_rank

        if TOPOLOGY_PATH_LEVELS[g2g].numeric_rank <= max_p2p_rank:
            return {
                "selected_transport": "P2P",
                "log_prefix": "P2P/IPC",
                "gpudirect_rdma_active": False,
                "mnnvl_active": False,
                "host_staging_required": False,
                "reason": f"Intra-node direct P2P enabled over {g2g} (rank {TOPOLOGY_PATH_LEVELS[g2g].numeric_rank} <= {max_p2p_rank})",
            }

        if shm_disable == 0:
            return {
                "selected_transport": "SHM",
                "log_prefix": "SHM/direct",
                "gpudirect_rdma_active": False,
                "mnnvl_active": False,
                "host_staging_required": True,
                "reason": f"Intra-node P2P disallowed or disabled over {g2g}; falling back to host /dev/shm staging",
            }

    # Inter-node (or intra-node when both P2P and SHM are disabled)
    if ib_disable == 0:
        gdr_ok = (
            nvidia_peermem_loaded
            and TOPOLOGY_PATH_LEVELS[g2n].numeric_rank <= TOPOLOGY_PATH_LEVELS[gdr_cutoff].numeric_rank
            and TOPOLOGY_PATH_LEVELS[g2n].numeric_rank < TOPOLOGY_PATH_LEVELS["SYS"].numeric_rank
        )
        if sharp_switch_available and collnet_enable == 1 and sharp_disable == 0 and gdr_ok:
            return {
                "selected_transport": "COLLNET",
                "log_prefix": "CollNet/SHARP",
                "gpudirect_rdma_active": True,
                "mnnvl_active": False,
                "host_staging_required": False,
                "reason": "Multi-node InfiniBand SHARP offload enabled (NCCL_COLLNET_ENABLE=1, NCCL_SHARP_DISABLE=0)",
            }
        return {
            "selected_transport": "NET_IB",
            "log_prefix": "NET/IB/GDRDMA" if gdr_ok else "NET/IB",
            "gpudirect_rdma_active": gdr_ok,
            "mnnvl_active": False,
            "host_staging_required": not gdr_ok,
            "reason": (
                f"RDMA over NET/IB with GPUDirect RDMA active (GPU-NIC={g2n} <= NCCL_NET_GDR_LEVEL={gdr_cutoff})"
                if gdr_ok
                else f"RDMA over NET/IB using host-staged bounce buffer (nvidia_peermem={nvidia_peermem_loaded}, GPU-NIC={g2n}, GDR_LEVEL={gdr_cutoff})"
            ),
        }

    return {
        "selected_transport": "NET_SOCKET",
        "log_prefix": "NET/Socket",
        "gpudirect_rdma_active": False,
        "mnnvl_active": False,
        "host_staging_required": True,
        "reason": "InfiniBand/RDMA disabled (NCCL_IB_DISABLE=1); falling back to POSIX TCP sockets via CPU",
    }


def filter_nccl_interfaces(candidates: Sequence[str], filter_spec: str) -> List[str]:
    """Evaluate `NCCL_SOCKET_IFNAME` or `NCCL_IB_HCA` filter syntax (`=`, `^`, `^=`).

    NCCL filter grammar:
    - No leading operator: prefix match on comma-separated tokens (`eth` matches `eth0`, `eth1`).
    - Leading `=`: exact match on comma-separated tokens (`=eth0` matches `eth0`, not `eth0.100`).
    - Leading `^`: exclude prefix match (`^docker,lo` excludes anything starting with `docker` or `lo`).
    - Leading `^=`: exclude exact match (`^=eth0,lo` excludes exact `eth0` and `lo`, keeps `eth0.100` and `eth1`).
    - For HCA port specs like `mlx5_0:1`, matching checks both the full string and the base HCA name before `:`.
    """
    spec = filter_spec.strip()
    if not spec:
        return list(candidates)

    exclude = False
    exact = False
    if spec.startswith("^="):
        exclude = True
        exact = True
        body = spec[2:]
    elif spec.startswith("^"):
        exclude = True
        exact = False
        body = spec[1:]
    elif spec.startswith("="):
        exclude = False
        exact = True
        body = spec[1:]
    else:
        body = spec

    tokens = [t.strip() for t in body.split(",") if t.strip()]
    if not tokens:
        raise NCCLTopologyEnvError(f"Empty token list in filter_spec: {filter_spec!r}")

    def matches_token(item: str, tok: str) -> bool:
        item_base = item.split(":")[0]
        if ":" in tok:
            return item == tok if exact else item.startswith(tok)
        if exact:
            return item == tok or item_base == tok
        return item.startswith(tok) or item_base.startswith(tok)

    selected: List[str] = []
    for cand in candidates:
        hit = any(matches_token(cand, tok) for tok in tokens)
        if exclude and not hit:
            selected.append(cand)
        elif not exclude and hit:
            selected.append(cand)
    return selected


def validate_socket_transport_limits(
    *,
    nsocks_perthread: int,
    socket_nthreads: int,
    num_nics: int = 1,
    single_nic_bw_gbps: float = 800.0,
) -> Dict[str, object]:
    """Validate `NCCL_NSOCKS_PERTHREAD * NCCL_SOCKET_NTHREADS <= 64` and compute multirail aggregate bandwidth."""
    if nsocks_perthread < 1 or socket_nthreads < 1:
        raise NCCLTopologyEnvError("nsocks_perthread and socket_nthreads must be >= 1")
    if num_nics < 1:
        raise NCCLTopologyEnvError("num_nics must be >= 1")

    total_sockets = nsocks_perthread * socket_nthreads
    max_allowed_sockets = 64
    is_valid = total_sockets <= max_allowed_sockets
    clamped_sockets = min(total_sockets, max_allowed_sockets)
    aggregate_gbps = num_nics * single_nic_bw_gbps
    aggregate_tbps = aggregate_gbps / 1000.0

    return {
        "nsocks_perthread": nsocks_perthread,
        "socket_nthreads": socket_nthreads,
        "total_sockets": total_sockets,
        "max_allowed_sockets": max_allowed_sockets,
        "within_nccl_64_limit": is_valid,
        "effective_sockets": clamped_sockets,
        "num_nics": num_nics,
        "single_nic_bw_gbps": single_nic_bw_gbps,
        "aggregate_bw_gbps": round(aggregate_gbps, 2),
        "aggregate_bw_tbps": round(aggregate_tbps, 2),
    }


def evaluate_numa_and_k8s_topology_manager(
    *,
    num_numa_nodes: int = 2,
    cores_per_numa: int = 64,
    gpus_per_numa: int = 4,
    os_reserved_cores_on_numa1: int = 2,
    pod_cpu_request: int = 16,
    pod_gpu_request: int = 1,
    num_pods_to_schedule: int = 8,
    policy: str = "single-numa-node",
    nccl_ignore_cpu_affinity: int = 1,
) -> Dict[str, object]:
    """Simulate Kubernetes `Topology Manager` (`single-numa-node`) pod admission and `NCCL_IGNORE_CPU_AFFINITY`.

    Reproduces the Volume 07 Chapter 8 production incident on a 128-core, 8-GPU dual-socket
    HGX server:
    - NUMA 0 has 64 cores and 4 GPUs (Pods 1-4 take 4 * 16 = 64 cores and GPUs 0-3).
    - NUMA 1 has 64 cores and 4 GPUs, with 2 cores used by OS/DaemonSets (62 free cores).
    - Pods 5, 6, 7 take 3 * 16 = 48 cores (leaving 62 - 48 = 14 free cores and 1 empty GPU).
    - When Pod 8 (or the 5th pod targeting a NUMA node with only 14 free cores) requests 16 cores,
      `single-numa-node` rejects it with `TopologyAffinityError` rather than crossing UPI.
    - Reducing `pod_cpu_request` to 12 cores schedules all 8 pods (`4 * 12 = 48 <= 62` cores/NUMA).
    """
    if policy not in {"none", "best-effort", "restricted", "single-numa-node"}:
        raise NCCLTopologyEnvError(f"Unsupported Topology Manager policy: {policy!r}")

    free_cores = [cores_per_numa for _ in range(num_numa_nodes)]
    if num_numa_nodes >= 2:
        free_cores[1] = max(0, free_cores[1] - os_reserved_cores_on_numa1)
    free_gpus = [gpus_per_numa for _ in range(num_numa_nodes)]

    admitted_pods = 0
    rejected_pods = 0
    first_failure_reason = ""

    for pod_idx in range(1, num_pods_to_schedule + 1):
        placed = False
        for nid in range(num_numa_nodes):
            if free_gpus[nid] >= pod_gpu_request and free_cores[nid] >= pod_cpu_request:
                free_gpus[nid] -= pod_gpu_request
                free_cores[nid] -= pod_cpu_request
                admitted_pods += 1
                placed = True
                break
        if not placed:
            if policy in {"single-numa-node", "restricted"}:
                rejected_pods += 1
                if not first_failure_reason:
                    first_failure_reason = (
                        f"TopologyAffinityError on Pod {pod_idx}: requires {pod_cpu_request} cores + "
                        f"{pod_gpu_request} GPU on a single NUMA node, but remaining per-NUMA cores={free_cores} "
                        f"and GPUs={free_gpus}"
                    )
            else:
                # none / best-effort allows cross-NUMA placement across UPI
                total_free_cores = sum(free_cores)
                total_free_gpus = sum(free_gpus)
                if total_free_cores >= pod_cpu_request and total_free_gpus >= pod_gpu_request:
                    admitted_pods += 1
                else:
                    rejected_pods += 1

    recommended_cores_per_pod = (cores_per_numa - os_reserved_cores_on_numa1) // gpus_per_numa
    return {
        "policy": policy,
        "total_server_cores": num_numa_nodes * cores_per_numa,
        "total_server_gpus": num_numa_nodes * gpus_per_numa,
        "pod_cpu_request": pod_cpu_request,
        "admitted_pods": admitted_pods,
        "rejected_pods": rejected_pods,
        "remaining_free_cores_per_numa": free_cores,
        "remaining_free_gpus_per_numa": free_gpus,
        "status": "TopologyAffinityError" if rejected_pods > 0 else "AllPodsRunning",
        "first_failure_reason": first_failure_reason,
        "recommended_max_cores_per_pod": recommended_cores_per_pod,
        "nccl_ignore_cpu_affinity": nccl_ignore_cpu_affinity == 1,
    }


if __name__ == "__main__":
    print("Chapter 12.16 model loaded: NCCL topology, channels, transports, and environment variables.")
