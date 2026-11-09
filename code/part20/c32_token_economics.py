"""Token Factory unit economics (chapter 20.32).

Rules come from the public Token Factory docs fetched 2026-11-09:
- Cached Tokens page: prompt tokens = uncached input + cached input, each billed once.
- Rate Limits page: a rolling 15-minute window, x1.2 up when usage >= 80 percent,
  divide by 1.5 when usage <= 50 percent, hard ceiling 20x the base allocation.
- Billing Policy page: the prose and the table disagree for partially ready capacity,
  so both readings are modelled.
Prices are always arguments. The numbers in the tests are placeholders, not Nebius prices.
"""
import math
from dataclasses import dataclass

PER_MILLION = 1_000_000
UP_FACTOR = 1.2
DOWN_DIVISOR = 1.5
UP_THRESHOLD = 0.80
DOWN_THRESHOLD = 0.50
CEILING_MULTIPLE = 20.0


def request_cost(prompt_tokens, cached_tokens, output_tokens,
                 input_price, cached_price, output_price):
    """Cost of one Serverless request. Prices are per million tokens."""
    if cached_tokens < 0 or cached_tokens > prompt_tokens:
        raise ValueError("cached_tokens must be between 0 and prompt_tokens")
    uncached = prompt_tokens - cached_tokens
    return (uncached * input_price + cached_tokens * cached_price
            + output_tokens * output_price) / PER_MILLION


def cache_saving_fraction(prompt_tokens, cached_tokens, output_tokens,
                          input_price, cached_price, output_price):
    """Share of the no-cache bill that the cache removed."""
    base = request_cost(prompt_tokens, 0, output_tokens,
                        input_price, cached_price, output_price)
    real = request_cost(prompt_tokens, cached_tokens, output_tokens,
                        input_price, cached_price, output_price)
    return 0.0 if base == 0 else (base - real) / base


def dedicated_cost(gpu_hour_price, gpu_count, billed_minutes, replicas=1):
    """GPU-time cost. The docs say per-minute granularity, so minutes are the unit."""
    return gpu_hour_price * gpu_count * replicas * billed_minutes / 60.0


def breakeven_tokens_per_month(dedicated_monthly, blended_price_per_million):
    """Tokens per month at which Serverless would cost as much as the dedicated floor."""
    return dedicated_monthly / blended_price_per_million * PER_MILLION


@dataclass
class Segment:
    minutes: float
    readiness: str        # "ready", "partially_ready", "not_ready"
    running_replicas: int


def billed_minutes(segments, policy):
    """policy 'table': bill only ready capacity. policy 'prose': bill while any replica runs."""
    if policy not in ("table", "prose"):
        raise ValueError("policy must be 'table' or 'prose'")
    total = 0.0
    for s in segments:
        if policy == "table" and s.readiness == "ready":
            total += s.minutes
        elif policy == "prose" and s.running_replicas >= 1:
            total += s.minutes
    return total


def next_scale(scale, usage_fraction):
    """One 15-minute window of the dynamic rate limit."""
    if usage_fraction >= UP_THRESHOLD:
        scale *= UP_FACTOR
    elif usage_fraction <= DOWN_THRESHOLD:
        scale /= DOWN_DIVISOR
    return min(max(scale, 1.0), CEILING_MULTIPLE)


def ramp(windows, usage_fraction=1.0, start=1.0):
    """Scale factor after each window of constant usage. Index 0 is the baseline."""
    out = [start]
    for _ in range(windows):
        out.append(next_scale(out[-1], usage_fraction))
    return out


def windows_to_reach(multiple):
    """Windows of sustained 80 percent usage needed to reach a multiple of the base limit."""
    if multiple <= 1:
        return 0
    return math.ceil(math.log(multiple) / math.log(UP_FACTOR))


if __name__ == "__main__":
    prices = (1.00, 0.10, 3.00)   # placeholders per million tokens, not Nebius prices
    print("cost with cache   :", request_cost(3108, 3072, 62, *prices))
    print("cost without cache:", request_cost(3108, 0, 62, *prices))
    print("saving            :", round(cache_saving_fraction(3108, 3072, 62, *prices), 3))
    print("ramp 0,1,2,4,8    :", [round(ramp(8)[i], 2) for i in (0, 1, 2, 4, 8)])
    print("windows to 20x    :", windows_to_reach(20), "=", windows_to_reach(20) * 15, "minutes")
