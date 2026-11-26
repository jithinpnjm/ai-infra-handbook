import re
import xml.etree.ElementTree as ET

# Labels
labels = [
    "Capacity forecast",
    "Canary rollout",
    "SLOs",
    "Burn-rate alerts",
    "Incident process",
    "Post-mortem",
    "Runbooks, automation"
]

print("Checking label lengths at font-size 30 bold:")
for l in labels:
    # check split options
    w = len(l) * 30 * 0.6
    print(f"  '{l}': full width ~{w:.1f}px")

