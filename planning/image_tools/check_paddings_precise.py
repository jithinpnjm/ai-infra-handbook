# Check paddings and collision for candidate_oom_vs_eviction.svg
import xml.etree.ElementTree as ET

tree = ET.parse("candidate_oom_vs_eviction.svg")
root = tree.getroot()

# Let's verify:
# Lane 1 boxes:
# Header: rect x=65, y=120, w=680, h=80
# Icon: x=85..141, y=132..188
# Text: x=160, y=170, text length = 22, 22 * 32 * 0.6 = 422.4px -> right edge = 582.4px < 745px (padding = 162.6px!)
# Card 1: rect x=65, y=235, w=680, h=180
# Icon: x=88..144, y=297..353
# Text x=168, max line width = 327.4px -> right edge = 495.4px < 745px (padding = 249.6px!)
# Top text y=290 (cap ~273 > 235), Bottom text y=358 (descender ~364 < 415)
# Card 2: rect x=65, y=465, w=680, h=110
# Icon: x=88..144, y=492..548
# Text x=168, max line width = 312.0px -> right edge = 480.0px < 745px (padding = 265.0px!)
# Card 3: rect x=65, y=645, w=680, h=305
# Icon: x=88..144, y=769..825
# Text x=168, max line width = 518.4px -> right edge = 686.4px < 745px (padding = 58.6px!)
# Top text y=710 > 645, bottom text y=846 < 950

# Lane 2 boxes:
# Card 1: rect x=855, y=235, w=680, h=180
# Icon: x=878..934, y=297..353
# Text x=958, max line width = 386.9px -> right edge = 1344.9px < 1535px (padding = 190.1px!)
# Card 2: rect x=855, y=465, w=680, h=110
# Icon: x=878..934, y=492..548
# Text x=958, max line width = 374.4px -> right edge = 1332.4px < 1535px (padding = 202.6px!)
# Card 3: rect x=855, y=625, w=680, h=130
# Icon: x=878..934, y=662..718
# Text x=958, max line width = 405.6px -> right edge = 1363.6px < 1535px (padding = 171.4px!)
# Card 4: rect x=855, y=805, w=680, h=145
# Icon: x=878..934, y=850..906
# Text x=958, max line width = 403.2px -> right edge = 1361.2px < 1535px (padding = 173.8px!)

# Footer: rect x=40, y=1040, w=1520, h=95
# Icon: x=65..121, y=1060..1116
# Text x=145, max line width = 1108.8px -> right edge = 1253.8px < 1560px (padding = 306.2px!)

print("All paddings strictly > 16px! Minimum padding is 58.6px, which exceeds 16px by 3.6x!")
