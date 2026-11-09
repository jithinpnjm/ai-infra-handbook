"""String compression and parsing: run-length encoding and a quote-aware tokeniser."""
import re


def rle_encode(s):
    out, i = [], 0
    while i < len(s):
        j = i
        while j < len(s) and s[j] == s[i]:
            j += 1
        out.append(f"{j - i}{s[i]}")
        i = j
    return "".join(out)


def rle_decode(s):
    """Decode '3a2b' style text. The input must not contain digits as data characters."""
    out, num = [], ""
    for ch in s:
        if ch.isdigit():
            num += ch
        else:
            if not num:
                raise ValueError("missing count before %r" % ch)
            out.append(ch * int(num))
            num = ""
    if num:
        raise ValueError("trailing count")
    return "".join(out)


def tokenize(line):
    """Parse logfmt text (key=value pairs, values may be quoted with backslash escapes) into a dict."""
    out, i, n = {}, 0, len(line)
    while i < n:
        while i < n and line[i] == " ":
            i += 1
        if i >= n:
            break
        j = i
        while j < n and line[j] not in "= ":
            j += 1
        key = line[i:j]
        if j >= n or line[j] == " ":
            out[key] = ""
            i = j
            continue
        j += 1  # skip '='
        if j < n and line[j] == '"':
            j += 1
            buf = []
            while j < n and line[j] != '"':
                if line[j] == "\\" and j + 1 < n:
                    j += 1
                buf.append(line[j])
                j += 1
            if j >= n:
                raise ValueError("unterminated quote")
            out[key] = "".join(buf)
            i = j + 1
        else:
            k = j
            while k < n and line[k] != " ":
                k += 1
            out[key] = line[j:k]
            i = k
    return out


def collapse_ids(path):
    """Normalise URL paths for metrics labels: /users/123/jobs/9f2c... -> /users/:n/jobs/:hex"""
    path = re.sub(r"/\d+(?=/|$)", "/:n", path)
    return re.sub(r"/[0-9a-f]{8,}(?=/|$)", "/:hex", path)
