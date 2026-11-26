l4 = "S = 'hack'; [(temp := S[i]) + temp.upper() for i in range(len(S))] gives ['hH', 'aA', 'cC', 'kK']; temp is 'k' in the enclosing scope, i raises NameError: name i is not defined"

lines = [
    "S = 'hack'; [(temp := S[i]) + temp.upper() ",
    "for i in range(len(S))] gives ",
    "['hH', 'aA', 'cC', 'kK']; ",
    "temp is 'k' in the enclosing scope, ",
    "i raises NameError: name i is not defined"
]

reconstructed = "".join(lines)
assert reconstructed == l4, f"Mismatch:\n'{reconstructed}'\nvs\n'{l4}'"
print("Block 2 reconstruction: MATCHES PERFECTLY!")
for l in lines:
    w_mono = len(l) * 24 * 0.62
    w_sans = len(l) * 24 * 0.6
    print(f"({len(l):2d} chars) w_mono={w_mono:.1f}px, w_sans={w_sans:.1f}px | {l}")
