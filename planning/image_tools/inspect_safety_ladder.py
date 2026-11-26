#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("../../docs/part-04-automation/img/p4-0409-safety-run-ladder.svg")
root = tree.getroot()
for i, el in enumerate(root.iter('{http://www.w3.org/2000/svg}text'), 1):
    txt = re.sub(r'\s+', ' ', "".join(el.itertext()).strip())
    fs = el.attrib.get('font-size', '')
    print(f"{i:2d}. [{fs}px] '{txt}'")
