"""Customer-side SLIs from Token Factory Observability samples.

The Observability dashboards document these per-window series for a dedicated
endpoint: requests per minute, error rate by status code, TTFT and end-to-end
latency at p50/p90/p99, active replicas and GPU utilisation (avg, busiest).
Latency arrives as three percentiles per window, not as a histogram. So a
"fraction of requests under T seconds" can only be bounded, not computed.
Field names below are this module's own. Nebius has not documented the
federated metric names, so map your scraped series onto Sample yourself.

Run: python3 c37_customer_slis.py
"""
from __future__ import annotations

from dataclasses import dataclass, field


class SliInputError(ValueError):
    """Samples are missing, inconsistent or out of order."""


@dataclass
class Sample:
    minute: int                      # window start, minutes since some epoch
    requests: float                  # requests in the window
    errors: dict = field(default_factory=dict)   # {"429": n, "503": n, ...}
    streaming_requests: float = 0.0  # TTFT is measured on streaming only
    ttft_p50: float = 0.0            # seconds
    ttft_p90: float = 0.0
    ttft_p99: float = 0.0
    active_replicas: int = 0
    gpu_util_avg: float = 0.0        # 0..1
    gpu_util_busiest: float = 0.0


def validate(samples):
    if not samples:
        raise SliInputError("no samples")
    last = None
    for s in samples:
        if last is not None and s.minute <= last:
            raise SliInputError("samples must be strictly increasing in time")
        last = s.minute
        if s.requests < 0 or any(v < 0 for v in s.errors.values()):
            raise SliInputError("negative count")
        if sum(s.errors.values()) > s.requests + 1e-9:
            raise SliInputError(f"minute {s.minute}: more errors than requests")
        if s.streaming_requests > s.requests:
            raise SliInputError(f"minute {s.minute}: streaming exceeds requests")
        if not s.ttft_p50 <= s.ttft_p90 <= s.ttft_p99:
            raise SliInputError(f"minute {s.minute}: percentiles not ordered")


def _split(s: Sample):
    server = sum(v for k, v in s.errors.items() if k.startswith("5"))
    capacity = s.errors.get("429", 0.0)
    client = sum(v for k, v in s.errors.items() if k.startswith("4") and k != "429")
    return server, capacity, client


def availability_sli(samples, count_429_as_bad=False):
    """Good / valid. Client 4xx are not valid events. 5xx are always bad.
    429 is bad only if you decide the endpoint was overloaded (see 20.19)."""
    validate(samples)
    good = valid = 0.0
    for s in samples:
        server, cap, client = _split(s)
        v = s.requests - client
        bad = server + (cap if count_429_as_bad else 0.0)
        valid += v
        good += v - bad
    if valid == 0:
        raise SliInputError("no valid requests")
    return good / valid


def fraction_below_bounds(p50, p90, p99, limit):
    """Bounds on P(latency <= limit) implied by three percentiles."""
    if limit >= p99:
        return 0.99, 1.0
    if limit >= p90:
        return 0.90, 0.99
    if limit >= p50:
        return 0.50, 0.90
    return 0.0, 0.50


def ttft_sli_bounds(samples, limit_s):
    """Request-weighted lower and upper bound of the share of streams whose
    first token arrived within limit_s."""
    validate(samples)
    lo = hi = total = 0.0
    for s in samples:
        n = s.streaming_requests
        if n == 0:
            continue
        a, b = fraction_below_bounds(s.ttft_p50, s.ttft_p90, s.ttft_p99, limit_s)
        lo += a * n
        hi += b * n
        total += n
    if total == 0:
        raise SliInputError("no streaming requests")
    return lo / total, hi / total


def verdict(lo, hi, slo):
    if lo >= slo:
        return "met"
    if hi < slo:
        return "missed"
    return "indeterminate"


def burn_rate(sli, slo):
    """Budget consumption speed: 1.0 means the budget lasts exactly the period."""
    if not 0 < slo < 1:
        raise SliInputError("slo must be between 0 and 1")
    return (1 - sli) / (1 - slo)


def capacity_flags(samples, max_replicas, skew_limit=0.25, util_limit=0.85):
    """Windows where the endpoint was at its replica ceiling and hot, or lopsided."""
    validate(samples)
    flags = []
    for s in samples:
        if s.active_replicas >= max_replicas and s.gpu_util_avg >= util_limit:
            flags.append((s.minute, "at ceiling and hot"))
        elif s.gpu_util_busiest - s.gpu_util_avg > skew_limit:
            flags.append((s.minute, "one replica far busier than average"))
    return flags


def synthetic_samples():
    """60 minutes shaped like a 503 burst in minutes 20-29. Invented, not measured."""
    out = []
    for m in range(60):
        burst = 20 <= m < 30
        req = 1200.0
        errs = {"503": 300.0} if burst else {"429": 6.0}
        out.append(Sample(
            minute=m, requests=req, errors=errs, streaming_requests=900.0,
            ttft_p50=0.35, ttft_p90=0.8 if not burst else 1.6,
            ttft_p99=1.4 if not burst else 4.0, active_replicas=4,
            gpu_util_avg=0.6, gpu_util_busiest=0.7))
    return out


def main():
    samples = synthetic_samples()
    a = availability_sli(samples)
    lo, hi = ttft_sli_bounds(samples, 1.0)
    print(f"availability SLI {a:.4f}  burn vs 99.9%: {burn_rate(a, 0.999):.1f}")
    print(f"TTFT<=1.0s SLI bounds {lo:.3f}..{hi:.3f}  vs 99%: {verdict(lo, hi, 0.99)}")


if __name__ == "__main__":
    main()
