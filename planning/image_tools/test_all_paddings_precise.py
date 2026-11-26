import re

boxes = []

def add_box(name, bx, by, bw, bh, lines, font_size, is_mono, text_anchor="start", tx=None, start_y=None, line_spacing=32):
    boxes.append({
        "name": name,
        "bx": bx, "by": by, "bw": bw, "bh": bh,
        "lines": lines,
        "font_size": font_size,
        "is_mono": is_mono,
        "text_anchor": text_anchor,
        "tx": tx,
        "start_y": start_y,
        "line_spacing": line_spacing
    })

# 1. Left Title (in Left Panel Header: x=40, y=140, w=740, h=80)
add_box("Left Title", 40, 140, 740, 80, [
    "Default (weak host)"
], 30, False, "start", 135, 192, 0)

# 2. Wrong Port Box (in Switch)
# x=285, y=260, w=345, h=100
add_box("Wrong Port Box", 285, 260, 345, 100, [
    "learns the IP on",
    "the wrong port"
], 24, False, "middle", 457.5, 303, 32)

# 3. eth0 box
add_box("eth0 Box", 90, 465, 300, 95, [
    "eth0 10.20.0.1"
], 26, True, "middle", 240, 522, 0)

# 4. eth1 box
add_box("eth1 Box", 430, 465, 300, 95, [
    "eth1 10.20.0.2"
], 26, True, "middle", 580, 522, 0)

# 5. Caption Box
add_box("Caption Box", 65, 605, 690, 100, [
    "Linux answers an ARP request",
    "for any local IP on any interface"
], 24, False, "middle", 410, 646, 32)

# 6. Right Title (in Right Panel Header: x=820, y=140, w=740, h=80)
add_box("Right Title", 820, 140, 740, 80, [
    "Recipe for multi-homed servers"
], 30, False, "start", 915, 192, 0)

# 7. Recipe 1 Card
add_box("Recipe 1 Card", 845, 235, 690, 96, [
    "arp_ignore=1: reply only if the target IP",
    "is configured on the receiving interface"
], 24, False, "start", 870, 276, 32)

# 8. Recipe 2 Card
add_box("Recipe 2 Card", 845, 345, 690, 126, [
    "arp_announce=2: always use the best",
    "source address of the outgoing interface",
    "in ARP requests"
], 24, False, "start", 870, 385, 32)

# 9. Recipe 3 Card
add_box("Recipe 3 Card", 845, 485, 690, 96, [
    "rp_filter=2: loose reverse path filtering",
    "(strict mode 1 drops asymmetric traffic)"
], 24, False, "start", 870, 526, 32)

# 10. Recipe 4 Card
add_box("Recipe 4 Card", 845, 595, 690, 126, [
    "policy routing with one routing table per NIC",
    "so replies leave on the interface that",
    "received the request"
], 24, False, "start", 870, 635, 32)

# 11. Footer Strip (x=40, y=835, w=1520, h=120)
add_box("Footer Strip", 40, 835, 1520, 120, [
    "Also: arp_filter=1 answers only if the route to the sender would use this interface;",
    "arp_notify sends a gratuitous ARP when an interface comes up or the address changes;",
    "all keys are per interface"
], 24, False, "middle", 800, 874, 30)

# 12. Result Row Strip (x=40, y=965, w=1520, h=95)
add_box("Result Row Strip", 40, 965, 1520, 95, [
    "Symptoms without the recipe: asymmetric paths, RDMA and NCCL oddities,",
    "flapping MAC tables, confused bonding; often seen only after another NIC is plugged in"
], 24, False, "middle", 800, 1004, 32)

# 13. Bottom Bar Strip (x=40, y=1070, w=1520, h=90)
add_box("Bottom Bar Strip", 40, 1070, 1520, 90, [
    "Each setting makes the server answer only for the address",
    "that belongs to the card the question arrived on"
], 24, False, "middle", 800, 1108, 32)

all_passed = True
for b in boxes:
    rate = 0.62 if b["is_mono"] else 0.6
    max_w = max(len(l) * b["font_size"] * rate for l in b["lines"])
    
    if b["text_anchor"] == "middle":
        left = b["tx"] - max_w / 2
        right = b["tx"] + max_w / 2
        pad_l = left - b["bx"]
        pad_r = (b["bx"] + b["bw"]) - right
    else:
        pad_l = b["tx"] - b["bx"]
        pad_r = (b["bx"] + b["bw"]) - (b["tx"] + max_w)
    
    # Text height
    top_t = b["start_y"] - 0.75 * b["font_size"]
    bot_t = (b["start_y"] + (len(b["lines"]) - 1) * b["line_spacing"]) + 0.25 * b["font_size"]
    pad_t = top_t - b["by"]
    pad_b = (b["by"] + b["bh"]) - bot_t
    
    ok = (pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16)
    if not ok:
        all_passed = False
    print(f"[{'PASS' if ok else 'FAIL'}] {b['name']:20s}: pad_l={pad_l:5.1f}, pad_r={pad_r:5.1f}, pad_t={pad_t:5.1f}, pad_b={pad_b:5.1f} | max_w={max_w:6.1f}, bw={b['bw']}")

print("\nAll boxes passed padding check:", all_passed)
