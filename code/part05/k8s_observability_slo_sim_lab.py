#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.24: Observability for Kubernetes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from k8s_observability_slo_sim import (
    compute_showback_requests_vs_consumption,
    estimate_prometheus_series_cardinality,
    evaluate_slo_multiwindow_burn_rate,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Section 3: Multi-window multi-burn-rate SLO alerting (99.5% SLO -> 0.005 budget; fast=14.4x=0.072)
    # Active fast burn (both 1h and 5m > 0.072) -> page fires!
    active_burn = evaluate_slo_multiwindow_burn_rate(
        slo_target=0.995,
        error_ratio_5m=0.080,
        error_ratio_30m=0.080,
        error_ratio_1h=0.080,
        error_ratio_6h=0.020,
    )
    # Resolved spike (1h is still > 0.072, but 5m recovered to 0.001) -> fast_page immediately clears!
    resolved_burn = evaluate_slo_multiwindow_burn_rate(
        slo_target=0.995,
        error_ratio_5m=0.001,
        error_ratio_30m=0.040,
        error_ratio_1h=0.080,
        error_ratio_6h=0.010,
    )
    check(
        "evaluate_slo_multiwindow_burn_rate fires fast_page when both 1h & 5m > 0.072 and resets immediately when 5m recovers",
        active_burn["fast_threshold"] == 0.072
        and active_burn["fast_page_firing"] is True
        and resolved_burn["fast_page_firing"] is False,
    )

    # 2. Section 7: Multiplicative Prometheus cardinality explosion from high-cardinality user_id label
    safe_card = estimate_prometheus_series_cardinality(
        metric_count=10,
        label_cardinalities={"pod": 50, "method": 4, "status": 5},
    )
    exploded_card = estimate_prometheus_series_cardinality(
        metric_count=10,
        label_cardinalities={"pod": 50, "method": 4, "status": 5, "user_id": 50000},
    )
    check(
        "Adding a 50,000-user 'user_id' label explodes 10,000 series to 500,000,000 series (~1.46 TB head RAM) and flags 'user_id'",
        safe_card["total_series"] == 10_000
        and exploded_card["total_series"] == 500_000_000
        and exploded_card["dangerous_labels"] == ["user_id"],
    )

    # 3. PK Ch. 9 Figure 9-5: Requests-based vs Consumption-based (max(request, usage)) showback
    showback = compute_showback_requests_vs_consumption(
        [
            {"team": "team-a", "requested": 16.0, "actual_usage": 10.0},  # over-requested -> max(16,10)=16
            {"team": "team-a", "requested": 8.0, "actual_usage": 14.0},   # burst over request -> max(8,14)=14
        ]
    )
    check(
        "PK Ch. 9 showback attributes 24.0 under requests model and 30.0 (16 + 14) under consumption max(req, use) model",
        showback["team-a"] == {"requests_showback": 24.0, "consumption_showback": 30.0},
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
