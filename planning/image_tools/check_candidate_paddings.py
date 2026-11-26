import xml.etree.ElementTree as ET

tree = ET.parse('candidate.svg')
root = tree.getroot()

# For each text element, let's inspect the coordinates of its tspans and calculate estimated text width and bounding boxes.
# Conservative formula: sans 0.6 * font_size * char_count.

# Cards mapping:
# Row 1 (Utilization): box x=60, y=135, w=680, h=240 -> x_max = 740, y_max = 375
# Row 2 (Saturation): box x=60, y=400, w=680, h=240 -> x_max = 740, y_max = 640
# Row 3 (Errors): box x=60, y=665, w=680, h=240 -> x_max = 740, y_max = 905
# PCIe Gen4: box x=820, y=135, w=720, h=170 -> x_max = 1540, y_max = 305
# PCIe Gen5: box x=820, y=320, w=720, h=175 -> x_max = 1540, y_max = 495
# Apply method: box x=820, y=552, w=720, h=210 -> x_max = 1540, y_max = 762
# Lab check: box x=820, y=812, w=720, h=100 -> x_max = 1540, y_max = 912
# Bottom bar: box x=40, y=960, w=1520, h=80 -> x_max = 1560, y_max = 1040

texts = root.findall('{http://www.w3.org/2000/svg}text')

for idx, t in enumerate(texts):
    full = "".join(t.itertext()).strip()
    tspans = t.findall('{http://www.w3.org/2000/svg}tspan')
    print(f"\nText {idx+1}: '{full[:40]}...'")
    if not tspans:
        # direct text
        x = float(t.get('x', 0))
        y = float(t.get('y', 0))
        fs = float(t.get('font-size', 24))
        w = len(full) * 0.6 * fs
        anchor = t.get('text-anchor', 'start')
        if anchor == 'middle':
            x_min = x - w / 2
            x_max = x + w / 2
        else:
            x_min = x
            x_max = x + w
        print(f"  Single line: x=[{x_min:.1f}, {x_max:.1f}], y={y}, fs={fs}")
    else:
        for tsp in tspans:
            line_str = tsp.text or ""
            x = float(tsp.get('x', t.get('x', 0)))
            y = float(tsp.get('y', t.get('y', 0)))
            fs = float(tsp.get('font-size', t.get('font-size', 24)))
            w = len(line_str) * 0.6 * fs
            anchor = tsp.get('text-anchor', t.get('text-anchor', 'start'))
            if anchor == 'middle':
                x_min = x - w / 2
                x_max = x + w / 2
            else:
                x_min = x
                x_max = x + w
            print(f"  Line ({fs:2.0f}px, {len(line_str):2d} chars): x=[{x_min:6.1f}, {x_max:6.1f}], y={y:5.1f} | '{line_str}'")

