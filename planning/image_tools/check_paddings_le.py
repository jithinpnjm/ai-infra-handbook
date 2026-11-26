import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate_le.svg")
root = tree.getroot()

print("Checking text line widths and paddings:")

texts_to_check = [
    {
        "desc": "Title Line 1",
        "text": "Histogram buckets: keep le,",
        "fs": 48,
        "type": "sans",
        "box_w": 1600,
        "x_center": 800
    },
    {
        "desc": "Title Line 2",
        "text": "then take the quantile once",
        "fs": 48,
        "type": "sans",
        "box_w": 1600,
        "x_center": 800
    },
    {
        "desc": "Left note Line 1",
        "text": "Each box counts",
        "fs": 24,
        "type": "sans",
        "box_w": 500,
        "x_center": 300
    },
    {
        "desc": "Left note Line 2",
        "text": "every request at or",
        "fs": 24,
        "type": "sans",
        "box_w": 500,
        "x_center": 300
    },
    {
        "desc": "Left note Line 3",
        "text": "under its bound: cumulative",
        "fs": 24,
        "type": "sans",
        "box_w": 500,
        "x_center": 300
    },
    {
        "desc": "Middle label Line 1",
        "text": "histogram_quantile",
        "fs": 24,
        "type": "monospace",
        "box_w": 380,
        "x_center": 780
    },
    {
        "desc": "Middle label Line 2",
        "text": "interpolates inside",
        "fs": 24,
        "type": "sans",
        "box_w": 380,
        "x_center": 780
    },
    {
        "desc": "Middle label Line 3",
        "text": "the bucket that",
        "fs": 24,
        "type": "sans",
        "box_w": 380,
        "x_center": 780
    },
    {
        "desc": "Middle label Line 4",
        "text": "holds the quantile",
        "fs": 24,
        "type": "sans",
        "box_w": 380,
        "x_center": 780
    },
    {
        "desc": "Row 1 Title Line 1",
        "text": "Trap: sum by (model)",
        "fs": 25,
        "type": "sans",
        "box_left": 1120,
        "box_right": 1525 # card ends at 1035+490=1525
    },
    {
        "desc": "Row 1 Title Line 2",
        "text": "drops le",
        "fs": 25,
        "type": "sans",
        "box_left": 1120,
        "box_right": 1525
    },
    {
        "desc": "Row 1 Note",
        "text": "Breaks histogram_quantile",
        "fs": 24,
        "type": "sans",
        "box_w": 490,
        "x_center": 1280
    },
    {
        "desc": "Row 2 Title",
        "text": "Right: sum by (le, model)",
        "fs": 25,
        "type": "sans",
        "box_left": 1120,
        "box_right": 1525
    },
    {
        "desc": "Row 2 Note Line 1",
        "text": "Keep le in the by clause,",
        "fs": 24,
        "type": "sans",
        "box_w": 490,
        "x_center": 1280
    },
    {
        "desc": "Row 2 Note Line 2",
        "text": "then take the quantile once",
        "fs": 24,
        "type": "sans",
        "box_w": 490,
        "x_center": 1280
    },
    {
        "desc": "Pod A buckets",
        "text": "Pod A buckets",
        "fs": 24,
        "type": "sans",
        "box_w": 250,
        "x_center": 205
    },
    {
        "desc": "Pod B buckets",
        "text": "Pod B buckets",
        "fs": 24,
        "type": "sans",
        "box_w": 250,
        "x_center": 205
    },
    {
        "desc": "rate per series",
        "text": "rate per series",
        "fs": 25,
        "type": "sans",
        "box_w": 280,
        "x_center": 530
    },
    {
        "desc": "sum by (le, model)",
        "text": "sum by (le, model)",
        "fs": 24,
        "type": "monospace",
        "box_w": 340,
        "x_center": 890
    },
    {
        "desc": "histogram_quantile(0.99)",
        "text": "histogram_quantile(0.99)",
        "fs": 24,
        "type": "monospace",
        "box_w": 410,
        "x_center": 1315
    },
    {
        "desc": "Caption Bar",
        "text": "le stands for less than or equal to.",
        "fs": 28,
        "type": "sans",
        "box_w": 1500,
        "x_center": 800
    }
]

all_pass = True
for item in texts_to_check:
    factor = 0.62 if item["type"] == "monospace" else 0.60
    estimated_w = len(item["text"]) * factor * item["fs"]
    
    if "box_w" in item and "x_center" in item:
        total_pad = item["box_w"] - estimated_w
        side_pad = total_pad / 2
    elif "box_left" in item and "box_right" in item:
        avail_w = item["box_right"] - item["box_left"]
        side_pad = avail_w - estimated_w
    else:
        side_pad = 0
        
    status = "OK" if side_pad >= 16 else "FAIL"
    if side_pad < 16:
        all_pass = False
    print(f"[{status}] {item['desc']:25s} | len={len(item['text']):2d} | est_w={estimated_w:5.1f}px | pad={side_pad:5.1f}px | text='{item['text']}'")

assert all_pass, "Some text lines have < 16px padding!"
print("\nALL PADDING CHECKS PASSED!")
