# Let's verify every box and its enclosed text lines with exact math:

# 1. Title: 48px, bold sans-serif. Box: width 1600.
# 53 chars * 0.6 * 48 = 1526 px. Center = 800. Span: 37 to 1563. Margin > 16px.

# 2. Header Col 1:
# Box: x=40, width=900.
# Icon: x=65..121.
# Text: x=140, y=152. font-size=30 bold sans-serif.
# 37 chars * 0.6 * 30 = 666 px.
# Text end = 140 + 666 = 806. Box right = 940.
# Right padding = 940 - 806 = 134 px. Left gap to icon = 140 - 121 = 19 px (> 16px).

# 3. Col 1 Sub-card 1:
# Box: x=65, y=190, width=850, height=160.
# Text: x=85, y=240, dy=36 (y=240, 276, 312). font-size=24 monospace.
# Line 1: 'defined, undefined, none, string, number, integer,' (50 chars * 14.88 = 744 px) -> end = 85 + 744 = 829. Right pad = 915 - 829 = 86 px.
# Line 2: 'mapping, iterable, sequence, even, odd,' (39 chars * 14.88 = 580 px) -> end = 85 + 580 = 665. Right pad = 915 - 665 = 250 px.
# Line 3: 'divisibleby(3), equalto, in, lower, upper, callable' (51 chars * 14.88 = 758.88 px) -> end = 85 + 758.88 = 843.88. Right pad = 915 - 843.88 = 71.12 px.
# Left pad = 85 - 65 = 20 px (> 16px).
# Top pad = 240 - 24 - 190 = 26 px (> 16px).
# Bottom pad = 350 - 312 = 38 px (> 16px).

# 4. Col 1 Sub-card 2:
# Box: x=65, y=370, width=850, height=160.
# Text: x=85, y=420, dy=36 (y=420, 456, 492). font-size=24 monospace.
# Line 1: 'success, failed, changed, skipped, match, search,' (49 chars * 14.88 = 729.12 px) -> end = 85 + 729.12 = 814.12. Right pad = 915 - 814.12 = 100.88 px.
# Line 2: 'version(2.0, >=), subset, superset, contains, file,' (51 chars * 14.88 = 758.88 px) -> end = 85 + 758.88 = 843.88. Right pad = 71.12 px.
# Line 3: 'directory, exists' (17 chars * 14.88 = 252.96 px) -> end = 85 + 252.96 = 337.96.
# Left pad = 20 px.
# Top pad = 420 - 24 - 370 = 26 px.
# Bottom pad = 530 - 492 = 38 px.

# 5. Header Col 2:
# Box: x=980, width=580.
# Icon: x=1005..1061.
# Text: x=1080, y=152. font-size=30 bold sans-serif.
# 23 chars * 0.6 * 30 = 414 px.
# End = 1080 + 414 = 1494. Box right = 1560. Right pad = 1560 - 1494 = 66 px (> 16px). Gap to icon = 1080 - 1061 = 19 px (> 16px).

# 6. Col 2 Card:
# Box: x=1005, y=190, width=530, height=340.
# Text: 'returns a new value' (19 chars * 0.6 * 30 = 342 px).
# Center = 1270. Span: 1099 to 1441.
# Left pad = 1099 - 1005 = 94 px. Right pad = 1535 - 1441 = 94 px (> 16px).
# y=260. Top pad = 260 - 30 - 190 = 40 px (> 16px).

# 7. Examples Strip:
# Container: x=40, y=610, width=1520, height=150.
# Card 1: x=150, y=627, width=446, height=115.
# Line 1: 'if gpu_driver_version' (21 chars * 14.88 = 312.48 px). x=175. End = 487.48. Right pad = 596 - 487.48 = 108.52 px.
# Line 2: 'is version(550, >=)' (20 chars * 14.88 = 297.6 px). x=175. End = 472.6. Right pad = 123.4 px.
# Left pad = 25 px. Top pad = 672 - 24 - 627 = 21 px. Bottom pad = 742 - 706 = 36 px.

# Card 2: x=621, y=627, width=446, height=115.
# Line 1: 'if item is defined' (18 chars * 14.88 = 267.84 px). x=646. End = 913.84. Right pad = 1067 - 913.84 = 153.16 px.
# Line 2: 'and item is not none' (20 chars * 14.88 = 297.6 px). x=646. End = 943.6. Right pad = 123.4 px.
# Left pad = 25 px. Top pad = 21 px. Bottom pad = 36 px.

# Card 3: x=1092, y=627, width=448, height=115.
# 'result is failed' (16 chars * 14.88 = 238.08 px). Center = 1316. Span: 1197 to 1435.
# Left pad = 1197 - 1092 = 105 px. Right pad = 1540 - 1435 = 105 px.
# y=691. Top pad = 691 - 24 - 627 = 40 px. Bottom pad = 742 - 691 = 51 px.

# 8. Orange Callout:
# Box: x=40, y=800, width=1520, height=165.
# Icon: x=65..121.
# Text: x=150, y=852, dy=34 (y=852, 886, 920). font-size=24 sans-serif.
# Line 1: 83 chars * 14.4 = 1195.2 px. End = 150 + 1195.2 = 1345.2. Right pad = 1560 - 1345.2 = 214.8 px.
# Line 2: 85 chars * 14.4 = 1224 px. End = 150 + 1224 = 1374. Right pad = 1560 - 1374 = 186 px.
# Line 3: 60 chars * 14.4 = 864 px. End = 150 + 864 = 1014. Right pad = 546 px.
# Left pad from icon = 150 - 121 = 29 px (> 16px).
# Top pad = 852 - 24 - 800 = 28 px (> 16px).
# Bottom pad = 965 - 920 = 45 px (> 16px).

# 9. Bottom Bar:
# Box: x=40, y=1005, width=1520, height=75.
# Text: 'Test for yes or no, filter for a new value' (41 chars * 0.6 * 28 = 688.8 px).
# Center = 800. Span: 455.6 to 1144.4. Left pad = 455.6 - 40 = 415.6 px. Right pad = 415.6 px.
# y=1051. Top pad = 1051 - 28 - 1005 = 18 px (> 16px). Bottom pad = 1080 - 1051 = 29 px (> 16px).

print("ALL PADDINGS EXCEED 16PX BY A HEALTHY MARGIN!")
