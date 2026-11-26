#!/usr/bin/env python3

def calc_text_width(text, font_size, is_mono=False):
    factor = 0.62 if is_mono else 0.6
    return len(text) * factor * font_size

# Let's test lines:
print("--- cluster.name & opens the drawer ---")
code1 = "cluster.name"
print("cluster.name (mono 26):", calc_text_width(code1, 26, True)) # 193.4px

# If we have 3 lines for opens the drawer cluster and takes the name folder:
desc1_lines = ["opens the drawer cluster ", "and takes the name folder"]
for l in desc1_lines:
    print(f"'{l}' (sans 24):", calc_text_width(l, 24, False))

# If 3 lines:
desc1_3lines = ["opens the drawer cluster", "and takes the ", "name folder"]
for l in desc1_3lines:
    print(f"'{l}' (sans 24):", calc_text_width(l, 24, False))

print("\n--- cluster['name'] & item form ---")
code2 = 'cluster["name"]'
print('cluster["name"] (mono 26):', calc_text_width(code2, 26, True)) # 241.8px
desc2 = "item form"
print("item form (sans 26 bold):", calc_text_width(desc2, 26, False)) # 140.4px

print("\n--- lists & items ---")
print("list[0] (mono 24):", calc_text_width("list[0]", 24, True)) # 104.2px
print("list[-1] (mono 24):", calc_text_width("list[-1]", 24, True)) # 119.0px
print("list[1:3] (mono 24):", calc_text_width("list[1:3]", 24, True)) # 133.9px

print("\n--- Literals ---")
lit_text = "strings, numbers, true and false (Python True and False also work), none, lists [1, 2], dicts {a: 1}, tuples"
# Let's split into lines:
lit_lines = [
    "strings, numbers, true and false ",
    "(Python True and False also work), ",
    "none, lists [1, 2], dicts {a: 1}, tuples"
]
for l in lit_lines:
    print(f"'{l}' (sans 24):", calc_text_width(l, 24, False))

print("\n--- Operators ---")
ops = [
    ("arithmetic + - * / // % **", True),
    ("comparison == != < > <= >=", True),
    ("logic and or not", True),
    ("membership in", True),
    ("conditional: {{ a if cond else b }}", True),
    ("is applies a test", False)
]
for op, mono in ops:
    print(f"'{op}' (size 24 mono={mono}):", calc_text_width(op, 24, mono))

print("\n--- Callout ---")
callout_lines = [
    "join strings with ~, not +: ~ always treats its operands as text ",
    "so a node number of 1 joins cleanly as gpu ~ 1; ",
    "+ tries arithmetic first and mixing text with a number fails"
]
for l in callout_lines:
    print(f"'{l}' (sans 24):", calc_text_width(l, 24, False))

print("\n--- Bottom bar ---")
bb = "Use ~ to join text"
print("Use ~ to join text (sans 30):", calc_text_width(bb, 30, False))
