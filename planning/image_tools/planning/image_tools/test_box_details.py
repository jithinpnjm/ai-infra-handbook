#!/usr/bin/env python3
import sys

# Test every box in detail

# Fonts:
# Title: 48px bold
# Box titles: 30px bold (sans factor 0.6 -> 18 px/char)
# Secondary text: 24px regular (sans factor 0.6 -> 14.4 px/char)

# Boxes definition:
# Col 1: x = 40, w = 480
# Col 2: x = 560, w = 480
# Col 3: x = 1080, w = 480

# Row 1: y = 120, h = 215 (Tile 1, Tile 2, Tile 3)
# Row 2: y = 375, h = 180 (Tile 8, Center, Tile 4)
# Row 3: y = 595, h = 275 (Tile 7, Tile 6, Tile 5)
# Row 4: y = 910, h = 250 (Fail 1, Fail 2, Fail 3)

def check_box(name, w, h, icon_beside, title_lines, body_lines):
    # Padding: 20px
    left_pad = 24
    right_pad = 24
    top_pad = 24
    bot_pad = 20
    
    avail_w = w - left_pad - right_pad # 480 - 48 = 432px
    
    icon_w = 52
    icon_gap = 16
    
    if icon_beside:
        title_avail_w = avail_w - icon_w - icon_gap # 432 - 68 = 364px
    else:
        title_avail_w = avail_w
        
    print(f"\nChecking {name} (w={w}, h={h}, title_max_w={title_avail_w}, body_max_w={avail_w}):")
    
    ok = True
    # Check title lines
    for line in title_lines:
        line_w = len(line) * 18.0
        if line_w > title_avail_w:
            print(f"  [FAIL TITLE] '{line}' w={line_w:.1f} > {title_avail_w}")
            ok = False
        else:
            print(f"  [OK TITLE] '{line}' w={line_w:.1f} <= {title_avail_w}")
            
    # Check body lines
    for line in body_lines:
        line_w = len(line) * 14.4
        if line_w > avail_w:
            print(f"  [FAIL BODY] '{line}' w={line_w:.1f} > {avail_w}")
            ok = False
        else:
            print(f"  [OK BODY] '{line}' w={line_w:.1f} <= {avail_w}")
            
    # Check vertical height:
    # Title line height: 34px
    # Body line height: 28px
    # Gap between title and body: 14px
    title_h = len(title_lines) * 34
    body_h = len(body_lines) * 28 if body_lines else 0
    content_top = max(icon_w, title_h) if icon_beside else (icon_w + 14 + title_h if icon_w else title_h)
    total_h = top_pad + content_top + (14 if body_lines else 0) + body_h + bot_pad
    
    if total_h > h:
        print(f"  [FAIL HEIGHT] total_h={total_h} > box_h={h}")
        ok = False
    else:
        print(f"  [OK HEIGHT] total_h={total_h} <= box_h={h} (slack={h - total_h}px)")
        
    return ok

all_ok = True

# Tile 1: Row 1, Col 1
# '1 Identical software state: same OS image, kernel patch level, GPU driver, NIC firmware'
ok = check_box("Tile 1", 480, 215, True,
    ["1 Identical software", "state:"],
    ["same OS image, kernel patch", "level, GPU driver, NIC firmware"])
all_ok = all_ok and ok

# Tile 2: Row 1, Col 2
# '2 Synchronized time and identity: chrony or NTP; same numeric UID and GID everywhere'
ok = check_box("Tile 2", 480, 215, True,
    ["2 Synchronized time", "and identity:"],
    ["chrony or NTP; same numeric", "UID and GID everywhere"])
all_ok = all_ok and ok

# Tile 3: Row 1, Col 3
# '3 Predictable naming and networking: DNS, hosts, DHCP and PXE, out-of-band management network, compute fabric'
ok = check_box("Tile 3", 480, 215, True,
    ["3 Predictable naming", "and networking:"],
    ["DNS, hosts, DHCP and PXE,", "out-of-band management", "network, compute fabric"])
all_ok = all_ok and ok

# Tile 8: Row 2, Col 1
# '8 Spares and SLA discipline: on-site stock of key spares, vendor replacement SLAs'
ok = check_box("Tile 8", 480, 180, True,
    ["8 Spares and SLA", "discipline:"],
    ["on-site stock of key spares,", "vendor replacement SLAs"])
all_ok = all_ok and ok

# Center: Row 2, Col 2
# 'one illusion of a giant computer'
ok = check_box("Center", 480, 180, False,
    ["one illusion of a", "giant computer"],
    [])
all_ok = all_ok and ok

# Tile 4: Row 2, Col 3
# '4 Uniform shared storage: same mount paths, enforced quotas'
ok = check_box("Tile 4", 480, 180, True,
    ["4 Uniform shared", "storage:"],
    ["same mount paths,", "enforced quotas"])
all_ok = all_ok and ok

# Tile 7: Row 3, Col 1
# '7 Repeatable provisioning: a replacement server boots into an identical state within minutes'
ok = check_box("Tile 7", 480, 275, True,
    ["7 Repeatable", "provisioning:"],
    ["a replacement server boots", "into an identical state within", "minutes"])
all_ok = all_ok and ok

# Tile 6: Row 3, Col 2
# '6 Comprehensive observability: node health, temperatures, power supplies, air conditioning, UPS, fabric symbol errors, GPU faults'
ok = check_box("Tile 6", 480, 275, True,
    ["6 Comprehensive", "observability:"],
    ["node health, temperatures,", "power supplies, air conditioning,", "UPS, fabric symbol errors,", "GPU faults"])
all_ok = all_ok and ok

# Tile 5: Row 3, Col 3
# '5 Centralized scheduling and accounting: users never start work on compute nodes directly; scheduler places jobs, isolates them in cgroups, logs usage'
ok = check_box("Tile 5", 480, 275, True,
    ["5 Centralized", "scheduling & acc:", "accounting:"], # wait let's check exact wording
    ["users never start work on", "compute nodes directly;", "scheduler places jobs,", "isolates them in cgroups,", "logs usage"])
all_ok = all_ok and ok

print("\nOverall Status:", "ALL OK" if all_ok else "SOME FAILED")
