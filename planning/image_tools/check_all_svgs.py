import json, glob, xml.etree.ElementTree as ET, re

# Check a few svgs against specs
for svg_path in glob.glob("*.svg"):
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        title_el = root.find('{http://www.w3.org/2000/svg}title')
        if title_el is not None and title_el.text:
            title = title_el.text.strip()
            # print title and number of text elements
            texts = []
            for t in root.iter('{http://www.w3.org/2000/svg}text'):
                txt = " ".join("".join(t.itertext()).split())
                texts.append(txt)
            print(f"{svg_path} | Title: '{title}' | {len(texts)} text elements")
    except Exception as e:
        pass
