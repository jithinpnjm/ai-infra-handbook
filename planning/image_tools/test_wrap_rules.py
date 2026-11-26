l9 = "more than two for or if clauses, or side effects: use a loop; never [print(x) for x in xs]; you cannot catch exceptions inside a comprehension, wrap risky code in a function; use [[0]*c for _ in range(r)]; generator expressions for sum, any, all, max, sorted, join, set, tuple; comprehensions are usually 20 to 50% faster than the equivalent loops"

lines_l9 = [
    "more than two for or if clauses, or side ",
    "effects: use a loop; never [print(x) for x ",
    "in xs]; you cannot catch exceptions inside a ",
    "comprehension, wrap risky code in a function; ",
    "use [[0]*c for _ in range(r)]; generator ",
    "expressions for sum, any, all, max, sorted, ",
    "join, set, tuple; comprehensions are usually ",
    "20 to 50% faster than the equivalent loops"
]

reconstructed = "".join(lines_l9)
assert reconstructed == l9, f"Mismatch:\n'{reconstructed}'\nvs\n'{l9}'"
print("Exact match for L9 (8 lines)!")
for l in lines_l9:
    w_mono = len(l) * 24 * 0.62
    w_sans = len(l) * 24 * 0.6
    print(f"({len(l):2d} chars, w_sans={w_sans:.1f}px) {l}")
