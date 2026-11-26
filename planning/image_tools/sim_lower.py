l7 = "[y for x in data if (y := expensive(x)) is not None] calls expensive once per item"
l8 = "M = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]: column [row[1] for row in M] is [2, 5, 8]; diagonal [M[i][i] ...] is [1, 5, 9]; anti-diagonal is [3, 5, 7]; [col + 10 for row in M for col in row] is flat while [[col + 10 for col in row] for row in M] keeps rows"
l9 = "more than two for or if clauses, or side effects: use a loop; never [print(x) for x in xs]; you cannot catch exceptions inside a comprehension, wrap risky code in a function; use [[0]*c for _ in range(r)]; generator expressions for sum, any, all, max, sorted, join, set, tuple; comprehensions are usually 20 to 50% faster than the equivalent loops"

lines_l7 = [
    "[y for x in data if (y := expensive(x)) is ",
    "not None] calls expensive once per item"
]
assert "".join(lines_l7) == l7
print("L7 (Walrus use): 2 lines")

lines_l8 = [
    "M = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]: ",
    "column [row[1] for row in M] is [2, 5, 8]; ",
    "diagonal [M[i][i] ...] is [1, 5, 9]; ",
    "anti-diagonal is [3, 5, 7]; ",
    "[col + 10 for row in M for col in row] is flat ",
    "while [[col + 10 for col in row] for row in M] ",
    "keeps rows"
]
assert "".join(lines_l8) == l8
print("L8 (Matrix examples): 7 lines")

lines_l9 = [
    "more than two for or if clauses, or side ",
    "effects: use a loop; never [print(x) for x ",
    "in xs]; you cannot catch exceptions inside a ",
    "comprehension, wrap risky code in a function; ",
    "use [[0]*c for _ in range(r)]; generator ",
    "expressions for sum, any, all, max, sorted, ",
    "join, set, tuple; comprehensions are ",
    "usually 20 to 50% faster than the ",
    "equivalent loops"
]
assert "".join(lines_l9) == l9
print("L9 (Rules of thumb): 9 lines")

