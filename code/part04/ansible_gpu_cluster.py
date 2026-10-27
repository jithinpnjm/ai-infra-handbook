"""Chapter 4.17 model: GPU node bring-up dependency DAG validator, fleet
`nvidia-smi` health-sweep outlier detector, and `nccl-tests` (`all_reduce_perf`)
bus-bandwidth parser and gate.

Sources modeled:
- Chris Fregly, AI Systems Performance Engineering (ai-systems-performance-
  engineering, ASP), Chapter 3 ("OS, Docker, and Kubernetes Tuning for GPU-Based
  Environments"):
  * CPU `performance` governor and disabling deep C-states (preventing GPU
    bubbles), NUMA locality (`nvidia-smi topo -m`, Grace Blackwell NVLink-C2C
    900 GB/s, NVL72 130 TB/s aggregate / 1.8 TB/s per GPU), `vm.swappiness=1`,
    checkpoint write-back tuning (`vm.dirty_background_ratio`, `vm.dirty_ratio`),
    `jemalloc`/`tcmalloc`, `nvidia-persistenced`, ECC (`-e 1`), locked clocks
    (`-lgc`) for benchmarks, Blackwell B200 MIG profiles (`1g.23gb`, `1g.45gb`,
    `2g.45gb`, `3g.90gb`, `4g.90gb`, `7g.180gb`), `/dev/shm` sizing for NCCL,
    and Kubernetes `--topology-manager-policy` + `--cpu-manager-policy=static`.
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR).
- volume-10/04-ansible-for-infrastructure-automation.md.
"""
import re
from typing import Dict, List, Mapping, Sequence, Tuple


REQUIRED_PRECEDENCE_PAIRS: Sequence[Tuple[str, str]] = (
    ("gpu_facts", "mofed"),
    ("base_os", "kernel_tuning"),
    ("kernel_tuning", "mofed"),
    ("mofed", "nvidia_driver"),
    ("nvidia_driver", "fabric_manager"),
    ("nvidia_driver", "gpu_tuning"),
    ("fabric_manager", "dcgm"),
    ("dcgm", "gpu_validate"),
    ("container_toolkit", "gpu_validate"),
    ("gpu_validate", "slurm_client"),
)


def validate_bringup_role_order(role_sequence: Sequence[str]) -> List[str]:
    """Verify that `role_sequence` satisfies all hardware/kernel/driver/validation
    dependency edges from Section 1 (`mofed` before `nvidia_driver` for
    `nvidia-peermem`, `nvidia_driver` before `fabric_manager`, `gpu_validate`
    before `slurm_client`).
    """
    violations: List[str] = []
    pos = {r: idx for idx, r in enumerate(role_sequence)}
    for earlier, later in REQUIRED_PRECEDENCE_PAIRS:
        if earlier in pos and later in pos and pos[earlier] > pos[later]:
            violations.append(f"{earlier} must run before {later}")
    return violations


def evaluate_gpu_health_sweep(
    host_csv_rows: Mapping[str, Sequence[str]],
    expected_gpus: int = 8,
    expected_driver_prefix: str = "550.",
    expected_pcie_gen: int = 5,
    expected_pcie_width: int = 16,
) -> Dict[str, List[str]]:
    """Model Section 6 fleet health sweep over `nvidia-smi --query-gpu=index,name,
    driver_version,temperature.gpu,power.draw,clocks_throttle_reasons.active,
    ecc.errors.uncorrected.volatile.total,pcie.link.gen.current,pcie.link.width.current`.
    Returns `{hostname: [reasons...]}` for any unhealthy node.
    """
    outliers: Dict[str, List[str]] = {}
    for host, rows in sorted(host_csv_rows.items()):
        reasons: List[str] = []
        if len(rows) != expected_gpus:
            reasons.append(f"gpu_count={len(rows)} (expected {expected_gpus})")
        for row in rows:
            parts = [p.strip() for p in row.split(",")]
            if len(parts) < 9:
                reasons.append(f"malformed row: {row!r}")
                continue
            idx, _, drv, temp_s, _, throttle, uncorr_ecc_s, pcie_gen_s, pcie_width_s = parts[:9]
            if not drv.startswith(expected_driver_prefix):
                reasons.append(f"gpu{idx}: driver={drv} (expected {expected_driver_prefix}*)")
            if int(uncorr_ecc_s) > 0:
                reasons.append(f"gpu{idx}: uncorrected_ecc={uncorr_ecc_s}")
            if int(pcie_gen_s) < expected_pcie_gen or int(pcie_width_s) < expected_pcie_width:
                reasons.append(f"gpu{idx}: pcie=Gen{pcie_gen_s}x{pcie_width_s} (expected Gen{expected_pcie_gen}x{expected_pcie_width})")
            if int(temp_s) >= 85:
                reasons.append(f"gpu{idx}: high_temp={temp_s}C")
            if throttle not in {"0x0000000000000000", "0x0000000000000001"}:  # 0x1 is GpuIdle
                reasons.append(f"gpu{idx}: active_throttle={throttle}")
        if reasons:
            outliers[host] = reasons
    return outliers


def parse_and_gate_nccl_busbw(nccl_stdout: str, min_busbw_gbps: float) -> Tuple[bool, float]:
    """Model Section 5 `all_reduce_perf` `Avg bus bandwidth` regex extraction and assertion."""
    m = re.search(r"Avg bus bandwidth\s*:\s*([0-9.]+)", nccl_stdout)
    if not m:
        raise ValueError("Avg bus bandwidth line not found in nccl-tests output")
    busbw = float(m.group(1))
    return (busbw >= min_busbw_gbps), busbw
