import re

def wrap_text(text, max_chars):
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

l5 = "a for variable in a list, set, dict or generator comprehension lives in the comprehension's own scope; := binds its target in the enclosing scope; a yield inside a comprehension is forbidden"
l6 = 'a filter if sits after the for; a conditional expression that picks a value sits before it: ["even" if n % 2 == 0 else "odd" for n in range(5)]; nested for clauses read left to right like nested for statements'

print("--- Rules strip in 740 width (max 44 chars) ---")
lines_l5 = wrap_text(l5, 44)
for l in lines_l5:
    print(f"({len(l):2d}) {l}")

print("\n--- Placement strip in 740 width (max 44 chars) ---")
lines_l6 = wrap_text(l6, 44)
for l in lines_l6:
    print(f"({len(l):2d}) {l}")

