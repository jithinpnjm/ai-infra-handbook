"""Chapter 2.31 model: AI fabric per-rail bandwidth skew and ECMP uplink
coefficient-of-variation (stddev / mean) detector, In-Band Flow Analyzer (IFA)
per-hop residence-time and ECN congestion analyzer, and Prometheus time-series
cardinality and ingestion sample-rate calculator.

Sources modeled:
- Dinakaran Setty et al., AI Data Center Network Design and Technologies (ADC),
  Chapter 11 ("Monitoring and Telemetry": SNMP, syslog, streaming telemetry
  sample/on-change, TWAMP, sFlow/IPFIX, historical vs real-time monitoring,
  server+switch correlation, egress buffers, mirror-on-drop, In-Band Flow
  Analyzer IFA initiator/transit/terminator and draft-kumar-ippm-ifa-08,
  corrective actions).
- Brendan Gregg, Systems Performance, 2nd ed. (SP), Chapter 10.
- Christian Adell et al., Network Programmability and Automation, 2nd ed. (NPA),
  Chapters 10 and 14.
- nvidia-devops/volume-07 (observability masterclass).
"""
import math
from typing import Dict, List


def evaluate_rail_skew_and_ecmp_balance(
    rail_rates_gbps: List[float],
    skew_alert_threshold: float = 1.5,
) -> Dict[str, object]:
    """Compute max/min rail bandwidth skew ratio and coefficient of variation (stddev / mean)."""
    if not rail_rates_gbps or any(r <= 0 for r in rail_rates_gbps):
        raise ValueError("rail_rates_gbps must be non-empty positive numbers")
    max_r = max(rail_rates_gbps)
    min_r = min(rail_rates_gbps)
    skew_ratio = round(max_r / min_r, 2)
    mean_r = sum(rail_rates_gbps) / float(len(rail_rates_gbps))
    variance = sum((r - mean_r) ** 2 for r in rail_rates_gbps) / float(len(rail_rates_gbps))
    cv = round(math.sqrt(variance) / mean_r, 3)
    straggler_idx = rail_rates_gbps.index(min_r)
    return {
        "max_min_skew_ratio": skew_ratio,
        "coeff_of_variation": cv,
        "skew_alert_firing": skew_ratio > skew_alert_threshold,
        "straggler_rail_index": straggler_idx,
    }


def analyze_ifa_metadata_stack(hops: List[Dict[str, object]]) -> Dict[str, object]:
    """Analyze an In-Band Flow Analyzer (IFA) metadata stack of hop records
    ({'device_id', 'residence_ns', 'ecn_marked'}).
    """
    if not hops:
        raise ValueError("hops list must be non-empty")
    total_res_ns = sum(int(h["residence_ns"]) for h in hops)
    worst_hop = max(hops, key=lambda h: int(h["residence_ns"]))
    congested_hops = [str(h["device_id"]) for h in hops if bool(h.get("ecn_marked", False))]
    return {
        "hop_count": len(hops),
        "total_residence_ns": total_res_ns,
        "bottleneck_device": str(worst_hop["device_id"]),
        "bottleneck_residence_ns": int(worst_hop["residence_ns"]),
        "ecn_congested_devices": congested_hops,
    }


def estimate_telemetry_cardinality_and_rate(
    num_switches: int,
    ports_per_switch: int,
    metrics_per_port: int,
    sample_interval_sec: float,
) -> Dict[str, float]:
    """Estimate active time-series cardinality and ingestion rate in samples/sec."""
    if num_switches <= 0 or ports_per_switch <= 0 or metrics_per_port <= 0 or sample_interval_sec <= 0:
        raise ValueError("Telemetry sizing parameters must be positive")
    total_series = num_switches * ports_per_switch * metrics_per_port
    samples_per_sec = round(total_series / float(sample_interval_sec), 1)
    return {
        "active_series": float(total_series),
        "samples_per_sec": samples_per_sec,
    }
