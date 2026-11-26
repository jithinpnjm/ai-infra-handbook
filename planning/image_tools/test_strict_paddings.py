#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("test_yaml_structures.svg")
root = tree.getroot()

def est_w(text, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(text) * fs * rate

# 1. Table Headers:
# Bar: x=880, y=198, w=660, h=56
# Structure: x=898, w=est_w("Structure", 28, False)=151.2
# Syntax: x=1070, w=est_w("Syntax", 28, False)=100.8
# JSON or Python: x=1270, w=est_w("JSON or Python", 28, False)=235.2
print("--- Table Headers ---")
print("Structure pad L:", 898 - 880)
print("Structure to Syntax gap:", 1070 - (898 + 151.2))
print("Syntax to JSON or Python gap:", 1270 - (1070 + 100.8))
print("JSON or Python pad R:", (880 + 660) - (1270 + 235.2))

# 2. Table Rows:
# Box: x=880, w=660
# Text x=898 -> left pad = 18px!
print("\n--- Table Rows ---")
rows = [
    ('Scalar L1', 'Scalar: 42, 3.14, true, null, hello, ', True),
    ('Scalar L2', '"quoted" / number, bool, null, string', False),
    ('Seq L1', 'Sequence: - item per line, or [a, b] ', True),
    ('Seq L2', '/ array or list', False),
    ('Map L1', 'Mapping: key: value pairs, or ', True),
    ('Map L2', '{a: 1, b: 2} / object or dict', False),
]
for name, text, is_mono in rows:
    w = est_w(text, 24, is_mono)
    r_pad = (880 + 660) - (898 + w)
    print(f"{name:10s}: w={w:5.1f}, right_pad={r_pad:5.1f}")
    assert r_pad >= 16

# 3. Notes Panel:
# Box: x=880, w=660
# Text x=898 -> left pad = 18px!
print("\n--- Notes Panel ---")
notes = [
    "a parser turns each value into a typed ",
    "object before any tool reads it: the ",
    "clerk at a counter files each word as ",
    "number, true or false, or text",
    'JSON is valid YAML 1.2, so {"a": 1} ',
    "works anywhere YAML does",
    "indentation tells the parser where each ",
    "item ends, brackets do the same for short ",
    "lists; pick the form a reviewer reads ",
    "fastest and keep it consistent in each file"
]
for n in notes:
    w = est_w(n, 24, False)
    r_pad = (880 + 660) - (898 + w)
    print(f"Note line: w={w:5.1f}, right_pad={r_pad:5.1f} | '{n}'")
    assert r_pad >= 16
