import xml.etree.ElementTree as ET

tree = ET.parse("test_timeline.svg")
root = tree.getroot()

print("=== CHECKING MESSAGE RECT PADDINGS ===")

for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.attrib.get('id', '')
    if gid.startswith('step-') or gid == 'note-running':
        rect = g.find('{http://www.w3.org/2000/svg}rect')
        texts = list(g.iter('{http://www.w3.org/2000/svg}text'))
        # The message text is the last text in the group
        msg_text = texts[-1]
        rw = float(rect.attrib['width'])
        fs = float(msg_text.attrib['font-size'])
        tspans = list(msg_text.iter('{http://www.w3.org/2000/svg}tspan'))
        if tspans:
            for tsp in tspans:
                txt = tsp.text.strip()
                w = len(txt) * fs * 0.60
                pad = (rw - w) / 2
                assert pad >= 16.0, f"FAIL in {gid}: '{txt}' has pad {pad:.1f} < 16 in width {rw}"
                print(f"  [{gid:14s}] pad={pad:5.1f}px (w={w:5.1f}/{rw}px): '{txt}'")
        else:
            txt = "".join(msg_text.itertext()).strip()
            w = len(txt) * fs * 0.60
            pad = (rw - w) / 2
            assert pad >= 16.0, f"FAIL in {gid}: '{txt}' has pad {pad:.1f} < 16 in width {rw}"
            print(f"  [{gid:14s}] pad={pad:5.1f}px (w={w:5.1f}/{rw}px): '{txt}'")

print("\nALL MESSAGE RECTS PASSED STRICT PADDING CHECKS (pad >= 16px everywhere)!")
