#!/usr/bin/env python3
import math

def wrap_text(text, max_width, font_size, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    char_w = font_size * factor
    max_chars = int(max_width / char_w)
    
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        w_len = len(w)
        if not curr:
            curr.append(w)
            curr_len = w_len
        elif curr_len + 1 + w_len <= max_chars:
            curr.append(w)
            curr_len += 1 + w_len
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = w_len
    if curr:
        lines.append(" ".join(curr))
    return lines

print("=== TESTING LAYOUT 2 (2 columns: width 700 each) ===")
# Usable inner text width in a 690px card with icon:
# Card width = 690. Icon width = 56, padding = 30 left, 20 gap, 30 right -> text_width = 690 - 30 - 56 - 20 - 30 = 554 px.
w_text = 550
font_size = 26

l1 = "startupProbe: periodSeconds 10, failureThreshold 180, up to 30 minutes; liveness and readiness are disabled until it succeeds once"
lines1 = wrap_text(l1, w_text, font_size)
print(f"startupProbe ({len(lines1)} lines):")
for ln in lines1:
    print(f"  [{len(ln)}c, {len(ln)*font_size*0.6:.1f}px] '{ln}'")

l2 = "readinessProbe periodSeconds 5: on failure the pod IP leaves the EndpointSlices, container is NOT restarted"
lines2 = wrap_text(l2, w_text, font_size)
print(f"\nreadinessProbe ({len(lines2)} lines):")
for ln in lines2:
    print(f"  [{len(ln)}c, {len(ln)*font_size*0.6:.1f}px] '{ln}'")

l3 = "livenessProbe periodSeconds 20, failureThreshold 6: restarts only after 2 full minutes of no response"
lines3 = wrap_text(l3, w_text, font_size)
print(f"\nlivenessProbe ({len(lines3)} lines):")
for ln in lines3:
    print(f"  [{len(ln)}c, {len(ln)*font_size*0.6:.1f}px] '{ln}'")

l4 = "during loading the server downloads or maps weights and captures CUDA graphs"
lines4 = wrap_text(l4, w_text, font_size)
print(f"\nLeft note ({len(lines4)} lines):")
for ln in lines4:
    print(f"  [{len(ln)}c, {len(ln)*font_size*0.6:.1f}px] '{ln}'")

l5 = "liveness with no startup probe on a slow starter creates a restart loop"
lines5 = wrap_text(l5, w_text, font_size)
print(f"\nRed cross note ({len(lines5)} lines):")
for ln in lines5:
    print(f"  [{len(ln)}c, {len(ln)*font_size*0.6:.1f}px] '{ln}'")
