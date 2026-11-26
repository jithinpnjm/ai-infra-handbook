import re

labels = {
    "title": "Which way to work: bottom-up, top-down, divide, follow, compare",
    "aid1": "Bottom-up: physical, link, network, transport, application; when many things fail at once or after a hardware change; physical problems are cheapest to rule out (a loose cable or dead optic shows in a light or counter)",
    "aid2": "Top-down: when only one application misbehaves",
    "aid3": "Divide and conquer (half-split): when the path is long",
    "aid4": "Follow the path: trace the actual flow end to end, including NAT, overlays and load balancers",
    "aid5": "Compare with a working peer: diff a good node against a bad one; check configs, firmware, ethtool, sysctls, routes and counters; configuration drift is the most common root cause in fleets",
    "aid6": "Change one thing at a time, and revert the experiments that fail",
    "aid7": "Use the packet: a capture beats opinion",
    "side": "Two engineers, same alert: one changes settings at once and the evidence is gone by the time the cause would have shown; the other writes down the symptom, saves the counters, and only then changes one thing",
    "bar": "Write the symptom in measurable terms before you touch a command"
}

# Rule checks:
# sans: 0.6 * font_size per char
# font_size = 24 -> char width = 14.4 px
# font_size = 28 -> char width = 16.8 px
# font_size = 30 -> char width = 18.0 px
# Box width = 740 px.
# Padding inside box: >= 16 px.
# With an icon on the left (say 56px wide, plus 20px margin = 76px from left):
# Or icon at top left, text beside or below.
# If icon is at (x + 24, y + 24), size 56x56:
# Text x can be x + 100, giving available text width = 740 - 100 - 24 = 616 px!
# 616 / 14.4 = 42.7 characters per line!

print("Available chars per line at 24px in 616px width: ~42 chars")
