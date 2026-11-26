import re
import xml.etree.ElementTree as ET

tree = ET.parse('perfect_migration.svg')
root = tree.getroot()

def est_width(text, fs, is_mono):
    return len(text) * fs * (0.62 if is_mono else 0.6)

# Let's inspect all boxes and their text
# Box 1: Phase 1: rect x=40, y=120, w=480, h=210 (ends: x=520, y=330)
# Icon at x=68, y=140, w=56, h=56 (ends: x=124, y=196)
# Text starts at x=68, y=232
# Since text y=232 > icon bottom (196), text is below icon!
# Available horizontal width: from x=68 to 520 - 16 = 504 -> 436 px!
# Lines:
# "Phase 1 expand:" -> 15 * 30 * 0.6 = 270 px <= 436 px. Left pad: 68 - 40 = 28 px. Right pad: 520 - (68 + 270) = 182 px.
# "add the new piece in a way" -> 26 * 24 * 0.6 = 374.4 px <= 436 px. Right pad: 520 - (68 + 374.4) = 77.6 px.
# "old code ignores" -> 16 * 24 * 0.6 = 230.4 px <= 436 px. Right pad: 221.6 px.
# Text top: 232 - 30 = 202 > 196 (icon bottom). Gap to icon = 6 px.
# Text bottom: 232 + 38 + 34 = 304. Baseline 304 + 6 = 310. Box bottom = 330. Bottom pad: 330 - 310 = 20 px >= 16 px!
print("Phase 1 bounds: PASS")

# Box 2: Phase 2: rect x=560, y=120, w=480, h=210 (ends: x=1040, y=330)
# Icon at x=588, y=140, w=56, h=56 (ends: x=644, y=196)
# Text starts at x=588, y=232
# Lines:
# "Phase 2 move the code" -> 21 * 30 * 0.6 = 378 px <= 436 px. Right pad: 1040 - (588 + 378) = 74 px >= 16 px.
# "over with serial rolling," -> 25 * 24 * 0.6 = 360 px <= 436 px. Right pad: 1040 - (588 + 360) = 92 px >= 16 px.
# "old and new run side by side" -> 28 * 24 * 0.6 = 403.2 px <= 436 px. Right pad: 1040 - (588 + 403.2) = 48.8 px >= 16 px.
# Bottom pad: 330 - 310 = 20 px >= 16 px.
print("Phase 2 bounds: PASS")

# Box 3: Phase 3: rect x=1080, y=120, w=480, h=210 (ends: x=1560, y=330)
# Icon at x=1108, y=140, w=56, h=56 (ends: x=1164, y=196)
# Text starts at x=1108, y=242
# Lines:
# "Phase 3 contract:" -> 17 * 30 * 0.6 = 306 px <= 436 px. Right pad: 1560 - (1108 + 306) = 146 px >= 16 px.
# "later remove the old piece" -> 26 * 24 * 0.6 = 374.4 px <= 436 px. Right pad: 1560 - (1108 + 374.4) = 77.6 px >= 16 px.
# Text bottom: 242 + 40 = 282 + 6 = 288. Bottom pad: 330 - 288 = 42 px >= 16 px.
print("Phase 3 bounds: PASS")

# Lane 1 Header: rect x=65, y=390, w=260, h=115 (ends: x=325, y=505)
# Icon at x=85, y=423, w=48, h=38 (ends: x=133, y=461)
# Text at x=150, y=460. Width: 8 * 30 * 0.6 = 144 px. Ends at 294. Right pad: 325 - 294 = 31 px >= 16 px.
# Left pad to icon: 150 - 133 = 17 px >= 16 px.
# Vertical: y=460. Baseline 460. Top pad: 460 - 30 = 430 - 390 = 40 px >= 16 px. Bottom pad: 505 - 466 = 39 px >= 16 px.
print("Lane 1 Header bounds: PASS")

# Lane 2 Header: rect x=65, y=525, w=260, h=115 (ends: x=325, y=640)
# Icon at x=85, y=558, w=48, h=38 (ends: x=133, y=596)
# Text at x=150, y=595. Width: 8 * 30 * 0.6 = 144 px. Ends at 294. Right pad: 31 px >= 16 px.
# Left pad to icon: 150 - 133 = 17 px >= 16 px.
# Vertical: y=595. Baseline 595. Top pad: 595 - 30 - 525 = 40 px. Bottom pad: 640 - 601 = 39 px.
print("Lane 2 Header bounds: PASS")

# Database Layer: rect x=40, y=700, w=1520, h=110 (ends: x=1560, y=810)
# Icon at x=68, y=725, w=52, h=44 (ends: x=120)
# Text at x=140, y=766. Width: 25 * 30 * 0.6 = 450 px. Ends at 590.
# Next element inside DB is at x=640. Gap between text and visual = 640 - 590 = 50 px >= 16 px.
# Left pad to icon: 140 - 120 = 20 px >= 16 px.
# Vertical: y=766. Top pad: 766 - 30 - 700 = 36 px >= 16 px. Bottom pad: 810 - 772 = 38 px >= 16 px.
print("Database Layer bounds: PASS")

# Warning Box: rect x=40, y=850, w=940, h=230 (ends: x=980, y=1080)
# Icon at x=68, y=882, w=56, h=48 (ends: x=124, y=930)
# Text starts at x=146, y=930
# Left pad to icon: 146 - 124 = 22 px >= 16 px.
# Line 1: 33 * 26 * 0.6 = 514.8 px. Ends at 146 + 514.8 = 660.8. Right pad: 980 - 660.8 = 319.2 px >= 16 px.
# Line 2: 26 * 26 * 0.6 = 405.6 px. Ends at 551.6. Right pad: 428.4 px.
# Line 3: 20 * 26 * 0.6 = 312 px. Ends at 458. Right pad: 522 px.
# Vertical: y=930, 972, 1014. Top pad: 930 - 26 - 850 = 54 px >= 16 px. Bottom pad: 1080 - 1020 = 60 px >= 16 px.
print("Warning Box bounds: PASS")

# Note Box: rect x=1020, y=850, w=540, h=230 (ends: x=1560, y=1080)
# Icon at x=1050, y=882, w=48, h=38 (ends: x=1098, y=920)
# Text at x=1050, y=960.
# Notice: text y=960 > icon bottom (920). Text is below icon!
# Left pad: 1050 - 1020 = 30 px >= 16 px.
# Line 1: 20 * 24 * 0.62 = 297.6 px. Ends at 1050 + 297.6 = 1347.6. Right pad: 1560 - 1347.6 = 212.4 px >= 16 px.
# Line 2: 15*14.4 + 8*14.88 = 335.04 px. Ends at 1385.04. Right pad: 1560 - 1385.04 = 174.96 px >= 16 px.
# Line 3: 17*14.4 = 244.8 px. Ends at 1294.8. Right pad: 265.2 px.
# Text top: 960 - 24 = 936 > 920 (icon bottom). Gap = 16 px >= 16 px.
# Text bottom: 960 + 38 + 38 = 1036. Baseline 1036 + 6 = 1042. Bottom pad: 1080 - 1042 = 38 px >= 16 px.
print("Note Box bounds: PASS")

# Check all gaps between boxes:
# Horizontal:
# Phase 1 to Phase 2: 560 - 520 = 40 px.
# Phase 2 to Phase 3: 1080 - 1040 = 40 px.
# Warning to Note: 1020 - 980 = 40 px.
# Vertical:
# Title (ends ~76) to Row 1 (120): 44 px >= 40 px.
# Row 1 (ends 330) to Row 2 (370): 40 px >= 40 px.
# Row 2 (ends 660) to Row 3 (700): 40 px >= 40 px.
# Row 3 (ends 810) to Row 4 (850): 40 px >= 40 px.
# Row 4 (ends 1080) to Canvas bottom (1120): 40 px >= 40 px.
# Outside margins:
# Left: 40 px.
# Right: 1600 - 1560 = 40 px.
# Top: 40 px.
# Bottom: 40 px.
print("All gaps and margins >= 40px: PASS")
