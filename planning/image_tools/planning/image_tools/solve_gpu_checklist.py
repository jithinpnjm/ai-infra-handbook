#!/usr/bin/env python3

# Vertical budget solver for H=1200

# Top elements:
# Title at 48px:
# If title is on 1 line:
# Title has 65 chars. Sans at 48px is 0.6 * 48 = 28.8px/char => 1872px (exceeds 1600).
# So title must be 2 lines:
# Line 1: 'The 60-second checklist for a GPU node: '
# Line 2: 'eight read-only additions'
# Let's check vertical footprint of title:
# y1 = 44, y2 = 92
# Title spans from y = 44 - 36 = 8 to y = 92 + 12 = 104.
# Table header: y = 118, h = 44 (y = 118..162)
# Footnote / Footer:
# 'All of them are read-only; option names vary by driver and DCGM version, so check the flags on your own system' (110 chars)
# At 24px sans (14.4px/char): 110 * 14.4 = 1584px.
# If 2 lines: line 1 (72 chars = 1036px), line 2 (38 chars = 547px).
# Footer box: y_footer..y_footer + h_footer.
# Bottom bar:
# 'Add these to the host checklist when you are on a GPU node' (58 chars * 14.4 = 835px)
# 1 line, h_bar = 46.
# Margin to bottom: 40px (ends at 1160).

# Let's compute available height for 8 rows:
# Bottom bar: 1114..1160 (h=46)
# Footer: 1046..1098 (h=52, 2 lines with dy=26, asc=18, desc=6 => text span = 50px, inside h=52? wait, 16px pad needs 16+50+16 = 82px!)
# Wait! Let's check footer padding rule:
# Does footer need to be inside a rect box, or can it be text or inside a panel?
# If footer is inside a panel rect, padding must be >= 16px!
