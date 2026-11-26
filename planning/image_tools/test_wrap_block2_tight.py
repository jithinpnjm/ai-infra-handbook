l4 = "S = 'hack'; [(temp := S[i]) + temp.upper() for i in range(len(S))] gives ['hH', 'aA', 'cC', 'kK']; temp is 'k' in the enclosing scope, i raises NameError: name i is not defined"

lines_l4 = [
    "S = 'hack'; ",
    "[(temp := S[i]) + temp.upper() ",
    "for i in range(len(S))] gives ",
    "['hH', 'aA', 'cC', 'kK']; temp is 'k' ",
    "in the enclosing scope, i raises ",
    "NameError: name i is not defined"
]

reconstructed = "".join(lines_l4)
assert reconstructed == l4, f"Mismatch:\n'{reconstructed}'\nvs\n'{l4}'"
print("Exact match for L4 (6 lines)!")
for l in lines_l4:
    w = len(l) * 24 * 0.62
    print(f"({len(l):2d} chars, w={w:.1f}px) {l}")
