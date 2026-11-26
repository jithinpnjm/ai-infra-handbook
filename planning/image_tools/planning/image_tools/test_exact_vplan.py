# Optimization script to fit everything comfortably within H=1200

# Let's inspect each element's minimal height that still gives:
# - font-size >= 24
# - left/right/top/bottom padding >= 16
# - icon gap >= 16
# - all box gaps >= 40 (or >= 16 for nested)

# Total canvas H = 1200
# Outside margins: Top = 40, Bottom = 40 -> Usable H = 1120

# 1. Title:
# y = 35 to 95 (ends at 95). Gap = 45 -> Row starts at y = 140.

# 2. cli.py:
# x = 40, y = 140, w = 1000, h = 76
# Text: 1 line at 28px bold:
# "cli.py: Click group, output formatting and exit codes"
# 53 chars * 0.6 * 28 = 890.4 px.
# In 1000 box: text at x = 128 -> ends at 128 + 890.4 = 1018.4 px.
# Right pad = 1040 - 1018.4 = 21.6 px >= 16 px!
# Icon: (56, 150, 56, 56) -> icon gap = 128 - 112 = 16 px!
# Text y = 186. Top pad = (186 - 22.4) - 140 = 23.6 px.
# Bot pad = 216 - (186 + 7) = 23 px.
# Height = 76 px! (Ends at 216).

# Gap: Arrow 1 from (540, 216) to (540, 256) (gap = 40 px).

# 3. collect.py:
# y = 256 to 352 (h = 96)
# Text: 2 lines at 24px bold (or 26px):
# Line 1: "collect.py: per-host executor over SSH, " (40 chars * 14.4 = 576 px)
# Line 2: "an agent or Redfish, with timeout and bounded concurrency" (57 chars * 14.4 = 820.8 px)
# Text starts at x = 128 -> ends at 128 + 820.8 = 948.8 px.
# Right pad = 1040 - 948.8 = 91.2 px >= 16 px!
# Text y1 = 292, y2 = 324.
# Top pad = (292 - 19.2) - 256 = 16.8 px.
# Bot pad = 352 - (324 + 6) = 22 px.
# Height = 96 px! (Ends at 352).

# Gap: Arrow 2 from (540, 352) to (540, 392) (gap = 40 px).

# 4. Pure Layers Container:
# y = 392 to 860 (h = 468 px).
# Inside:
# parsers.py card: y = 408 to 616 (h = 208 px).
#   parsers text (3 lines at 24px):
#     Line 1: "parsers.py: pure functions turning nvidia-smi CSV and " (54 chars * 14.4 = 777.6 px)
#     Line 2: "dcgmi output into frozen dataclasses (a pure function " (54 chars * 14.4 = 777.6 px)
#     Line 3: "answers from its inputs alone: no network, no clock, no randomness)" (67 chars * 14.4 = 964.8 px)
#     Wait! 964.8 px in 968 box (starts at 56, ends at 1024):
#     Text starts at 72 (or 68): 68 + 964.8 = 1032.8 > 1024!
#     So Line 3 needs to be wrapped or split!
#     What if 4 lines:
#     L1: "parsers.py: pure functions turning nvidia-smi CSV " (50 chars * 14.4 = 720 px)
#     L2: "and dcgmi output into frozen dataclasses " (41 chars * 14.4 = 590.4 px)
#     L3: "(a pure function answers from its inputs alone: " (48 chars * 14.4 = 691.2 px)
#     L4: "no network, no clock, no randomness)" (36 chars * 14.4 = 518.4 px)
#     4 lines take: y = 432, 458, 484, 510 (height ~100 px).
#   Parser detail panel:
#     y = 524 to 604 (h = 80 px).
#     Can Parser detail fit in 80 px?
#     3 lines of monospace:
#     L1: "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); " (82 chars * 14.88 = 1220 > 936).
#     So Parser detail needs 4 lines of 24px monospace!
#     If 4 lines of 24px monospace: panel height = 116 px (y = 524 to 640).
#     Then parsers card height = 248 px (y = 408 to 656).
# Gap: Arrow 3 from (540, 656) to (540, 696) (gap = 40 px).
# rules.py card:
#   y = 696 to 844 (h = 148 px).
#   rules.py text (1 line at 26px): y = 726.
#   Rules detail panel (2 lines at 24px): y = 744 to 832 (h = 88 px).
#   L1: "problems for: expected 8 GPUs but found a different count; " (59 chars * 14.4 = 849.6 px)
#   L2: "temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes" (73 chars * 14.4 = 1051.2 px > 936 px!)
#   So Rules detail needs 3 lines!
#   3 lines of 24px: panel height = 110 px (y = 744 to 854).
#   Then rules card ends at y = 870!
# Then Pure Layers container ends at y = 886!

# Gap: 40 px -> Test strip starts at y = 926!
# Test strip: y = 926 to 1046 (h = 120 px).
# Gap: 40 px -> Bottom bar starts at y = 1086!
# Bottom bar: y = 1086 to 1160 (h = 74 px).
# Bottom margin: 1200 - 1160 = 40 px!

print("IT FITS COMPLETELY WITHIN 1200 PX!")
print("Bottom margin is 40 px!")
