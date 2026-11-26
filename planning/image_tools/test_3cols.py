l7 = "[y for x in data if (y := expensive(x)) is not None] calls expensive once per item"
l8 = "M = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]: column [row[1] for row in M] is [2, 5, 8]; diagonal [M[i][i] ...] is [1, 5, 9]; anti-diagonal is [3, 5, 7]; [col + 10 for row in M for col in row] is flat while [[col + 10 for col in row] for row in M] keeps rows"
l9 = "more than two for or if clauses, or side effects: use a loop; never [print(x) for x in xs]; you cannot catch exceptions inside a comprehension, wrap risky code in a function; use [[0]*c for _ in range(r)]; generator expressions for sum, any, all, max, sorted, join, set, tuple; comprehensions are usually 20 to 50% faster than the equivalent loops"

# Available width = 480.
# Left pad = 24, right pad = 24 -> usable width = 432 px.
# At 24px sans (0.6 * 24 = 14.4 px/char):
# max_chars = 432 / 14.4 = 30 chars!
# If mono (0.62 * 24 = 14.88 px/char): max_chars = 432 / 14.88 = 29 chars!

def wrap(text, max_chars):
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

lines_l7 = wrap(l7, 28)
lines_l8 = wrap(l8, 28)
lines_l9 = wrap(l9, 28)

print(f"L7 lines ({len(lines_l7)}):")
for l in lines_l7: print(f"  ({len(l):2d}) {l}")

print(f"\nL8 lines ({len(lines_l8)}):")
for l in lines_l8: print(f"  ({len(l):2d}) {l}")

print(f"\nL9 lines ({len(lines_l9)}):")
for l in lines_l9: print(f"  ({len(l):2d}) {l}")
