"""E9: nearest-rank percentile."""
import math
from decimal import Decimal


def percentile(values, p):
    """Smallest value such that at least p percent of values are <= it.

    rank = ceil(p/100 * n), 1-based. Decimal avoids float surprises such as
    99.9 * 1000 / 100 not being exactly 999. O(n log n).
    """
    if not values:
        raise ValueError("empty input")
    if not 0 < p <= 100:
        raise ValueError("p must be in (0, 100]")
    rank = math.ceil(Decimal(str(p)) * len(values) / 100)
    return sorted(values)[rank - 1]
