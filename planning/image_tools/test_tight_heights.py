row_heights = [
    108, # Workloads (3L)
    56,  # Precision (1L)
    108, # Traffic (3L)
    82,  # Jobs (2L)
    82,  # Storage (2L)
    56,  # Packaging (1L)
    108, # Failure (3L)
    82,  # North star (2L)
    82   # Rack power (2L)
]
gap = 7

# Top layout:
# y=42: title (48px bold)
# y=60 to 110: Analogy banner (50px high, fs=24: baseline = 60 + 24 + 16 = 100, bottom_pad = 110 - 100 = 10 -> needs 56px: y=62 to 118, baseline = 102. top_pad = 102-24-62=16, bottom_pad = 118-102=16!)
# y=124 to 180: Column headers (56px high, fs=24 bold: baseline = 124 + 24 + 16 = 164, top_pad = 16, bottom_pad = 180 - 164 = 16!)
# Rows start at y = 186

cur_y = 186
for i, h in enumerate(row_heights):
    print(f"Row {i+1} y={cur_y}..{cur_y+h}")
    cur_y += h + gap

rows_end = cur_y - gap
print(f"Rows end at: {rows_end}px")

takeaway_y = rows_end + 8
takeaway_h = 82
takeaway_end = takeaway_y + takeaway_h
print(f"Takeaway ends at: {takeaway_end}px")
print(f"Remaining bottom margin in 1200: {1200 - takeaway_end}px")
assert takeaway_end <= 1200
print("SUCCESS! Fits inside 1200!")
