"""M6: group log lines by template (digit runs replaced by <N>)."""
import re
from collections import Counter

_DIGITS = re.compile(r"\d+")


def log_templates(lines):
    """Return [(template, count)] sorted by count desc, then template. O(total chars)."""
    counts = Counter(_DIGITS.sub("<N>", line) for line in lines)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
