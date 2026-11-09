"""E8: longest run of consecutive successful requests (status below 500)."""


def longest_ok_streak(statuses):
    best = cur = 0
    for s in statuses:
        cur = cur + 1 if s < 500 else 0
        best = max(best, cur)
    return best
