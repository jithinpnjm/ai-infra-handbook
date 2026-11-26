#!/usr/bin/env python3
import sys

# Test every box with refined coordinates and line breaks

# Fonts:
# Title: 48px bold
# Box titles: 30px bold (sans factor 0.6 -> 18 px/char)
# Secondary text: 24px regular (sans factor 0.6 -> 14.4 px/char)

# Boxes definition:
# Col 1: x = 40, w = 480
# Col 2: x = 560, w = 480
# Col 3: x = 1080, w = 480

# Row 1: y = 115, h = 215 (Tile 1, Tile 2, Tile 3)
# Row 2: y = 370, h = 200 (Tile 8, Center, Tile 4)
# Row 3: y = 610, h = 320 (Tile 7, Tile 6, Tile 5)
# Row 4: y = 970, h = 190 (Fail 1, Fail 2, Fail 3)

def check_tile(name, w, h, icon_pos, title_lines, body_lines):
    # Padding constraint: "Every text line must fit inside its box with at least 16 px padding."
    pad = 18
    avail_w = w - 2 * pad # 480 - 36 = 444px
    
    icon_w = 52
    icon_gap = 14
    
    if icon_pos == "beside":
        title_avail_w = avail_w - icon_w - icon_gap # 444 - 66 = 378px
    elif icon_pos == "above":
        title_avail_w = avail_w
    else: # None
        title_avail_w = avail_w
        
    print(f"\nChecking {name} (w={w}, h={h}, title_max_w={title_avail_w}, body_max_w={avail_w}):")
    
    ok = True
    for line in title_lines:
        line_w = len(line) * 18.0
        if line_w > title_avail_w:
            print(f"  [FAIL TITLE] '{line}' w={line_w:.1f} > {title_avail_w}")
            ok = False
        else:
            print(f"  [OK TITLE] '{line}' w={line_w:.1f} <= {title_avail_w}")
            
    for line in body_lines:
        line_w = len(line) * 14.4
        if line_w > avail_w:
            print(f"  [FAIL BODY] '{line}' w={line_w:.1f} > {avail_w}")
            ok = False
        else:
            print(f"  [OK BODY] '{line}' w={line_w:.1f} <= {avail_w}")
            
    title_h = len(title_lines) * 34
    body_h = len(body_lines) * 28 if body_lines else 0
    
    if icon_pos == "beside":
        content_top = max(icon_w, title_h)
    elif icon_pos == "above":
        content_top = icon_w + 12 + title_h
    else:
        content_top = title_h
        
    total_h = pad + content_top + (14 if body_lines else 0) + body_h + pad
    
    if total_h > h:
        print(f"  [FAIL HEIGHT] total_h={total_h} > box_h={h}")
        ok = False
    else:
        print(f"  [OK HEIGHT] total_h={total_h} <= box_h={h} (slack={h - total_h}px)")
        
    return ok

all_ok = True

# Tile 1: Row 1, Col 1
# '1 Identical software state: same OS image, kernel patch level, GPU driver, NIC firmware'
ok = check_tile("Tile 1", 480, 215, "beside",
    ["1 Identical software", "state:"],
    ["same OS image, kernel patch", "level, GPU driver,", "NIC firmware"])
all_ok = all_ok and ok

# Tile 2: Row 1, Col 2
# '2 Synchronized time and identity: chrony or NTP; same numeric UID and GID everywhere'
ok = check_tile("Tile 2", 480, 215, "beside",
    ["2 Synchronized time", "and identity:"],
    ["chrony or NTP; same numeric", "UID and GID everywhere"])
all_ok = all_ok and ok

# Tile 3: Row 1, Col 3
# '3 Predictable naming and networking: DNS, hosts, DHCP and PXE, out-of-band management network, compute fabric'
ok = check_tile("Tile 3", 480, 215, "beside",
    ["3 Predictable naming", "and networking:"],
    ["DNS, hosts, DHCP and PXE,", "out-of-band management", "network, compute fabric"])
all_ok = all_ok and ok

# Tile 8: Row 2, Col 1
# '8 Spares and SLA discipline: on-site stock of key spares, vendor replacement SLAs'
ok = check_tile("Tile 8", 480, 200, "beside",
    ["8 Spares and SLA", "discipline:"],
    ["on-site stock of key spares,", "vendor replacement SLAs"])
all_ok = all_ok and ok

# Center: Row 2, Col 2
# 'one illusion of a giant computer'
ok = check_tile("Center", 480, 200, None,
    ["one illusion of a", "giant computer"],
    [])
all_ok = all_ok and ok

# Tile 4: Row 2, Col 3
# '4 Uniform shared storage: same mount paths, enforced quotas'
ok = check_tile("Tile 4", 480, 200, "beside",
    ["4 Uniform shared", "storage:"],
    ["same mount paths,", "enforced quotas"])
all_ok = all_ok and ok

# Tile 7: Row 3, Col 1
# '7 Repeatable provisioning: a replacement server boots into an identical state within minutes'
ok = check_tile("Tile 7", 480, 320, "beside",
    ["7 Repeatable", "provisioning:"],
    ["a replacement server boots", "into an identical state within", "minutes"])
all_ok = all_ok and ok

# Tile 6: Row 3, Col 2
# '6 Comprehensive observability: node health, temperatures, power supplies, air conditioning, UPS, fabric symbol errors, GPU faults'
ok = check_tile("Tile 6", 480, 320, "beside",
    ["6 Comprehensive", "observability:"],
    ["node health, temperatures,", "power supplies,", "air conditioning, UPS,", "fabric symbol errors,", "GPU faults"])
all_ok = all_ok and ok

# Tile 5: Row 3, Col 3
# '5 Centralized scheduling and accounting: users never start work on compute nodes directly; scheduler places jobs, isolates them in cgroups, logs usage'
ok = check_tile("Tile 5", 480, 320, "beside",
    ["5 Centralized", "scheduling and", "accounting:"],
    ["users never start work on", "compute nodes directly;", "scheduler places jobs,", "isolates them in cgroups,", "logs usage"])
all_ok = all_ok and ok

# Fail 1: Row 4, Col 1
# 'clock drift of a few seconds makes ranks disagree and looks like an application bug'
ok = check_tile("Fail 1", 480, 190, None,
    [],
    ["clock drift of a few seconds", "makes ranks disagree and", "looks like an application", "bug"])
all_ok = all_ok and ok

# Fail 2: Row 4, Col 2
# 'one node with an older GPU driver runs slightly slower or different and nothing in the job log points to it; compare driver versions'
ok = check_tile("Fail 2", 480, 190, None,
    [],
    ["one node with an older GPU driver", "runs slightly slower or different", "and nothing in the job log", "points to it; compare driver", "versions"])
all_ok = all_ok and ok

# Fail 3: Row 4, Col 3
# 'a different UID makes a user unable to read their own checkpoint'
ok = check_tile("Fail 3", 480, 190, None,
    [],
    ["a different UID makes a user", "unable to read their own", "checkpoint"])
all_ok = all_ok and ok

print("\nOverall Status:", "ALL OK" if all_ok else "SOME FAILED")
