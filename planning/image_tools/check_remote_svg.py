import json
import xml.etree.ElementTree as ET

tree = ET.parse("../../docs/part-01-linux/img/l30-remote-display.svg")
root = tree.getroot()

texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    t = " ".join("".join(el.itertext()).split())
    texts.append((t, el.attrib.get('font-size')))

print(f"Total texts in l30-remote-display.svg: {len(texts)}")
for t, fs in texts:
    print(f"[{fs}px] '{t}'")

data = json.load(open("specs/v1_30.json"))
spec = data[2]['spec']
print("\nSpec:")
print(spec)
