"""E7: two latencies that add up to a budget."""


def pair_sum(latencies, budget):
    """Return (i, j), i < j, with the smallest j then the smallest i, or None."""
    first_seen = {}
    for j, x in enumerate(latencies):
        i = first_seen.get(budget - x)
        if i is not None:
            return (i, j)
        first_seen.setdefault(x, j)
    return None
