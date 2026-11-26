#!/usr/bin/env python3

# Let's test text wrapping for all labels in their respective columns!

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    for w in words:
        if curr and len(" ".join(curr + [w])) > max_chars:
            lines.append(" ".join(curr))
            curr = [w]
        else:
            curr.append(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

# Let's test Col 1 (pre_tasks):
col1_items = [
    "assert app_version is a tag or commit SHA",
    "touch drain flag under /var/www/lb-drain delegated to the first web host",
    "pause 5 seconds"
]

print("--- Col 1 (pre_tasks) width ~ 330px (avail ~ 290px, ~ 20 chars per line) ---")
for item in col1_items:
    lines = wrap_text(item, 20)
    print(f"Item: '{item}' -> {len(lines)} lines:")
    for l in lines:
        print(f"   '{l}' (w = {len(l)*0.6*24:.1f} px)")

