"""Chapter 5.24 model: Multi-window multi-burn-rate SLO alert evaluator,
Prometheus series cardinality & memory estimator, and `PK` Ch. 9 Requests vs
Consumption (`max(request, usage)`) showback calculator.

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 9 ("Observability"):
  * Logging mechanics: Node-agent (`Fluentd` / `Fluent Bit`) vs sidecar log
    shipping, Kubernetes `audit.k8s.io/v1` `Policy` levels (`None`, `Metadata`,
    `Request`, `RequestResponse`), and Kubernetes `Events` (`1h` TTL).
  * Metrics: Prometheus pull model vs `Pushgateway` for ephemeral batch jobs,
    Prometheus Operator CRDs (`Prometheus`, `ServiceMonitor`, `PrometheusRule`,
    `Alertmanager`), Federation vs `Thanos` (`Sidecar`, `Store Gateway`,
    `Compactor`, `Querier`, `Ruler`), and Dead Man's Switch (`Watchdog`) alert.
  * Showback and Chargeback (`Figure 9-5`): Requests-based showback vs
    Consumption-based showback (`max(requests, actual_usage)`).
  * Distributed Tracing (`OpenTracing` + `OpenCensus` -> `OpenTelemetry` /
    `Jaeger`: `Trace`, `Span`, `Tags`, `Logs`/`Baggage`, `Agent`, `Collector`).
"""
from typing import Any, Dict, List, Mapping, Sequence


def evaluate_slo_multiwindow_burn_rate(
    *,
    slo_target: float,
    error_ratio_5m: float,
    error_ratio_30m: float,
    error_ratio_1h: float,
    error_ratio_6h: float,
    fast_burn_multiplier: float = 14.4,
    slow_burn_multiplier: float = 6.0,
) -> Dict[str, Any]:
    """Model Section 3 Google SRE multi-window, multi-burn-rate SLO alerting:
    - `error_budget = 1.0 - slo_target` (e.g. `0.005` for `99.5%` SLO).
    - `fast_page`: fires ONLY when BOTH `1h` AND `5m` error ratios exceed
      `fast_burn_multiplier * error_budget` (2% of 30-day budget burned in 1h).
    - `slow_ticket`: fires ONLY when BOTH `6h` AND `30m` error ratios exceed
      `slow_burn_multiplier * error_budget` (5% of 30-day budget burned in 6h).
    """
    error_budget = round(1.0 - slo_target, 9)
    fast_threshold = round(fast_burn_multiplier * error_budget, 9)
    slow_threshold = round(slow_burn_multiplier * error_budget, 9)

    fast_page = (error_ratio_1h > fast_threshold) and (error_ratio_5m > fast_threshold)
    slow_ticket = (error_ratio_6h > slow_threshold) and (error_ratio_30m > slow_threshold)

    return {
        "error_budget": error_budget,
        "fast_threshold": fast_threshold,
        "slow_threshold": slow_threshold,
        "fast_page_firing": fast_page,
        "slow_ticket_firing": slow_ticket,
    }


def estimate_prometheus_series_cardinality(
    metric_count: int,
    label_cardinalities: Mapping[str, int],
    bytes_per_series_in_head: int = 3072,
) -> Dict[str, Any]:
    """Model Section 7 multiplicative Prometheus series cardinality explosion:
    `total_series = metric_count * product(label_cardinalities.values())`.
    Flags any label with cardinality > 1,000 as a high-cardinality hazard.
    """
    total_series = metric_count
    dangerous_labels: List[str] = []
    for lbl, card in sorted(label_cardinalities.items()):
        total_series *= int(card)
        if int(card) > 1000:
            dangerous_labels.append(lbl)

    head_mem_mb = round((total_series * bytes_per_series_in_head) / (1024 * 1024), 2)
    return {
        "total_series": total_series,
        "estimated_head_memory_mb": head_mem_mb,
        "dangerous_labels": dangerous_labels,
    }


def compute_showback_requests_vs_consumption(
    workloads: Sequence[Mapping[str, Any]],
) -> Dict[str, Dict[str, float]]:
    """Model PK Ch. 9 Figure 9-5 Showback models:
    - `requests_model`: attributes `requested` units to the team.
    - `consumption_model` (PK Ch. 9): attributes `max(requested, actual_usage)`
      to the workload so teams pay for reserved capacity AND any burst above
      requests.
    """
    by_team: Dict[str, Dict[str, float]] = {}
    for w in workloads:
        team = str(w["team"])
        req = float(w["requested"])
        use = float(w["actual_usage"])
        entry = by_team.setdefault(team, {"requests_showback": 0.0, "consumption_showback": 0.0})
        entry["requests_showback"] += req
        entry["consumption_showback"] += max(req, use)
    return by_team
