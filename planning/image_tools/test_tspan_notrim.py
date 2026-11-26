#!/usr/bin/env python3
import xml.etree.ElementTree as ET

snippet = '<text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36"><tspan x="800" dy="0">Reading the sample trace </tspan><tspan x="800" dy="54">line by line as a conversation</tspan></text>'

elem = ET.fromstring(snippet)
res1 = "".join(elem.itertext()).strip()
print(f"res1: '{res1}'")
assert res1 == "Reading the sample trace line by line as a conversation"
print("MATCHES EXACTLY EVEN WITHOUT re.sub!")
