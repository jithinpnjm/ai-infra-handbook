"""Chapter 2.18 model: 3-stage and 5-stage Clos non-blocking endpoint capacity
and switch/cable BOM calculator (R^2/2 and R^3/4), oversubscription ratio and
spine-loss surviving capacity ((S-1)/S), multidimensional torus diameter
(sum(d // 2)), and MTBF/MTTR availability and annual downtime calculator.

Sources modeled:
- Dinakaran Setty et al., AI Data Center Network Design and Technologies (ADC),
  Chapter 3 ("Network Design Considerations": 3-stage and 5-stage Clos sizing,
  rail-optimized / rail-only / rail-unified designs, ToR/MoR/EoR rack layouts,
  scheduled cell-based fabrics with VOQ, dragonfly and torus, multi-planar
  scale-out, inference vs training fabrics).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapters 19, 20, 22, 23, and 25 (failure domains, information hiding, network
  design patterns, MTBF/MTTR/availability nines, SRLGs, disaggregation and
  folded Clos fabrics).
"""
from typing import Dict, List


def size_clos3_fabric(radix: int, downlinks_per_leaf: int = 0) -> Dict[str, int]:
    """Compute max leaves, spines, endpoints, and cable counts for a 3-stage Clos of R-port switches."""
    if radix < 2 or radix % 2 != 0:
        raise ValueError("Switch radix must be a positive even integer")
    down = (radix // 2) if downlinks_per_leaf == 0 else downlinks_per_leaf
    up = radix - down
    if down <= 0 or up <= 0:
        raise ValueError("Invalid downlink/uplink split")
    spines = up
    leaves = radix
    endpoints = leaves * down
    leaf_spine_cables = leaves * up
    return {
        "radix": radix,
        "leaves": leaves,
        "spines": spines,
        "total_switches": leaves + spines,
        "max_endpoints": endpoints,
        "server_cables": endpoints,
        "leaf_spine_cables": leaf_spine_cables,
    }


def compute_5stage_max_endpoints_1to1(radix: int) -> int:
    """Compute theoretical 1:1 non-blocking max endpoints for a 5-stage Clos: R^3 // 4."""
    if radix < 2 or radix % 2 != 0:
        raise ValueError("Switch radix must be a positive even integer")
    return (radix ** 3) // 4


def compute_oversubscription_and_spine_loss(
    downlink_bw_gbps: float,
    uplink_bw_gbps: float,
    num_spines: int,
) -> Dict[str, float]:
    """Compute leaf oversubscription ratio (down / up) and surviving capacity % when 1 of num_spines fails."""
    if downlink_bw_gbps <= 0 or uplink_bw_gbps <= 0 or num_spines < 2:
        raise ValueError("Invalid bandwidth or spine count")
    oversub = round(downlink_bw_gbps / uplink_bw_gbps, 2)
    surviving_pct = round(100.0 * (num_spines - 1) / float(num_spines), 1)
    loss_pct = round(100.0 / float(num_spines), 1)
    return {
        "oversubscription_ratio": oversub,
        "surviving_capacity_pct": surviving_pct,
        "capacity_loss_pct": loss_pct,
    }


def compute_torus_diameter(dimensions: List[int]) -> int:
    """Compute worst-case hop count (diameter) of a k-D torus: sum(n_i // 2)."""
    if not dimensions or any(d <= 0 for d in dimensions):
        raise ValueError("dimensions must be non-empty positive integers")
    return sum(d // 2 for d in dimensions)


def compute_availability_and_downtime(mtbf_hours: float, mttr_hours: float) -> Dict[str, float]:
    """Compute availability = MTBF / (MTBF + MTTR) and expected downtime in minutes per 365-day year."""
    if mtbf_hours <= 0 or mttr_hours < 0:
        raise ValueError("Invalid MTBF or MTTR")
    avail = mtbf_hours / (mtbf_hours + mttr_hours)
    minutes_per_year = 365.0 * 24.0 * 60.0  # 525,600 minutes
    downtime_min_per_year = (1.0 - avail) * minutes_per_year
    return {
        "availability_pct": round(100.0 * avail, 4),
        "downtime_min_per_year": round(downtime_min_per_year, 1),
    }
