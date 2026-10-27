"""Chapter 1.23 model: USE method triage ordering (errors -> saturation -> utilization),
Amdahl's law and Gunther's Universal Scalability Law (USL), Little's law (L = lambda * W),
M/D/1 queueing response time r = s * (2 - rho) / (2 * (1 - rho)), harmonic mean of
transfer rates, and resource-limit capacity extrapolation.

Sources modeled:
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 1 ("Introduction": 60-second checklist, case studies), Chapter 2
  ("Methodologies": USE, RED, workload characterization, drill-down, Amdahl/USL,
  Little's law, M/D/1 queueing, resource-limit capacity planning, harmonic mean),
  and Chapter 4 (observability taxonomy preview).
"""
from typing import Dict, List, Tuple


LINUX_60S_CHECKLIST: List[str] = [
    "uptime",
    "dmesg -T | tail",
    "vmstat -SM 1",
    "mpstat -P ALL 1",
    "pidstat 1",
    "iostat -sxz 1",
    "free -m",
    "sar -n DEV 1",
    "sar -n TCP,ETCP 1",
    "top",
]


def amdahl_relative_capacity(n_workers: int, alpha_serial: float) -> float:
    """Compute Amdahl's law relative capacity: C(N) = N / (1 + alpha * (N - 1))."""
    if n_workers < 1 or not (0.0 <= alpha_serial <= 1.0):
        raise ValueError("n_workers must be >= 1 and alpha_serial in [0, 1]")
    return round(n_workers / (1.0 + alpha_serial * (n_workers - 1)), 2)


def usl_relative_capacity(n_workers: int, alpha_contention: float, beta_coherence: float) -> float:
    """Compute Gunther's Universal Scalability Law: C(N) = N / (1 + alpha*(N-1) + beta*N*(N-1))."""
    if n_workers < 1 or alpha_contention < 0.0 or beta_coherence < 0.0:
        raise ValueError("Invalid USL parameters")
    denom = 1.0 + alpha_contention * (n_workers - 1) + beta_coherence * n_workers * (n_workers - 1)
    return round(n_workers / denom, 2)


def littles_law_in_flight(arrival_rate_per_sec: float, mean_time_in_system_sec: float) -> float:
    """Compute Little's law: L = lambda * W."""
    if arrival_rate_per_sec < 0.0 or mean_time_in_system_sec < 0.0:
        raise ValueError("Arrival rate and residence time must be non-negative")
    return round(arrival_rate_per_sec * mean_time_in_system_sec, 3)


def md1_response_time(service_time_s: float, utilization_rho: float) -> float:
    """Compute M/D/1 mean response time: r = s * (2 - rho) / (2 * (1 - rho))."""
    if service_time_s <= 0.0 or not (0.0 <= utilization_rho < 1.0):
        raise ValueError("service_time_s must be > 0 and utilization_rho in [0, 1)")
    return round(service_time_s * (2.0 - utilization_rho) / (2.0 * (1.0 - utilization_rho)), 3)


def weighted_harmonic_mean_rate(segments: List[Tuple[float, float]]) -> float:
    """Compute overall transfer rate for segments of (work_amount, rate_per_sec): sum(w) / sum(w / r)."""
    if not segments:
        raise ValueError("segments must be non-empty")
    total_work = 0.0
    total_time = 0.0
    for work, rate in segments:
        if work <= 0.0 or rate <= 0.0:
            raise ValueError("work and rate must be positive")
        total_work += work
        total_time += work / rate
    return round(total_work / total_time, 1)


def extrapolate_cpu_max_request_rate(
    current_req_per_sec: float,
    num_cpus: int,
    avg_cpu_util_pct: float,
) -> Dict[str, float]:
    """Extrapolate theoretical 100% CPU ceiling using Gregg's resource-limit method (SP Ch. 2.7.1)."""
    if current_req_per_sec <= 0 or num_cpus <= 0 or not (0.0 < avg_cpu_util_pct <= 100.0):
        raise ValueError("Invalid resource-limit parameters")
    total_cpu_pct = num_cpus * avg_cpu_util_pct
    cpu_pct_per_req = round(total_cpu_pct / current_req_per_sec, 4)
    max_req_per_sec = round((num_cpus * 100.0) / cpu_pct_per_req, 1)
    return {
        "cpu_pct_per_req": cpu_pct_per_req,
        "max_req_per_sec": max_req_per_sec,
    }
