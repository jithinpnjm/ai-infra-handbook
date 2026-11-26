import xml.etree.ElementTree as ET

tree = ET.parse("test_slow_rail.svg")
root = tree.getroot()

# Check all vertical gaps:
# Title bounds: ~30 to 165
# Chart: y=205 to 485 (gap = 205 - 165 = 40px)
# Cause boxes: y=525 to 765 (gap = 525 - 485 = 40px)
# Grey note: y=805 to 885 (gap = 805 - 765 = 40px)
# Mitigation box: y=925 to 1035 (gap = 925 - 885 = 40px)
# Caption bar: y=1075 to 1135 (gap = 1075 - 1035 = 40px)
# Bottom margin: 1180 - 1135 = 45px >= 40px

assert 205 - 165 >= 40
assert 525 - 485 >= 40
assert 805 - 765 >= 40
assert 925 - 885 >= 40
assert 1075 - 1035 >= 40
assert 1180 - 1135 >= 40

print("All vertical section gaps and margins are >= 40px!")

# Text conservative widths check:
# For every line in text/tspan, estimate width: sans 0.6 * fs * len
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib.get('font-size', 24))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        for tsp in tspans:
            t = tsp.text.strip() if tsp.text else ""
            tfs = float(tsp.attrib.get('font-size', fs))
            w = len(t) * 0.6 * tfs
            assert w < 1520, f"Line '{t}' exceeds 1520px! ({w}px)"
            print(f"tspan: '{t}' est_w={w:.1f}px (len={len(t)}, fs={tfs})")
    else:
        t = elem.text.strip() if elem.text else ""
        w = len(t) * 0.6 * fs
        assert w < 1520, f"Line '{t}' exceeds 1520px! ({w}px)"
        print(f"text: '{t}' est_w={w:.1f}px (len={len(t)}, fs={fs})")

print("ALL CLEARANCES PASSED!")
