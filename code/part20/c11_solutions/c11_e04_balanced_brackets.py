"""E4: are the brackets in a config string balanced and properly nested?"""

PAIRS = {")": "(", "]": "[", "}": "{"}


def balanced(s):
    stack = []
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in PAIRS:
            if not stack or stack.pop() != PAIRS[ch]:
                return False
    return not stack
