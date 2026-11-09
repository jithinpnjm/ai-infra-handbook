"""M15: expand '3[a2[c]]' style repeat notation."""


def decode_string(s):
    """Valid input only: lowercase letters, digits as counts, '[' follows each count.

    Stack of (text so far, repeat count). O(output length).
    """
    stack = []
    cur = []
    num = 0
    for ch in s:
        if ch.isdigit():
            num = num * 10 + int(ch)
        elif ch == "[":
            stack.append(("".join(cur), num))
            cur, num = [], 0
        elif ch == "]":
            prev, n = stack.pop()
            cur = [prev + "".join(cur) * n]
        else:
            cur.append(ch)
    return "".join(cur)
