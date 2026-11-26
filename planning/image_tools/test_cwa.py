cwa_text = "cut -d space -f1 access.log | uniq -c | sort -rn | head -3 skips the first sort, so uniq counted only neighbouring lines and printed 3 203.0.113.77 twice"

# Available width inside panel: 1520 - 64 = 1456 px.
# At font-size 24:
# If monospace / code portion:
# Let's wrap into 2 lines:
# Line 1: code + explanation start
# Line 2: remainder
line1 = "cut -d space -f1 access.log | uniq -c | sort -rn | head -3 skips the first sort,"
line2 = "so uniq counted only neighbouring lines and printed 3 203.0.113.77 twice"

print("Line 1 len:", len(line1), "width:", len(line1) * 0.6 * 24)
print("Line 2 len:", len(line2), "width:", len(line2) * 0.6 * 24)
print("Combined:", line1 + " " + line2 == cwa_text)
