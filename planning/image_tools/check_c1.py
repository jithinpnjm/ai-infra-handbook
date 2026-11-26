import re
import xml.etree.ElementTree as ET

def est_width(txt, fs=24, is_mono=False):
    coeff = 0.62 if is_mono else 0.6
    return len(txt) * fs * coeff

print("=== CHECKING ALL TEXT WRAPS AND FITS ===")

# Proposed Layout:
# Canvas: 1600 x 1150
# Title at y = 65, 48px bold
#
# ROW 1 (y = 110 to 450, h = 340):
#   Card 1: x = 50, y = 110, w = 730, h = 340
#   Card 2: x = 820, y = 110, w = 730, h = 340
# Gap = 40px
#
# ROW 2 (y = 490 to 810, h = 320):
#   Card 3: x = 50, y = 490, w = 730, h = 320
#   Card 4: x = 820, y = 490, w = 730, h = 320
# Gap = 40px
#
# ROW 3: dnsConfig example (y = 850 to 965, h = 115)
#   Box: x = 50, y = 850, w = 1500, h = 115
# Gap = 30px (or 40px)
#
# ROW 4: Callout (y = 995 to 1100, h = 105)
#   Box: x = 50, y = 995, w = 1500, h = 105
# Canvas bottom margin = 1150 - 1100 = 50px (>= 40px).

# Let's verify clearances and paddings for all text elements:
# Card 1 text:
# Title at 30px bold: beside icon or below icon?
# If icon is at (x=75, y=130, w=56, h=56):
# If title is at x=150, y=168:
# "ClusterFirst (the real default):" -> width = 32 * 18 = 576.
# 150 + 576 = 726. Card ends at 780. Right padding = 780 - 726 = 54px >= 16px!
# Description lines below icon (y >= 130 + 56 + 24 = 210):
# y = 225: "nameserver is the kube-dns ClusterIP; search"
# y = 260: "ns.svc.domain svc.domain domain plus node"
# y = 295: "search domains; options ndots:5; names outside"
# y = 330: "the cluster domain are forwarded upstream"
# y = 365: "by CoreDNS"
# Wait, Card 1 ends at 450. 365 + 24 = 389. Bottom padding = 450 - 389 = 61px >= 16px!

c1_lines = [
    ("ClusterFirst (the real default):", 30, 150, 780),
    ("nameserver is the kube-dns ClusterIP; search", 24, 75, 780),
    ("ns.svc.domain svc.domain domain plus node", 24, 75, 780),
    ("search domains; options ndots:5; names outside", 24, 75, 780),
    ("the cluster domain are forwarded upstream by", 24, 75, 780),
    ("CoreDNS", 24, 75, 780)
]

for txt, fs, x, box_right in c1_lines:
    w = est_width(txt, fs)
    right_edge = x + w
    pad = box_right - right_edge
    print(f"C1: w={w:5.1f}, right={right_edge:5.1f}, pad={pad:4.1f} | '{txt}'")
    assert pad >= 16, f"Padding violation: {txt}"

print("\nC1 PASS!")
