#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import glob

for f in sorted(glob.glob("planning/image_tools/*.svg")):
    try:
        tree = ET.parse(f)
        root = tree.getroot()
        texts = root.findall(".//{http://www.w3.org/2000/svg}text")
        sizes = [t.attrib.get('font-size') for t in texts if t.attrib.get('font-size')]
        # print title and font sizes
        title = root.find("{http://www.w3.org/2000/svg}title")
        t_str = title.text if title is not None else ""
        if "table" in f or "troubleshoot" in f or "golden" in f or "signals" in f or "ladder" in f:
            print(f"{f}: title='{t_str[:40]}' sizes={sorted(set(sizes))}")
    except Exception as e:
        pass
