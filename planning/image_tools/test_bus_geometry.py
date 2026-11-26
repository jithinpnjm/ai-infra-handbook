#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Let's explore how arrows can be structured:
# Source:
# C1 & C2 & C3 --> MDS
# C1 & C2 & C3 --> D1
# C1 & C2 & C3 --> D2
# C1 & C2 & C3 --> D3
# MDS --- D1

# If we have a bus/trunk from clients:
# Horizontal lines leave C1 (x=440, y=260), C2 (x=440, y=520), C3 (x=440, y=780).
# They join a vertical spine at x=540 (spanning y=260 to 780).
# From this spine:
# 4 arrows go to the right:
# Arrow 1: leaves spine at y=205, goes to MDS (x=980, y=205)
# Arrow 2: leaves spine at y=390, goes to D1 (x=980, y=390)
# Arrow 3: leaves spine at y=560, goes to D2 (x=980, y=560)
# Arrow 4: leaves spine at y=730, goes to D3 (x=980, y=730)
# And connection MDS --- D1:
# A line between MDS (x=1260, y=280) and D1 (x=1260, y=330) with NO arrowhead!

print("Testing bus arrow geometry...")
