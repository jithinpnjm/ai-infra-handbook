l8 = "M = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]: column [row[1] for row in M] is [2, 5, 8]; diagonal [M[i][i] ...] is [1, 5, 9]; anti-diagonal is [3, 5, 7]; [col + 10 for row in M for col in row] is flat while [[col + 10 for col in row] for row in M] keeps rows"

lines_l8 = [
    "M = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]: ",
    "column [row[1] for row in M] is ",
    "[2, 5, 8]; diagonal [M[i][i] ...] is ",
    "[1, 5, 9]; anti-diagonal is [3, 5, 7]; ",
    "[col + 10 for row in M for col in row] ",
    "is flat while [[col + 10 for col in row] ",
    "for row in M] keeps rows"
]

assert "".join(lines_l8) == l8
print("Exact match for L8!")
for l in lines_l8:
    w = len(l) * 24 * 0.62
    print(f"({len(l):2d} chars, w={w:.1f}px) {l}")
