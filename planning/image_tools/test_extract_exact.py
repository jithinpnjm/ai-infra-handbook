import xml.etree.ElementTree as ET
import re

xml_test = """<svg xmlns="http://www.w3.org/2000/svg"><text font-family="sans-serif" fill="#303a36"><tspan x="100" y="100" font-size="30" font-weight="bold" fill="#207448">Quantify: </tspan><tspan font-size="24">throughput, latency percentiles, </tspan><tspan x="100" dy="32" font-size="24">retransmit rate, against baseline and line rate or BDP</tspan></text></svg>"""

root = ET.fromstring(xml_test)
text_elem = root.find("{http://www.w3.org/2000/svg}text")
joined = "".join(text_elem.itertext()).strip()
print("Joined:", repr(joined))
assert joined == "Quantify: throughput, latency percentiles, retransmit rate, against baseline and line rate or BDP"
print("MATCHES EXACTLY without regex!")
norm_joined = re.sub(r'\s+', ' ', "".join(text_elem.itertext()).strip())
assert norm_joined == "Quantify: throughput, latency percentiles, retransmit rate, against baseline and line rate or BDP"
print("MATCHES EXACTLY with regex!")
