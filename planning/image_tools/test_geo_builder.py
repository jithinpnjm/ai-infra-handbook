#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def sans_w(text, size=24):
    return len(text) * 0.60 * size

def mono_w(text, size=24):
    return len(text) * 0.62 * size

# Let's test all text wraps and ensure padding >= 20px for every line in its container.

boxes = {}

# 1. Title: x=800, y=56 (centered)
# Two lines:
# "Keeping the GPU, its NIC and its CPUs"
# "on one NUMA node"
# font-size: 48, bold

# 2. Left Comparison Area:
# Two Sockets / Columns:
# Socket 0 (NUMA node 0): x=40, y=140, w=440, h=770
# Interconnect Link: x=480 to x=560 (w=80)
# Socket 1 (NUMA node 1): x=560, y=140, w=440, h=770

# Inside Left Comparison Area:
# We have two row containers:
# Row 1: Panel 'Aligned' (y=210 to y=520, h=310)
# Row 2: Panel 'Misaligned' (y=550 to y=890, h=340)

# Socket 0 header:
# x=40, y=140, w=440, h=60
# Title: 'NUMA node 0' (font-size 30 bold)
# Icon beside it: chip icon (56px)

# Socket 1 header:
# x=560, y=140, w=440, h=60
# Title: 'NUMA node 1' (font-size 30 bold)
# Icon beside it: chip icon (56px)

# Interconnect link:
# Between x=480 and x=560, at y=170 and spanning down or at key transfer paths!

print("Testing geometry...")
