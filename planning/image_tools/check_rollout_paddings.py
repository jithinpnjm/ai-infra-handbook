import xml.etree.ElementTree as ET
import re

# Conservative text width calculation
# sans 0.6 * font-size * chars, monospace 0.62 * font-size * chars

boxes_and_text = [
    # (box_desc, box_x, box_w, text_x, text, font_type, font_size, align)
    ("Title Line 1", 0, 1600, 800, "A bad rollout, ", "sans", 48, "center"),
    ("Title Line 2", 0, 1600, 800, "from first failed request to the rollback", "sans", 48, "center"),
    
    # Step 1
    ("Step 1 Title", 40, 1090, 175, "Rollout starts", "sans", 30, "left"),
    ("Step 1 Detail", 40, 1090, 60, "A rollout breaks the model for 12 minutes and all requests fail.", "sans", 24, "left"),
    
    # Step 2
    ("Step 2 Title", 40, 1090, 175, "First failing requests reach the gateway", "sans", 30, "left"),
    ("Step 2 Detail", 40, 1090, 60, "The error ratio is 100 percent.", "sans", 24, "left"),
    
    # Step 3
    ("Step 3 Title", 40, 1090, 175, "Fast burn short window goes above the threshold", "sans", 30, "left"),
    ("Step 3 Detail", 40, 1090, 60, "The 5 minute window has enough data and is above 1.44 percent.", "sans", 24, "left"),
    
    # Step 4
    ("Step 4 Title", 40, 1090, 175, "Long window is still catching up", "sans", 30, "left"),
    ("Step 4 Detail", 40, 1090, 60, "The page waits until both windows agree.", "sans", 24, "left"),
    
    # Step 5
    ("Step 5 Title", 40, 1090, 175, "Page fires in about 52 seconds", "sans", 30, "left"),
    ("Step 5 Detail", 40, 1090, 60, "Both windows are above the threshold, so the on-call engineer is paged.", "sans", 24, "left"),
    
    # Step 6
    ("Step 6 Title", 40, 1090, 175, "On-call engineer rolls back", "sans", 30, "left"),
    ("Step 6 Detail", 40, 1090, 60, "The error ratio drops once the bad release is removed.", "sans", 24, "left"),
    
    # Step 7
    ("Step 7 Title", 40, 1090, 175, "Short window clears first", "sans", 30, "left"),
    ("Step 7 Detail", 40, 1090, 60, "The alert clears within minutes of the rollback, before the long window.", "sans", 24, "left"),
    
    # Gap near step 5 (clock text)
    ("Clock Text", 1130, 110, 1185, "clock", "sans", 24, "center"),
    
    # Budget spent box
    ("Budget Title", 1240, 320, 1400, "Budget spent", "sans", 30, "center"),
    ("Budget Mono", 1250, 300, 1400, "12 / 43.2 = 27.8%", "mono", 24, "center"),
    ("Budget Sans Line 1", 1240, 320, 1400, "of a 30 day ", "sans", 24, "center"),
    ("Budget Sans Line 2", 1240, 320, 1400, "99.9 percent budget", "sans", 24, "center"),
    
    # Takeaway
    ("Takeaway", 40, 1520, 800, "Tie the freeze decision to the written error budget policy and do not improvise it.", "sans", 25, "center")
]

print("Checking text paddings (conservative rule >= 16px):")
for desc, bx, bw, tx, text, ftype, fsize, align in boxes_and_text:
    factor = 0.62 if ftype == "mono" else 0.6
    tw = len(text) * factor * fsize
    if align == "center":
        pad_left = (tx - tw/2.0) - bx
        pad_right = (bx + bw) - (tx + tw/2.0)
    else:
        pad_left = tx - bx
        pad_right = (bx + bw) - (tx + tw)
    
    ok = (pad_left >= 16 and pad_right >= 16)
    print(f"[{'PASS' if ok else 'FAIL'}] {desc}: pad_l={pad_left:.1f}px, pad_r={pad_right:.1f}px (tw={tw:.1f}px in box_w={bw}px)")
    assert ok, f"Padding failed for {desc}"

print("\nALL TEXT PADDINGS >= 16px PASS!")
