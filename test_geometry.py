#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Test script for layout geometry
print("Verifying geometry...")

box_w = 660
box_h = 94

boxes = [
    ("Box 1", "baseline.yml", "baseline", "OS baseline on every host"),
    ("Box 2", "database.yml", "db", "PostgreSQL on the db group"),
    ("Box 3", "app.yml", "app", "application on the app group"),
    ("Box 4", "web.yml", "web", "nginx reverse proxy"),
    ("Box 5", "verify.yml", "verify", "end-to-end verification")
]

# Check text fitting inside each box
# Box starts at x = 470, ends at 1130
# Circle: cx = 512, r=24 -> ends at 536
# Icon: x = 550 to 606 (width 56)
# Text starts at x = 625
avail_w = 1130 - 625 - 16 # 16px right padding
print(f"Available width for text inside tier boxes: {avail_w}px")

for name, title, tag, note in boxes:
    # title is 30px bold sans (or mono)
    # tag is 24px mono in badge
    # note is 24px sans
    w_title = len(title) * 30 * 0.62 # mono
    w_tag = len(tag) * 24 * 0.62 + 24 # badge with padding
    w_note = len(note) * 24 * 0.6
    print(f"{name}:")
    print(f"  Title ({title}): {w_title:.1f}px + Tag ({tag}): {w_tag:.1f}px = {w_title + 16 + w_tag:.1f}px (avail {avail_w})")
    assert (w_title + 16 + w_tag) <= avail_w
    print(f"  Note ({note}): {w_note:.1f}px (avail {avail_w})")
    assert w_note <= avail_w

print("All tier box text fits with >= 16px padding!")
