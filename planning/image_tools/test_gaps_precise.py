from test_all_paddings_precise import boxes_data

# Check margin to canvas edges (1600 x 1200)
for name, bx, by, bw, bh, lines, tx, ty, lh, icon, anchor in boxes_data:
    assert bx >= 40, f"{name}: bx {bx} < 40"
    assert bx + bw <= 1560, f"{name}: bx+bw {bx+bw} > 1560"
    assert by >= 40, f"{name}: by {by} < 40"
    assert by + bh <= 1160, f"{name}: by+bh {by+bh} > 1160"

print("Canvas margin check (>=40px): ALL PASSED!")

# Check gap between any two boxes:
overlap_errs = []
for i in range(len(boxes_data)):
    for j in range(i+1, len(boxes_data)):
        n1, x1, y1, w1, h1 = boxes_data[i][:5]
        n2, x2, y2, w2, h2 = boxes_data[j][:5]
        dx = max(0, max(x1 - (x2 + w2), x2 - (x1 + w1)))
        dy = max(0, max(y1 - (y2 + h2), y2 - (y1 + h1)))
        if dx == 0 and dy == 0:
            overlap_errs.append(f"OVERLAP {n1} and {n2}")
        elif dx < 40 and dy < 40:
            overlap_errs.append(f"GAP < 40 between {n1} and {n2}: dx={dx}, dy={dy}")

if overlap_errs:
    print("Gap errors:")
    for e in overlap_errs:
        print("  ", e)
else:
    print("ALL GAPS >= 40px PASSED PERFECTLY!")
