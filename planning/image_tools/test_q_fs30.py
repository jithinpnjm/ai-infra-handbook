fs = 30
factor = 0.60
# Col 1 width = 600, x = 40, w = 600.
# Icon: x=58, y=..., w=48, h=48.
# Text starts at x = 126.
# Right edge = 640. Right padding = 16 -> max text x = 624.
# Usable text width = 624 - 126 = 498 px.
# Max chars at fs=30: 498 / (30 * 0.6) = 27.6 -> 27 chars!

print("Testing with fs=30 (max 27 chars):")
lines_q1 = ["Where is every thread", "stuck right now?"]
for l in lines_q1:
    print(f"'{l}': len={len(l)}, w={len(l)*30*0.6:.1f} <= 498")

lines_q2 = ["Look at a running process", "without changing its code"]
for l in lines_q2:
    print(f"'{l}': len={len(l)}, w={len(l)*30*0.6:.1f} <= 498")
