"""E2: run-length compress a lowercase string, only if that is shorter."""


def compress(s):
    """'aaabcc' -> 'a3bc2'. A run of 1 keeps no digit. Return s if not shorter.

    Input is lowercase letters only, so a digit always means a count.
    """
    if not s:
        return s
    out = []
    run_char, run_len = s[0], 1
    for ch in s[1:]:
        if ch == run_char:
            run_len += 1
        else:
            out.append(run_char + (str(run_len) if run_len > 1 else ""))
            run_char, run_len = ch, 1
    out.append(run_char + (str(run_len) if run_len > 1 else ""))
    packed = "".join(out)
    return packed if len(packed) < len(s) else s


def decompress(packed):
    """Inverse of compress for letters-only input."""
    out = []
    i = 0
    while i < len(packed):
        ch = packed[i]
        i += 1
        j = i
        while j < len(packed) and packed[j].isdigit():
            j += 1
        out.append(ch * (int(packed[i:j]) if j > i else 1))
        i = j
    return "".join(out)
