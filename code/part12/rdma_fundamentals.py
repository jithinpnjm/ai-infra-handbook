#!/usr/bin/env python3
"""Chapter 12.2 model: RDMA fundamentals: verbs, queue pairs and memory registration.

Encodes the verifiable RDMA execution model, Queue Pair (QP) state machine,
Protection Domains (PD) and Memory Regions (MR) with `lkey`/`rkey` and MTT/page-pinning
calculations, Send/Receive vs one-sided RDMA Write (13-step CM lifecycle) and RDMA Read
(11-step CM lifecycle), transport service types (`RC`, `UC`, `UD`, `DC`), `BTH`/`RETH`/`AETH`
header decoding, `ibv_devinfo -v` capability checks, and `perftest` (`ib_write_bw`) efficiency
metrics from:
- `nvidia-devops` Volume 08 (`chapter-03-verbs-queue-pairs-and-completion-queues.md`,
  `chapter-12-volume-08-summary.md`, `index.md`, `labs/lab-01..04`).
- `nvidia-devops` Volume 07 (`chapter-04-dma-rdma-and-peer-to-peer.md`) and
  Legacy Volume 06 (`volume-06/01-ai-networking-rdma-masterclass.md`).
- *AI Data Center Network Design and Technologies* (`ai-data-center-network-design-and-technologies`),
  Chapter 1 (*Wonders in the Workload*, Figures 1-7 to 1-16) and Chapter 7 (*RoCEv2 Transport and Congestion Management*).
- *Supercomputers for Linux SysAdmins* (`supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to`),
  Chapter 5 (*InfiniBand*) and Chapter 24 (*Node Setup and Software Installation*, `memlock unlimited`).
- *NVIDIA Base Command Manager 11 Installation Manual* (`bcm11-install`, Chapter 10 *OFED Software Stack*)
  and *Administrator Manual* (`bcm11-admin`, §3.6, §5.3.3, §9.6).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


class RDMAModelError(ValueError):
    """Raised when invalid RDMA verbs, queue pair, memory region, or header inputs are supplied."""


@dataclass(frozen=True)
class VerbsHcaProfile:
    """Adapter capability profile matching the illustrative ibv_devinfo -v output in V8 Ch 3 & Lab 01."""

    hca_id: str
    transport: str
    fw_ver: str
    node_guid: str
    sys_image_guid: str
    vendor_id_hex: str
    vendor_part_id: int
    max_mr_size_hex: str
    max_qp: int
    max_qp_wr: int
    max_sge: int
    max_cq: int
    max_cqe: int
    max_mr: int
    atomic_cap: str
    port_state: str
    max_mtu: int
    active_mtu: int
    phys_state: str
    link_layer: str


V8_CH3_MLX5_PROFILE = VerbsHcaProfile(
    hca_id="mlx5_0",
    transport="InfiniBand (0)",
    fw_ver="28.39.2048",
    node_guid="08c0:eb03:00f1:a2c3",
    sys_image_guid="08c0:eb03:00f1:a2c3",
    vendor_id_hex="0x02c9",
    vendor_part_id=4129,
    max_mr_size_hex="0xffffffffffffffff",
    max_qp=262144,
    max_qp_wr=32768,
    max_sge=30,
    max_cq=16777216,
    max_cqe=4194303,
    max_mr=16777216,
    atomic_cap="ATOMIC_HCA (1)",
    port_state="PORT_ACTIVE (4)",
    max_mtu=4096,
    active_mtu=4096,
    phys_state="LINK_UP (5)",
    link_layer="InfiniBand",
)


@dataclass(frozen=True)
class TransportServiceSpec:
    """RDMA transport service type characteristics (V8 Ch 3, SCL Ch 5, and DC comparison)."""

    code: str
    name: str
    connection_model: str
    reliable: bool
    ordered: bool
    supports_send_recv: bool
    supports_rdma_write: bool
    supports_rdma_read: bool
    supports_atomics: bool
    qps_per_process_for_n_peers_formula: str


TRANSPORT_SERVICES: Dict[str, TransportServiceSpec] = {
    "RC": TransportServiceSpec(
        code="RC",
        name="Reliable Connected",
        connection_model="One dedicated logical peer QP per local QP (1:1 connected)",
        reliable=True,
        ordered=True,
        supports_send_recv=True,
        supports_rdma_write=True,
        supports_rdma_read=True,
        supports_atomics=True,
        qps_per_process_for_n_peers_formula="N - 1 (scales as O(N^2) cluster-wide)",
    ),
    "UC": TransportServiceSpec(
        code="UC",
        name="Unreliable Connected",
        connection_model="One dedicated logical peer QP per local QP (1:1 connected, no ACK/retry)",
        reliable=False,
        ordered=True,
        supports_send_recv=True,
        supports_rdma_write=True,
        supports_rdma_read=False,
        supports_atomics=False,
        qps_per_process_for_n_peers_formula="N - 1 (scales as O(N^2) cluster-wide)",
    ),
    "UD": TransportServiceSpec(
        code="UD",
        name="Unreliable Datagram",
        connection_model="Connectionless; addressed per message via Address Handle (1:M)",
        reliable=False,
        ordered=False,
        supports_send_recv=True,
        supports_rdma_write=False,
        supports_rdma_read=False,
        supports_atomics=False,
        qps_per_process_for_n_peers_formula="1 (single QP reaches any peer up to single-MTU payload)",
    ),
    "DC": TransportServiceSpec(
        code="DC",
        name="Dynamic Connected",
        connection_model="Dynamically connects to remote DC target (DCT) per burst (1:M connected)",
        reliable=True,
        ordered=True,
        supports_send_recv=True,
        supports_rdma_write=True,
        supports_rdma_read=True,
        supports_atomics=True,
        qps_per_process_for_n_peers_formula="O(1) initiator QPs (avoids O(N^2) QP context explosion)",
    ),
}


VALID_QP_TRANSITIONS: Dict[str, Tuple[str, ...]] = {
    "RESET": ("INIT",),
    "INIT": ("RTR", "ERR", "RESET"),
    "RTR": ("RTS", "ERR", "RESET"),
    "RTS": ("SQD", "ERR", "RESET"),
    "SQD": ("RTS", "ERR", "RESET"),
    "ERR": ("RESET",),
}


def validate_qp_transition(
    current_state: str,
    target_state: str,
    *,
    local_port: Optional[int] = None,
    pkey_index: Optional[int] = None,
    local_active_mtu: int = 4096,
    requested_path_mtu: Optional[int] = None,
    dest_qp_num: Optional[int] = None,
    rq_psn: Optional[int] = None,
    remote_lid_or_gid_valid: bool = True,
    sq_psn: Optional[int] = None,
    retry_cnt: Optional[int] = None,
    rnr_retry: Optional[int] = None,
) -> Dict[str, object]:
    """Validate a Queue Pair state transition and required ibv_modify_qp attributes (V8 Ch 3 & V9 Ch 3)."""
    cur = current_state.strip().upper()
    tgt = target_state.strip().upper()
    if cur not in VALID_QP_TRANSITIONS or tgt not in VALID_QP_TRANSITIONS:
        raise RDMAModelError(f"Unknown QP state in transition {cur!r} -> {tgt!r}")
    if tgt not in VALID_QP_TRANSITIONS[cur]:
        return {
            "allowed": False,
            "next_state": cur,
            "errno": "EINVAL",
            "reason": f"Illegal QP state transition {cur} -> {tgt}",
        }

    if cur == "RESET" and tgt == "INIT":
        if local_port is None or local_port < 1 or pkey_index is None or pkey_index < 0:
            return {
                "allowed": False,
                "next_state": cur,
                "errno": "EINVAL",
                "reason": "RESET -> INIT requires valid local port (>= 1) and pkey_index (>= 0)",
            }

    if cur == "INIT" and tgt == "RTR":
        if (
            requested_path_mtu not in (256, 512, 1024, 2048, 4096)
            or dest_qp_num is None
            or dest_qp_num <= 0
            or rq_psn is None
            or rq_psn < 0
            or not remote_lid_or_gid_valid
        ):
            return {
                "allowed": False,
                "next_state": cur,
                "errno": "EINVAL",
                "reason": "INIT -> RTR requires valid path_mtu, dest_qp_num (> 0), rq_psn, and remote LID/GID",
            }
        if requested_path_mtu > local_active_mtu:
            return {
                "allowed": False,
                "next_state": cur,
                "errno": "EINVAL",
                "reason": (
                    f"Failed to modify QP to RTR: requested path_mtu ({requested_path_mtu}) "
                    f"exceeds port active_mtu ({local_active_mtu})"
                ),
            }

    if cur == "RTR" and tgt == "RTS":
        if (
            sq_psn is None
            or sq_psn < 0
            or retry_cnt is None
            or not (0 <= retry_cnt <= 7)
            or rnr_retry is None
            or not (0 <= rnr_retry <= 7)
        ):
            return {
                "allowed": False,
                "next_state": cur,
                "errno": "EINVAL",
                "reason": "RTR -> RTS requires valid sq_psn (>= 0), retry_cnt (0..7), and rnr_retry (0..7)",
            }

    return {
        "allowed": True,
        "next_state": tgt,
        "errno": "SUCCESS",
        "reason": f"Transition {cur} -> {tgt} succeeded",
    }


def analyze_cq_completion_stream(
    completions: List[Tuple[int, str, str, int]],
) -> Dict[str, object]:
    """Identify the root-cause completion before QP error flushing (V8 Ch 3 Scenario 4).

    Each item is (wr_id, status_code, opcode, vendor_err).
    """
    if not completions:
        raise RDMAModelError("completions list must not be empty")

    success_count = 0
    first_failure: Optional[Tuple[int, str, str, int]] = None
    flushed_wr_ids: List[int] = []

    for wr_id, status, opcode, vendor_err in completions:
        if status == "IBV_WC_SUCCESS":
            success_count += 1
        elif status == "IBV_WC_WR_FLUSH_ERR":
            flushed_wr_ids.append(wr_id)
        elif first_failure is None:
            first_failure = (wr_id, status, opcode, vendor_err)

    if first_failure is None:
        fault_domain = "HEALTHY"
    elif first_failure[1] in ("IBV_WC_LOC_PROT_ERR", "IBV_WC_LOC_LEN_ERR", "IBV_WC_LOC_QP_OP_ERR"):
        fault_domain = "LOCAL_ENDPOINT_MEMORY_OR_WQE"
    elif first_failure[1] in ("IBV_WC_REM_ACCESS_ERR", "IBV_WC_REM_INV_REQ_ERR", "IBV_WC_REM_OP_ERR"):
        fault_domain = "REMOTE_ENDPOINT_MEMORY_OR_KEY"
    elif first_failure[1] == "IBV_WC_RNR_RETRY_EXC_ERR":
        fault_domain = "REMOTE_RECEIVE_QUEUE_STARVATION"
    elif first_failure[1] == "IBV_WC_RETRY_EXC_ERR":
        fault_domain = "TRANSPORT_ACK_TIMEOUT_PEER_OR_PATH"
    else:
        fault_domain = "OTHER_TRANSPORT_ERROR"

    return {
        "total_cqes": len(completions),
        "success_count": success_count,
        "first_failing_wr_id": first_failure[0] if first_failure else None,
        "first_failing_status": first_failure[1] if first_failure else None,
        "first_failing_opcode": first_failure[2] if first_failure else None,
        "first_failing_vendor_err_hex": f"0x{first_failure[3]:02x}" if first_failure else None,
        "flushed_count": len(flushed_wr_ids),
        "flushed_wr_ids": flushed_wr_ids,
        "fault_domain": fault_domain,
    }


def evaluate_memory_registration_and_mtt(
    buffer_bytes: int,
    page_size_bytes: int = 4096,
    mtt_entry_bytes: int = 8,
    pd_match: bool = True,
    key_valid: bool = True,
    access_offset_bytes: int = 0,
    access_length_bytes: int = 4096,
    is_remote_op: bool = False,
    remote_access_authorized: bool = True,
    memlock_limit_bytes: Optional[int] = None,
) -> Dict[str, object]:
    """Calculate pinned pages, MTT footprint, memlock gate, and PD/MR access validity (V8 Ch 3 & SCL Ch 24)."""
    if buffer_bytes <= 0 or page_size_bytes <= 0 or mtt_entry_bytes <= 0:
        raise RDMAModelError("buffer_bytes, page_size_bytes, and mtt_entry_bytes must be positive")
    if access_offset_bytes < 0 or access_length_bytes < 0:
        raise RDMAModelError("access_offset_bytes and access_length_bytes must be non-negative")

    num_pages = math.ceil(buffer_bytes / page_size_bytes)
    mtt_table_bytes = num_pages * mtt_entry_bytes
    memlock_ok = True if memlock_limit_bytes is None else (buffer_bytes <= memlock_limit_bytes)

    if not memlock_ok:
        cqe_status = "IBV_REG_MR_ENOMEM_MEMLOCK"
    elif not pd_match:
        cqe_status = "IBV_WC_LOC_PROT_ERR"
    elif not key_valid:
        cqe_status = "IBV_WC_REM_ACCESS_ERR" if is_remote_op else "IBV_WC_LOC_PROT_ERR"
    elif is_remote_op and not remote_access_authorized:
        cqe_status = "IBV_WC_REM_ACCESS_ERR"
    elif access_offset_bytes + access_length_bytes > buffer_bytes:
        cqe_status = "IBV_WC_REM_ACCESS_ERR" if is_remote_op else "IBV_WC_LOC_PROT_ERR"
    else:
        cqe_status = "IBV_WC_SUCCESS"

    return {
        "buffer_bytes": buffer_bytes,
        "page_size_bytes": page_size_bytes,
        "num_pinned_pages": num_pages,
        "mtt_table_bytes": mtt_table_bytes,
        "memlock_ok": memlock_ok,
        "cqe_status": cqe_status,
    }


def trace_rdma_cm_session_steps(operation: str) -> Dict[str, object]:
    """Return the exact CM handshake, data transfer, and teardown steps from ADC Ch 1 Figs 1-12 and 1-13."""
    op = operation.strip().upper()
    if op == "RDMA_WRITE":
        steps = [
            (1, "Handshake", "Client -> Server", "CM: Connect request with client QPN"),
            (2, "Handshake", "Server -> Client", "CM: Connect reply with server QPN"),
            (3, "Handshake", "Client -> Server", "CM: Ready to use (Connection established)"),
            (4, "RDMA Write", "Client -> Server", "Transfer size and remote address information"),
            (5, "RDMA Write", "Server -> Client", "Acknowledgement"),
            (6, "RDMA Write", "Client -> Server", "Memory region information"),
            (7, "RDMA Write", "Server -> Client", "Acknowledgement"),
            (8, "RDMA Write", "Client -> Server", "Data"),
            (9, "RDMA Write", "Server -> Client", "Acknowledgement"),
            (10, "Terminate", "Client -> Server", "CM: Disconnect request with server QPN"),
            (11, "Terminate", "Server -> Client", "CM: Disconnect reply"),
            (12, "Terminate", "Client -> Server", "CM: Disconnect request with client QPN"),
            (13, "Terminate", "Server -> Client", "CM: Disconnect reply"),
        ]
    elif op == "RDMA_READ":
        steps = [
            (1, "Handshake", "Client (20.0.0.2) -> Server (60.0.0.2)", "CM: Connect request with client QPN"),
            (2, "Handshake", "Server (60.0.0.2) -> Client (20.0.0.2)", "CM: Connect reply with server QPN"),
            (3, "Handshake", "Client (20.0.0.2) -> Server (60.0.0.2)", "CM: Ready to use (Connection established)"),
            (4, "RDMA Read", "Client -> Server", "Transfer size, remote address, and memory region information"),
            (5, "RDMA Read", "Server -> Client", "Acknowledgement"),
            (6, "RDMA Read", "Server -> Client", "Data"),
            (7, "RDMA Read", "Client -> Server", "Acknowledgement"),
            (8, "Terminate", "Client -> Server", "CM: Disconnect request with server QPN"),
            (9, "Terminate", "Server -> Client", "CM: Disconnect reply"),
            (10, "Terminate", "Server -> Client", "CM: Disconnect request with client QPN"),
            (11, "Terminate", "Client -> Server", "CM: Disconnect reply"),
        ]
    else:
        raise RDMAModelError(f"Unsupported CM session operation: {operation!r}")

    return {
        "operation": op,
        "total_steps": len(steps),
        "handshake_steps": 3,
        "transfer_steps": len(steps) - 7,
        "terminate_steps": 4,
        "steps": steps,
    }


BTH_OPCODES: Dict[int, str] = {
    12: "RC RDMA READ Request",
    14: "RC RDMA READ Response Middle",
    17: "RC Acknowledge",
    129: "RoCEv2 Congestion Notification Packet (CNP)",
}


def decode_rdma_transport_headers(
    *,
    bth_opcode: int,
    solicited_event: bool,
    mig_req: bool,
    pad_count: int,
    header_version: int,
    pkey: int,
    dest_qp: int,
    ack_req: bool,
    psn: int,
    icrc: int,
    reth_va: Optional[int] = None,
    reth_rkey: Optional[int] = None,
    reth_dma_len: Optional[int] = None,
    aeth_syndrome: Optional[int] = None,
    aeth_msn: Optional[int] = None,
    payload_bytes: int = 0,
) -> Dict[str, object]:
    """Decode BTH (12 B), optional RETH (16 B) or AETH (4 B), and ICRC (4 B) (ADC Ch 1 Figs 1-14..1-16 & VL6 Ch 1)."""
    if bth_opcode not in BTH_OPCODES:
        raise RDMAModelError(f"Unsupported BTH opcode: {bth_opcode}")
    if not (0 <= dest_qp <= 0xFFFFFF) or not (0 <= psn <= 0xFFFFFF):
        raise RDMAModelError("dest_qp and psn must fit in 24-bit unsigned integers")

    bth_bytes = 12
    icrc_bytes = 4
    ext_header_type = "NONE"
    ext_header_bytes = 0

    if bth_opcode == 12:
        if reth_va is None or reth_rkey is None or reth_dma_len is None:
            raise RDMAModelError("RC RDMA READ Request (opcode 12) requires RETH fields (va, rkey, dma_len)")
        ext_header_type = "RETH"
        ext_header_bytes = 16
    elif bth_opcode == 17:
        if aeth_syndrome is None or aeth_msn is None:
            raise RDMAModelError("RC Acknowledge (opcode 17) requires AETH fields (syndrome, msn)")
        ext_header_type = "AETH"
        ext_header_bytes = 4

    is_ack = (aeth_syndrome is not None) and ((aeth_syndrome >> 5) & 0b11 == 0)

    return {
        "opcode": bth_opcode,
        "opcode_name": BTH_OPCODES[bth_opcode],
        "solicited_event": solicited_event,
        "mig_req": mig_req,
        "pad_count": pad_count,
        "header_version": header_version,
        "pkey": pkey,
        "pkey_hex": f"0x{pkey:04x}",
        "dest_qp_hex": f"0x{dest_qp:06x}",
        "ack_req": ack_req,
        "psn": psn,
        "ext_header_type": ext_header_type,
        "ext_header_bytes": ext_header_bytes,
        "reth_va_hex": f"0x{reth_va:016x}" if reth_va is not None else None,
        "reth_rkey_hex": f"0x{reth_rkey:08x}" if reth_rkey is not None else None,
        "reth_dma_len": reth_dma_len,
        "aeth_syndrome": aeth_syndrome,
        "aeth_is_ack": is_ack if aeth_syndrome is not None else None,
        "aeth_msn": aeth_msn,
        "payload_bytes": payload_bytes,
        "icrc_hex": f"0x{icrc:08x}",
        "ib_transport_total_bytes": bth_bytes + ext_header_bytes + payload_bytes + icrc_bytes,
    }


def evaluate_qp_scaling_and_perftest(
    num_nodes: int,
    gpus_per_node: int,
    hca_max_qp: int = 262144,
    msg_size_bytes: int = 65536,
    bw_average_mb_per_sec: float = 23450.5,
    link_rate_gbps: float = 200.0,
) -> Dict[str, object]:
    """Compute cluster-wide RC QP mesh count and perftest message-rate / line-rate metrics (V8 Ch 3 & VL6 Ch 1)."""
    if num_nodes <= 0 or gpus_per_node <= 0 or hca_max_qp <= 0 or msg_size_bytes <= 0 or link_rate_gbps <= 0:
        raise RDMAModelError("All cluster and benchmark parameters must be positive")

    total_ranks = num_nodes * gpus_per_node
    rc_qps_per_rank = total_ranks - 1
    rc_qps_per_node = gpus_per_node * rc_qps_per_rank
    total_cluster_rc_qps = total_ranks * rc_qps_per_rank
    line_rate_mb_per_sec = (link_rate_gbps * 1000.0) / 8.0
    line_rate_utilization_pct = round((bw_average_mb_per_sec / line_rate_mb_per_sec) * 100.0, 2)
    msg_rate_mpps = round(bw_average_mb_per_sec / float(msg_size_bytes), 6)

    return {
        "total_ranks": total_ranks,
        "rc_qps_per_rank": rc_qps_per_rank,
        "rc_qps_per_node": rc_qps_per_node,
        "total_cluster_rc_qps": total_cluster_rc_qps,
        "exceeds_single_hca_max_qp": rc_qps_per_node > hca_max_qp,
        "line_rate_mb_per_sec": line_rate_mb_per_sec,
        "line_rate_utilization_pct": line_rate_utilization_pct,
        "msg_rate_mpps": msg_rate_mpps,
    }
