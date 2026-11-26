# Let's test the "Top Entry" / "Side Entry" geometry and verify all coordinates!

import sys

# Canvas: 1600 x 1200
# Title at y = 50 (or y = 40..80)
# Root box: y = 90 .. 180 (height 90), width = 900 (x = 350 .. 1250)
# Inside root:
# Title: 'Run vmstat 2 and start at line 2' (30px bold)
# Note: 'Line 1 is the average since boot' (24px)
# Root icon: 56x56 px, green stroke 4.

# Let's check root text layout:
# Text x = 450, icon at (370, 107, 56, 56)
# Line 1 y = 132: 'Run vmstat 2 and start at line 2'
# Line 2 y = 164: 'Line 1 is the average since boot'
# Width of box = 900: from 350 to 1250.
# Left margin = 350, right margin = 350 (centered).
# Text width: 32 chars * 0.6 * 30 = 576 px. Fits in 900 px with plenty of padding!

print("Root box fits nicely.")

