import math

def check_box(box_name, bx, by, bw, bh, lines, font_size, text_x, text_anchor="start", is_mono=False, icon_r=0):
    char_factor = 0.62 if is_mono else 0.6
    cap_h = font_size * 0.72
    desc_h = font_size * 0.22
    
    print(f"=== {box_name} (x={bx}, y={by}, w={bw}, h={bh}) ===")
    
    # Check lines
    for i, (txt, dy, fs) in enumerate(lines):
        line_w = len(txt) * char_factor * fs
        if text_anchor == "middle":
            lx = text_x - line_w / 2
            rx = text_x + line_w / 2
        elif text_anchor == "start":
            lx = text_x
            rx = text_x + line_w
        else:
            rx = text_x
            lx = text_x - line_w
            
        pad_l = lx - bx
        pad_r = (bx + bw) - rx
        
        # Check against icon if present
        if icon_r > 0:
            pad_icon = lx - icon_r
            print(f"  Line {i+1}: '{txt}' (w={line_w:.1f}px)")
            print(f"    pad_l={pad_l:.1f}, pad_icon={pad_icon:.1f}, pad_r={pad_r:.1f}")
            assert pad_icon >= 16, f"Icon collision in {box_name}: {pad_icon} < 16"
        else:
            print(f"  Line {i+1}: '{txt}' (w={line_w:.1f}px)")
            print(f"    pad_l={pad_l:.1f}, pad_r={pad_r:.1f}")
            assert pad_l >= 16, f"Left padding violated in {box_name}: {pad_l} < 16"
            assert pad_r >= 16, f"Right padding violated in {box_name}: {pad_r} < 16"

# Test Client capture: bx=40, by=96, bw=380, bh=96
# icon at x=60, w=56 -> icon_r = 116
# text_x = 136, text_anchor = "start", font_size = 30 bold
check_box("Client capture", 40, 96, 380, 96, [("client capture", 0, 30)], 30, 136, "start", False, 116)

# Test Server capture: bx=1180, by=96, bw=380, bh=96
# icon at x=1200, w=56 -> icon_r = 1256
# text_x = 1276, text_anchor = "start", font_size = 30 bold
check_box("Server capture", 1180, 96, 380, 96, [("server capture", 0, 30)], 30, 1276, "start", False, 1256)

# Test Middlebox: bx=480, by=96, bw=640, bh=96
# icon at x=500, w=56 -> icon_r = 556
# text: "path, firewall, NAT, load balancer" (35 chars)
# If split into 2 lines:
# "path, firewall," (15 chars)
# "NAT, load balancer" (18 chars)
# text_x = 580, text_anchor="start", font_size=26 bold
check_box("Middlebox", 480, 96, 640, 96, [
    ("path, firewall,", 0, 26),
    ("NAT, load balancer", 30, 26)
], 26, 580, "start", False, 556)
