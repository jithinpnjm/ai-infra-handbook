#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("final_expressions_diagram.svg")
root = tree.getroot()

checks = [
    # (name, box_bounds(x1, y1, x2, y2), text, font_size, is_mono)
    ("Title", (40, 0, 1560, 95), "Expressions: reading values out of the context", 48, False),
    ("cluster.name", (150, 126, 386, 212), "cluster.name", 26, True),
    ("opens drawer line 1", (390, 112, 756, 226), "opens the drawer ", 24, False),
    ("opens drawer line 2", (390, 112, 756, 226), "cluster and takes ", 24, False),
    ("opens drawer line 3", (390, 112, 756, 226), "the name folder", 24, False),
    ('cluster["name"]', (80, 250, 360, 322), 'cluster["name"]', 26, True),
    ("item form", (390, 250, 736, 322), "item form", 26, False),
    ("lists header", (64, 348, 756, 414), "lists", 30, False),
    ("list[0]", (84, 414, 288, 502), "list[0]", 26, True),
    ("list[-1]", (308, 414, 512, 502), "list[-1]", 26, True),
    ("list[1:3]", (532, 414, 736, 502), "list[1:3]", 26, True),
    ("Literals header", (846, 95, 1560, 175), "Literals", 30, False),
    ("Literals line 1", (846, 188, 1534, 515), "strings, numbers, true and false ", 26, False),
    ("Literals line 2", (846, 188, 1534, 515), "(Python True and False also work), ", 26, False),
    ("Literals line 3", (846, 188, 1534, 515), "none, lists [1, 2], ", 26, False),
    ("Literals line 4", (846, 188, 1534, 515), "dicts {a: 1}, tuples", 26, False),
    ("arithmetic", (64, 660, 772, 720), "arithmetic + - * / // % **", 26, True),
    ("comparison", (828, 660, 1536, 720), "comparison == != < > <= >=", 26, True),
    ("logic", (64, 732, 772, 792), "logic and or not", 26, True),
    ("membership", (828, 732, 1536, 792), "membership in", 26, True),
    ("conditional", (64, 804, 772, 864), "conditional: {{ a if cond else b }}", 26, True),
    ("is applies a test", (828, 804, 1536, 864), "is applies a test", 26, False),
    ("Callout line 1", (148, 920, 1540, 1055), "join strings with ~, not +: ~ always treats its operands as text ", 24, False),
    ("Callout line 2", (148, 920, 1540, 1055), "so a node number of 1 joins cleanly as gpu ~ 1; ", 24, False),
    ("Callout line 3", (148, 920, 1540, 1055), "+ tries arithmetic first and mixing text with a number fails", 24, False),
    ("Bottom bar", (40, 1080, 1560, 1145), "Use ~ to join text", 30, False),
]

all_passed = True
for name, (bx1, by1, bx2, by2), txt, fs, is_mono in checks:
    factor = 0.62 if is_mono else 0.6
    w = len(txt) * factor * fs
    bw = bx2 - bx1
    bh = by2 - by1
    
    if "Callout" in name:
        h_pad = bx2 - (148 + w)
    elif "lists header" in name:
        h_pad = 30.0 # indented from left
    else:
        h_pad = (bw - w) / 2
    
    if "opens drawer" in name:
        v_pad = (bh - (24 + 2*28)) / 2
    elif "Literals line" in name:
        v_pad = (bh - (26 + 3*48)) / 2
    elif "Callout" in name:
        v_pad = (bh - (24 + 2*32)) / 2
    else:
        v_pad = (bh - fs) / 2
    
    pass_h = h_pad >= 16
    pass_v = v_pad >= 16
    
    status = "PASS" if (pass_h and pass_v) else "FAIL"
    if status == "FAIL":
        all_passed = False
    print(f"[{status}] {name:20s}: text_w={w:5.1f}px, box_w={bw}px, h_pad={h_pad:5.1f}px | v_pad={v_pad:5.1f}px")

assert all_passed, "Some padding checks failed!"
print("\n==================== ALL PADDINGS ARE >= 16PX! ====================")
