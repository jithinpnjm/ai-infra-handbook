import xml.etree.ElementTree as ET
import re

s1 = '''<text>
  <tspan>sysctl net.netfilter.</tspan>
  <tspan>nf_conntrack_count</tspan>
</text>'''

s2 = '''<text><tspan>sysctl net.netfilter.</tspan><tspan>nf_conntrack_count</tspan></text>'''

print("s1:", repr(re.sub(r'\s+', ' ', "".join(ET.fromstring(s1).itertext()).strip())))
print("s2:", repr(re.sub(r'\s+', ' ', "".join(ET.fromstring(s2).itertext()).strip())))
