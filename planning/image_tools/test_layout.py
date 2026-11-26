import xml.etree.ElementTree as ET

# Let's inspect the layout and verify every dimension
# Available width: 1600. Margins: left=40, right=1600-40=1560.
# Available height: 900 to 1200. Margins: top=40, bottom=H-40.

# Title:
# Line 1: "Cluster autoscaler: pending pods,"
# Line 2: "node groups and the settings that matter"
# If title y starts at 80:
# Line 1: y=80. Top of text ~ 80 - 36 = 44 (>= 40 margin!)
# Line 2: y=80 + 54 = 134. Bottom of text ~ 134 + 12 = 146.
# Gap between title bottom (146) and top of containers: 170 - 146 = 24px (or start containers at y=175, gap=29px).

# Left container: Flow of 5 boxes + Dashboard note.
# Right container: Settings table (3 cards) + Nebius node group notes (1 card).

print("Layout calculation...")
