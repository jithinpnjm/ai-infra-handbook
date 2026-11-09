"""M10: slowest worker rate that still finishes the jobs in time."""


def min_rate(job_sizes, hours):
    """Smallest integer rate r so that sum(ceil(size / r)) <= hours.

    One worker handles one job at a time, one job per hour slot minimum.
    Binary search on the answer: O(n log max). Impossible if hours < number of jobs.
    """
    if not job_sizes:
        return 1
    if hours < len(job_sizes):
        raise ValueError("not enough hours for one slot per job")

    def hours_needed(r):
        return sum(-(-s // r) for s in job_sizes)

    lo, hi = 1, max(job_sizes)
    while lo < hi:
        mid = (lo + hi) // 2
        if hours_needed(mid) <= hours:
            hi = mid
        else:
            lo = mid + 1
    return lo
