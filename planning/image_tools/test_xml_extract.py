import xml.etree.ElementTree as ET
import re

xml = '''<text font-size="24"><tspan x="100" dy="0">event Pulled in X, </tspan><tspan x="100" dy="30">kubelet_image_</tspan><tspan x="100" dy="30">pull_duration_</tspan><tspan x="100" dy="30">seconds, containerd logs</tspan></text>'''
elem = ET.fromstring(xml)
t = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
expected = "event Pulled in X, kubelet_image_pull_duration_seconds, containerd logs"
print("Extracted:", repr(t))
print("Expected: ", repr(expected))
print("Match?    ", t == expected)
