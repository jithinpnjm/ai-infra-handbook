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

l2 = "X = 99; [X for X in range(5)] gives [0, 1, 2, 3, 4]; outer X is still 99"
l3 = "for X in range(5): pass changes outer X to 4"
l4 = "S = 'hack'; [(temp := S[i]) + temp.upper() for i in range(len(S))] gives ['hH', 'aA', 'cC', 'kK']; temp is 'k' in the enclosing scope, i raises NameError: name i is not defined"
l5 = "a for variable in a list, set, dict or generator comprehension lives in the comprehension's own scope; := binds its target in the enclosing scope; a yield inside a comprehension is forbidden"
l6 = 'a filter if sits after the for; a conditional expression that picks a value sits before it: ["even" if n % 2 == 0 else "odd" for n in range(5)]; nested for clauses read left to right like nested for statements'
l7 = "[y for x in data if (y := expensive(x)) is not None] calls expensive once per item"
l8 = "M = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]: column [row[1] for row in M] is [2, 5, 8]; diagonal [M[i][i] ...] is [1, 5, 9]; anti-diagonal is [3, 5, 7]; [col + 10 for row in M for col in row] is flat while [[col + 10 for col in row] for row in M] keeps rows"
l9 = "more than two for or if clauses, or side effects: use a loop; never [print(x) for x in xs]; you cannot catch exceptions inside a comprehension, wrap risky code in a function; use [[0]*c for _ in range(r)]; generator expressions for sum, any, all, max, sorted, join, set, tuple; comprehensions are usually 20 to 50% faster than the equivalent loops"

print("--- L9 wrapped at 44 chars ---")
for line in wrap_text(l9, 44):
    print(f"({len(line):2d}) {line}")

print("\n--- L8 wrapped at 44 chars ---")
for line in wrap_text(l8, 44):
    print(f"({len(line):2d}) {line}")

print("\n--- L7 wrapped at 44 chars ---")
for line in wrap_text(l7, 44):
    print(f"({len(line):2d}) {line}")

print("\n--- L6 wrapped at 44 chars ---")
for line in wrap_text(l6, 44):
    print(f"({len(line):2d}) {line}")

print("\n--- L5 wrapped at 44 chars ---")
for line in wrap_text(l5, 44):
    print(f"({len(line):2d}) {line}")

print("\n--- L4 wrapped at 42 chars ---")
for line in wrap_text(l4, 42):
    print(f"({len(line):2d}) {line}")

print("\n--- L2 wrapped at 40 chars ---")
for line in wrap_text(l2, 40):
    print(f"({len(line):2d}) {line}")
