# Check wrapping Node C
# Line 1: descriptor.__get__
# Line 2: (wins over instance dict)
sz1 = 28 # font size
mono1 = True # or false? descriptor.__get__ is a method, can be monospace or sans
char_w1 = 0.62 * sz1 if mono1 else 0.6 * sz1
w1 = len("descriptor.__get__") * char_w1

sz2 = 26 # secondary text >= 24 px
mono2 = False
char_w2 = 0.6 * sz2
w2 = len("(wins over instance dict)") * char_w2

print(f"Line 1 est width ({sz1}px): {w1:.1f}px")
print(f"Line 2 est width ({sz2}px): {w2:.1f}px")

# Available width in box:
# If box is x = 920 to 1540 (w = 620):
# icon x = 940, w = 56 -> right = 996
# text starts at tx = 1016
# available width = 1540 - 1016 - 16 = 508px!
print(f"Max text width: {max(w1, w2):.1f}px vs available 508px. Margin: {508 - max(w1, w2):.1f}px")
