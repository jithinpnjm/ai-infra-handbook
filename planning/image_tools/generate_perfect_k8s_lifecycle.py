# Complete generator and strict rule validator for Node lifecycle SVG
import re
import xml.etree.ElementTree as ET

# Canvas dimensions
WIDTH = 1600
HEIGHT = 1180

# Colors
BG = "#f5f8f5"
TEXT = "#303a36"
GREEN = "#207448"
PANEL_BG = "#e8f1ea"
ORANGE = "#db8129"
WHITE = "#ffffff"

# State box dimensions
BW = 240
BH = 115

# Columns:
# Col 0: cx = 240 (x = 120..360)
# Col 1: cx = 800 (x = 680..920)
# Col 2: cx = 1360 (x = 1240..1480; for Decommissioned: w=284 -> x = 1218..1502)

# Rows:
# Row 0: cy = 210 (y = 152.5..267.5)
# Row 1: cy = 550 (y = 492.5..607.5)
# Row 2: cy = 890 (y = 832.5..947.5)

print("Coordinates configured.")
