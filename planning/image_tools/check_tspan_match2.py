#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# If no whitespace between </tspan> and <tspan>:
xml_str = """<text font-size="24"><tspan x="424" dy="0">nvidia-smi --query-gpu=index,name,</tspan><tspan x="424" dy="28">temperature.gpu,utilization.gpu,</tspan><tspan x="424" dy="28">memory.used,memory.total,power.draw,</tspan><tspan x="424" dy="28">ecc.errors.uncorrected.volatile.total </tspan><tspan x="424" dy="28">--format=csv,noheader,nounits: one CSV line </tspan><tspan x="424" dy="28">per GPU; nvidia-smi -q -x for XML</tspan></text>"""

elem = ET.fromstring(xml_str)
full_text = "".join(elem.itertext()).strip()
full_text = re.sub(r'\s+', ' ', full_text)
target_r1c2 = "nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,ecc.errors.uncorrected.volatile.total --format=csv,noheader,nounits: one CSV line per GPU; nvidia-smi -q -x for XML"
print("Match without whitespace between tags?", full_text == target_r1c2)
assert full_text == target_r1c2
