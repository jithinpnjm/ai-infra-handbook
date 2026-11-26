import xml.etree.ElementTree as ET
import re

labels = [
    "Golden signals drawn from RED and USE",
    "Golden signals",
    "RED: service health (user view)",
    "Latency (duration, use percentiles)",
    "Traffic (request rate)",
    "Errors (request errors)",
    "USE: machine health (host view)",
    "Saturation (USE)",
    "Utilisation and errors also live here",
    "Netflix example: saturation approximated by the gap between p99 latency and the average",
    "RED judges the service, USE judges the host."
]

print("Total labels:", len(labels))
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. {l} (len={len(l)})")
