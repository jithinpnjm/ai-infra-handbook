import xml.etree.ElementTree as ET
import re

xml1 = '''<text font-size="24">
  <tspan x="100" dy="0">kubelet_run_podsandbox_</tspan>
  <tspan x="100" dy="28">duration_seconds</tspan>
</text>'''

elem1 = ET.fromstring(xml1)
t1 = re.sub(r'\s+', ' ', "".join(elem1.itertext()).strip())
print("xml1:", repr(t1))

xml2 = '''<text font-size="24"><tspan x="100" dy="0">kubelet_run_podsandbox_</tspan><tspan x="100" dy="28">duration_seconds</tspan></text>'''

elem2 = ET.fromstring(xml2)
t2 = re.sub(r'\s+', ' ', "".join(elem2.itertext()).strip())
print("xml2:", repr(t2))

xml3 = '''<text font-size="24"><tspan x="100" dy="0">kubelet_run_podsandbox_duration_seconds</tspan></text>'''
elem3 = ET.fromstring(xml3)
t3 = re.sub(r'\s+', ' ', "".join(elem3.itertext()).strip())
print("xml3:", repr(t3))
