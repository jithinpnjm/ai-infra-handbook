text = "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns"

# Monospace 24px: max width for box (w=936, left_pad>=16, right_pad>=16 -> max text width = 904)
# char width = 24 * 0.62 = 14.88 px
# max chars = 904 / 14.88 = 60.75 chars

words = text.split(" ")
lines = []
curr = []
for w in words:
    cand = " ".join(curr + [w]) if curr else w
    if len(cand) <= 56:
        curr.append(w)
    else:
        lines.append(" ".join(curr))
        curr = [w]
if curr:
    lines.append(" ".join(curr))

for i, l in enumerate(lines):
    w_px = len(l) * 14.88
    print(f"Line {i+1} ({len(l)} chars, {w_px:.1f} px): '{l}'")

print(f"Total lines: {len(lines)}")
