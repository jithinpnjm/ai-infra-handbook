import xml.etree.ElementTree as ET

tree = ET.parse("candidate_lossless_v2.svg")
root = tree.getroot()

# Rects:
# 1. Checklist container: (40, 175, 980, 395)
#    Item 1 rect: (55, 190, 950, 66)
#      Text at x=115, y=217, dy=28 (245). Top = 217-24*0.85 = 196.6 (pad top: 196.6-190 = 6.6 -> wait, let's check!)
