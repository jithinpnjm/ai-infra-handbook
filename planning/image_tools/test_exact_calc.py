#!/usr/bin/env python3
# Check the geometry with updated coordinates:
# Customer box: x=70, y=210, w=380, h=90 -> x=[70, 450]
# US panel: x=1120, y=205, w=420, h=430 -> x=[1120, 1540]
# Red arrow: (450, 255) to (1102, 255)
# Red cross: cx=1055, cy=255, r=26 -> x=[1029, 1081]
# Text center: x=742
# Line 1: x in [506, 978], y in [175, 199]
# Line 2: x in [631, 853], y in [207, 231]

print("Span between customer and red cross:", 1029 - 450)
print("Line 1 left clearance:", 506 - 450)
print("Line 1 right clearance:", 1029 - 978)
print("Line 1 top clearance:", 175 - 145)
print("Line 2 bottom clearance to arrow:", 255 - 231)
