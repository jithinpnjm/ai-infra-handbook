import re
import xml.etree.ElementTree as ET

# Define coordinates for Assignment D
# Canvas: 1600 x 1080
# Margin: left/right = 80, width = 560
# Col 1: x = 80 to 640 (width 560)
# Gap: x = 640 to 960 (width 320)
# Col 2: x = 960 to 1520 (width 560)

# Top row: y = 140 to 360 (height 220)
# Middle gap: y = 360 to 700 (height 340)
# Bottom row: y = 700 to 960 (height 260)

print("Checking layout parameters...")
