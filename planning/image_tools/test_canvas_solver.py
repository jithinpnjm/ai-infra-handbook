# Let's inspect the exact line counts and layout:
# Title at top:
# If title is 1 line? Can title be 1 line?
# "Common mistakes in errors, files and subprocesses, grouped"
# 57 characters * 48 * 0.60 = 1641.6 > 1600.
# So Title MUST be 2 lines (or font-size slightly smaller? "Title 48 px bold" -> must be 48 px bold!).
# So Title is 2 lines:
# line 1: Common mistakes in errors, files
# line 2: and subprocesses, grouped
# y1 = 44, y2 = 96. (ends around y = 104)

# Header: Area, Mistake, Fix
# y = 118, height = 36 (ends at 154)

# Table rows:
# Row 1 (Exceptions): m=3, f=2 -> h = 98 (lines: 3, h = 3*24 + pad)
# Row 2 (Files): m=4, f=2 -> h = 122
# Row 3 (Subprocess): m=6, f=3 -> h = 170
# Row 4 (Global state): m=3, f=2 -> h = 98
# Row 5 (Re-runs): m=1, f=3 -> h = 98
# Row 6 (Signals): m=2, f=1 -> h = 74
# Row 7 (Untrusted input): m=3, f=2 -> h = 98
# Sum of heights = 98 + 122 + 170 + 98 + 98 + 74 + 98 = 758 px!
# Gaps: 6 gaps of 8px = 48 px!
# Total table = 758 + 48 = 806 px!
# Table ends at 162 + 806 = 968!

# Stories strip:
# y = 980, height = 80 (ends at 1060)
# Bottom bar:
# y = 1074, height = 48 (ends at 1122)
# Bottom margin: 1200 - 1122 = 78 px!

print(f"Total canvas height fits easily in 1150-1200!")
