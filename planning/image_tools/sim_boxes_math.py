widths = [160, 196, 110, 232, 196, 160, 210]
n = len(widths)
total_w = sum(widths)
print("Total width of boxes:", total_w)
avail = 1600 - 80 # 40px margin on each side
gaps_total = avail - total_w
gap = gaps_total / (n - 1)
print(f"Total available for 6 gaps: {gaps_total} px")
print(f"Each gap: {gap:.2f} px")

# Compute positions
margin_left = 40
x = margin_left
boxes = []
for i, w in enumerate(widths):
    boxes.append({
        "i": i,
        "x": x,
        "w": w,
        "cx": x + w / 2,
        "right": x + w
    })
    x += w + gap

print("\nBoxes:")
for b in boxes:
    print(f"Box {b['i']}: x={b['x']:.1f}, w={b['w']:.1f}, right={b['right']:.1f}, cx={b['cx']:.1f}")

for i in range(len(boxes) - 1):
    g = boxes[i+1]['x'] - boxes[i]['right']
    print(f"Gap {i}-{i+1}: {g:.2f} px")

right_margin = 1600 - boxes[-1]['right']
print(f"Right margin: {right_margin:.2f} px")
