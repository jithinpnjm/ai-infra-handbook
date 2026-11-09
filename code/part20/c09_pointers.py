"""Two pointers on sorted data."""


def two_sum_sorted(a, target):
    """Indexes (i, j), i < j, with a[i] + a[j] == target in sorted a, else None."""
    i, j = 0, len(a) - 1
    while i < j:
        s = a[i] + a[j]
        if s == target:
            return i, j
        if s < target:
            i += 1
        else:
            j -= 1
    return None


def merge_sorted(a, b):
    """Merge two sorted lists, stable: on ties the element from a goes first."""
    out, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i]); i += 1
        else:
            out.append(b[j]); j += 1
    out.extend(a[i:])
    out.extend(b[j:])
    return out


def dedupe_in_place(a):
    """Remove duplicates from sorted list a in place. Return the new length."""
    if not a:
        return 0
    write = 1
    for read in range(1, len(a)):
        if a[read] != a[write - 1]:
            a[write] = a[read]
            write += 1
    del a[write:]
    return write


def common_sorted(a, b):
    """Sorted list of values present in both sorted lists, each value once."""
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] < b[j]:
            i += 1
        elif a[i] > b[j]:
            j += 1
        else:
            if not out or out[-1] != a[i]:
                out.append(a[i])
            i += 1
            j += 1
    return out
