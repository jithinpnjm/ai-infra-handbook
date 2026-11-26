#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Let's test the exact boxes and text placements
boxes = {
    "panel-1": (40, 145, 740, 380),
    "panel-2": (820, 145, 740, 380),
    "panel-3": (40, 565, 740, 380),
    "panel-4": (820, 565, 740, 380),
    "footer": (40, 985, 1520, 75),
    "bottom-bar": (40, 1100, 1520, 55)
}

print("Boxes configured successfully")
