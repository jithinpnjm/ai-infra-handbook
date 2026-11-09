"""E3: count HTTP status classes in access-log lines."""

KEYS = ("1xx", "2xx", "3xx", "4xx", "5xx", "other", "malformed")


def status_class_counts(lines):
    """Line shape: '<ts> <method> <path> <status> <ms>ms'. O(n) time, O(1) space."""
    counts = dict.fromkeys(KEYS, 0)
    for line in lines:
        parts = line.split()
        if len(parts) != 5 or not parts[3].isdigit() or len(parts[3]) != 3:
            counts["malformed"] += 1
            continue
        key = parts[3][0] + "xx"
        counts[key if key in counts else "other"] += 1
    return counts
