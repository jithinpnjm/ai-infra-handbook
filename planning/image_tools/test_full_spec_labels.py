#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Test all text elements against candidate audit rules

expected_labels = [
    "How the kernel walks /home/alice/train.py one name at a time",
    "Root directory /",
    "home -> inode A",
    "Directory /home (inode A)",
    "alice -> inode B",
    "Directory /home/alice (inode B)",
    "train.py -> inode C",
    "Inode C: type, permissions, owner, size, times, link count, pointers to data blocks",
    "Data blocks on the device",
    "look up home",
    "look up alice",
    "look up train.py",
    "read the inode and its data",
    "/home/alice/train.py",
    "The name lives in the directory; everything else lives in the inode",
    "rename = change one table row, so it is instant on one filesystem"
]

step_numbers = ["1", "2", "3", "4"]

print(f"Total expected labels: {len(expected_labels)}")
for i, el in enumerate(expected_labels):
    print(f"{i:2d}: '{el}'")
