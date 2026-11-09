"""E5: merge two sorted timestamp lists."""


def merge_sorted(a, b):
    """Two pointers. Ties take from a first. O(n+m) time."""
    out = []
    i = j = 0
    while i < len(a) and j < len(b):
        if b[j] < a[i]:
            out.append(b[j])
            j += 1
        else:
            out.append(a[i])
            i += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out
