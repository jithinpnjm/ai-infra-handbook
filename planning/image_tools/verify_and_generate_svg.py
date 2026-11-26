import re

# Font estimation rules:
# sans: len(text) * size * 0.6
# mono: len(text) * size * 0.62

def w_sans(text, size=24):
    return len(text) * size * 0.6

def w_mono(text, size=24):
    return len(text) * size * 0.62

# Let's verify every box and text position:

boxes = {}

# 1. Title: x=40, y=70 (line 1), y=118 (line 2)
# Text: "Why a published Docker port", "ignores your firewall rule"
# Size: 48px bold.
t1_w = w_sans("Why a published Docker port", 48)
t2_w = w_sans("ignores your firewall rule", 48)
print(f"Title L1: w={t1_w:.1f}px (fits in 1520px? {t1_w < 1520})")
print(f"Title L2: w={t2_w:.1f}px (fits in 1520px? {t2_w < 1520})")

# 2. Client box:
# x=40..450 (w=410), y=160..240 (h=80)
# Icon at x=55, y=172 (size 56x56)
# Step 1 badge: r=18 at x=130, y=180
# Text at x=155:
# Line 1: "Client on the office" (20 chars) -> wait, text_w = 288px.
# 410 - 155 = 255px! 288 > 255!
# Let's wrap Client text onto 3 lines:
# Line 1: "Client on the" (13 chars * 14.4 = 187.2px < 255px)
# Line 2: "office network or" (17 chars * 14.4 = 244.8px < 255px)
# Line 3: "anywhere" (8 chars * 14.4 = 115.2px < 255px)
# At 3 lines: y=185, 208, 231 (dy=23).
print("\nClient 3 lines:")
for l in ["Client on the", "office network or", "anywhere"]:
    print(f"  '{l}' w={w_sans(l, 24):.1f}px <= 255px")

# 3. Host NIC box:
# x=570..980 (w=410), y=160..240 (h=80)
# Icon at x=590, y=172 (size 56x56)
# Step 2 badge: r=18 at x=670, y=200
# Text at x=705, y=208: "Host NIC" (30px bold)
# w_sans("Host NIC", 30) = 8 * 30 * 0.6 = 144px.
# Available: 980 - 705 = 275px! 144 < 275!
print(f"\nHost NIC: w={w_sans('Host NIC', 30):.1f}px <= 275px")

# 4. Netfilter chains container:
# x=40..980 (w=940), y=280..490 (h=210)
# Header: icon at x=60, y=290 (size 32x32), Step 3 badge r=16 at x=105, y=306
# Text at x=130, y=312: "netfilter chains" (30px bold)
# w_sans("netfilter chains", 30) = 16 * 18 = 288px.
print(f"\nNetfilter header: w={w_sans('netfilter chains', 30):.1f}px")

# Inside Netfilter chains:
# Docker rules box:
# x=60..490 (w=430), y=330..475 (h=145)
# Available inner width: 430 - 32 = 398px.
# Text:
d_lines = [
    "Docker's own NAT and",
    "FORWARD rules (DOCKER",
    "chain) are inserted ahead",
    "of the rules managed by",
    "ufw or firewalld"
]
print("\nDocker rules lines:")
for l in d_lines:
    w = w_sans(l, 24)
    print(f"  '{l}' w={w:.1f}px (fits in 398px? {w < 398})")

# Firewall rule box (beside it, skipped):
# x=530..960 (w=430), y=330..475 (h=145)
# Available inner width: 430 - 32 = 398px.
# Text:
f_lines = [
    "ufw or firewalld rule that",
    "should block the port"
]
print("\nFW rule lines:")
for l in f_lines:
    w = w_sans(l, 24)
    print(f"  '{l}' w={w:.1f}px (fits in 398px? {w < 398})")

# 5. Container port 80 box:
# x=60..340 (w=280), y=530..600 (h=70)
# Available inner width: 280 - 32 = 248px.
# Icon at x=75, y=540 (size 40x40). Step 5 badge at x=125, y=565.
# Text at x=155, y=572: "container port 80" (font-size 26px bold? 17 chars * 26 * 0.6 = 265.2 > 248!)
# If 2 lines:
# Line 1: "container" (9 chars * 26 * 0.6 = 140.4px)
# Line 2: "port 80" (7 chars * 26 * 0.6 = 109.2px)
# At 2 lines, available width for text is 340 - 155 = 185px! Both fit!
print(f"\nContainer port 80: L1 w={w_sans('container', 26):.1f}px, L2 w={w_sans('port 80', 26):.1f}px <= 185px")

# 6. Orange arrow & label:
# Arrow from Docker rules bottom (x=200, y=475) to Container port 80 top (x=200, y=530).
# Label in clear space to the right of the arrow:
# x=225 to 550.
# Line 1: "published port 8080" (19 chars * 14.4 = 273.6px)
# Line 2: "answers from anywhere" (21 chars * 14.4 = 302.4px)
# y=498, y=522.
# Fits completely in x=225..550 without overlapping arrow (x=200) or FW box (y ends at 475, FW box starts at x=530)!
print(f"\nOrange arrow label: L1 w={w_sans('published port 8080', 24):.1f}px, L2 w={w_sans('answers from anywhere', 24):.1f}px")

# 7. Fixes box:
# x=40..980 (w=940), y=640..800 (h=160)
# Icon at x=60, y=655 (size 56x56)
# Text starts at x=135, inner max = 940 - 135 - 20 = 785px.
fix_lines = [
    "restrict a port with the DOCKER-USER chain",
    "bind the port to a specific address (for example",
    "127.0.0.1:8080:80)",
    "if a published port must stay private on a shared host,",
    "restrict it in DOCKER-USER before you publish it"
]
print("\nFixes lines:")
for l in fix_lines:
    w = w_sans(l, 24)
    print(f"  '{l}' w={w:.1f}px (fits in 785px? {w < 785})")

# 8. Right panel: Docker network modes
# x=1020..1560 (w=540), y=160..800 (h=640)
# Inner width = 540 - 48 = 492px.
rm_lines = [
    "bridge: private subnet, veth per",
    "container, NAT outbound, -p",
    "publishes via DNAT; user-defined",
    "bridges add DNS-based name",
    "resolution and isolation",
    "host: shares the host namespace,",
    "no isolation, no NAT, best",
    "performance, ports conflict with",
    "host: NCCL or HPC containers",
    "none: only loopback",
    "container:NAME: shares another",
    "container's namespace (how a",
    "Kubernetes pod works)",
    "overlay: VXLAN across Docker hosts",
    "(Swarm)",
    "macvlan or ipvlan: container on",
    "the physical network"
]
print("\nRight panel lines:")
for l in rm_lines:
    w = w_sans(l, 24)
    assert w <= 492, f"Overflow in right panel: {l}"
print("  All 17 right panel lines fit in 492px!")

# 9. Model strip:
# x=40..1560 (w=1520), y=840..920 (h=80)
# Icon at x=60, y=852 (size 56x56)
# Text at x=135, inner max = 1560 - 135 - 20 = 1405px.
cnm_lines = [
    "CNM: sandbox (the namespace config), endpoint (the attachment, typically a veth),",
    "network (a group of endpoints); local drivers bridge, host, none, macvlan, ipvlan;",
    "global driver overlay needs a key-value store"
]
print("\nCNM lines:")
for l in cnm_lines:
    w = w_sans(l, 24)
    assert w <= 1405, f"Overflow in CNM: {l}"
print("  All 3 CNM lines fit in 1405px!")

# 10. Footer box (default subnet...):
# x=40..760 (w=720), y=960..1060 (h=100)
# Icon at x=55, y=980 (size 40x40)
# Text at x=105, inner max = 760 - 105 - 16 = 639px.
footer_lines = [
    "default subnet 172.17.0.0/16 may overlap",
    "corporate or VPN ranges: set",
    "default-address-pools in",
    "/etc/docker/daemon.json"
]
print("\nFooter lines:")
for l in footer_lines:
    w = w_sans(l, 24)
    assert w <= 639, f"Overflow in Footer: {l}"
print("  All 4 Footer lines fit in 639px!")

# 11. Inspect commands box:
# x=800..1560 (w=760), y=960..1060 (h=100)
# Icon at x=820, y=980 (size 40x40)
# Text at x=870, inner max = 1560 - 870 - 16 = 674px.
cmd_lines = [
    "docker network ls; docker network inspect",
    "bridge; iptables -t nat -S DOCKER; bridge",
    "fdb show br docker0"
]
print("\nInspect command lines:")
for l in cmd_lines:
    w = w_mono(l, 24)
    assert w <= 674, f"Overflow in Commands: {l}"
print("  All 3 Command lines fit in 674px!")

# 12. Bottom takeaway bar:
# x=40..1560 (w=1520), y=1100..1160 (h=60)
# Text: "Docker inserts its own rules ahead of the firewall's rules" (26px bold white)
tw_w = w_sans("Docker inserts its own rules ahead of the firewall's rules", 26)
print(f"\nTakeaway: w={tw_w:.1f}px <= 1520px")
