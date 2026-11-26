import math

def check_diamond_icon_above(rx, ry, tw, th, iw, ih, gap=10):
    # cy = 0
    # Icon is at x in [-iw/2, iw/2], y in [-ih - gap/2, -gap/2]
    # Text is at x in [-tw/2, tw/2], y in [gap/2, gap/2 + th]
    # Or center the whole group:
    total_h = ih + gap + th
    top_icon = -total_h / 2
    bot_icon = top_icon + ih
    top_text = bot_icon + gap
    bot_text = top_text + th
    
    scale = math.sqrt(1/(rx*rx) + 1/(ry*ry))
    
    # Check corners of icon:
    icon_corners = [(-iw/2, top_icon), (iw/2, top_icon), (-iw/2, bot_icon), (iw/2, bot_icon)]
    # Check corners of text:
    text_corners = [(-tw/2, top_text), (tw/2, top_text), (-tw/2, bot_text), (tw/2, bot_text)]
    
    min_d = 9999
    for px, py in icon_corners + text_corners:
        val = abs(px)/rx + abs(py)/ry
        d = (1.0 - val) / scale
        if d < min_d:
            min_d = d
    return min_d

print("rx=180, ry=85:", check_diamond_icon_above(180, 85, 156, 28, 32, 32))
print("rx=190, ry=90:", check_diamond_icon_above(190, 90, 156, 28, 32, 32))
print("rx=200, ry=95:", check_diamond_icon_above(200, 95, 156, 28, 32, 32))
print("rx=180, ry=95 (b succeeded):", check_diamond_icon_above(180, 95, 170, 27, 32, 32))
print("rx=190, ry=95 (b succeeded):", check_diamond_icon_above(190, 95, 170, 27, 32, 32))
