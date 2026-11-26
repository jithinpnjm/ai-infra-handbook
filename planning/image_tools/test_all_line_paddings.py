import xml.etree.ElementTree as ET

tree = ET.parse("test_lab_ladder.svg")
root = tree.getroot()

# Let's map each step text to its enclosing card rect
boxes = {
    "pre-step": (40, 74, 1520, 66),
    "group-1": (40, 152, 1520, 236),
    "step-1": (60, 208, 710, 164),
    "step-2": (830, 208, 710, 164),
    "group-2": (40, 400, 740, 725),
    "step-3": (60, 456, 700, 122),
    "step-4": (60, 590, 700, 122),
    "step-5": (60, 724, 700, 122),
    "step-6": (60, 858, 700, 122),
    "step-7": (60, 992, 700, 122),
    "group-3": (820, 400, 740, 725),
    "step-8": (840, 456, 700, 122),
    "step-9": (840, 590, 700, 122),
    "step-10": (840, 724, 700, 122),
    "step-11": (840, 858, 700, 122),
    "step-12": (840, 992, 700, 122),
    "bottom-bar": (40, 1138, 1520, 46)
}

# Audit each text element
# In SVG:
# <text font-family="..." font-size="24" fill="...">
#   <tspan x="..." y="..." ...>text</tspan>
# </text>

for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    # find parent or matching box
    parent_id = None
    # Let's see what text it contains
    raw_text = "".join(elem.itertext()).strip()
    if raw_text in [str(i) for i in range(1, 13)]:
        continue # number circle
    if "The twelve lab steps" in raw_text:
        continue # title
    
    b_key = None
    if "checks the byte-offset filters" in raw_text: b_key = "pre-step"
    elif "Read a healthy trace" in raw_text: b_key = "group-1"
    elif "1 Handshake" in raw_text: b_key = "step-1"
    elif "2 Filters" in raw_text: b_key = "step-2"
    elif "Inject a fault and compare" in raw_text: b_key = "group-2"
    elif "3 Retransmissions" in raw_text: b_key = "step-3"
    elif "4 MTU black hole" in raw_text: b_key = "step-4"
    elif "5 Zero window" in raw_text: b_key = "step-5"
    elif "6 TLS" in raw_text: b_key = "step-6"
    elif "7 Offload artefacts" in raw_text: b_key = "step-7"
    elif "Wider tools" in raw_text: b_key = "group-3"
    elif "8 Overlay" in raw_text: b_key = "step-8"
    elif "9 Ring buffer" in raw_text: b_key = "step-9"
    elif "10 BPF tools" in raw_text: b_key = "step-10"
    elif "11 Container capture" in raw_text: b_key = "step-11"
    elif "12 Clean up" in raw_text: b_key = "step-12"
    elif "The healthy trace from step 1" in raw_text: b_key = "bottom-bar"
    
    assert b_key is not None, f"Unknown box for text '{raw_text}'"
    bx, by, bw, bh = boxes[b_key]
    print(f"\nChecking text in box '{b_key}' (x={bx}, y={by}, w={bw}, h={bh}):")
    
    # Check tspans or text directly
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if not tspans:
        # direct text
        txt = elem.text.strip()
        fs = float(elem.attrib.get('font-size', 24))
        x = float(elem.attrib.get('x', bx))
        y = float(elem.attrib.get('y', by))
        anchor = elem.attrib.get('text-anchor', 'start')
        is_mono = elem.attrib.get('font-family') == 'monospace'
        w = len(txt) * (0.62 if is_mono else 0.6) * fs
        if anchor == 'middle':
            pad_left = (x - w/2) - bx
            pad_right = (bx + bw) - (x + w/2)
        else:
            pad_left = x - bx
            pad_right = (bx + bw) - (x + w)
        pad_top = y - 0.75 * fs - by
        pad_bot = (by + bh) - (y + 0.25 * fs)
        print(f"  Line: '{txt[:30]}...' -> pad_l={pad_left:.1f}, pad_r={pad_right:.1f}, pad_t={pad_top:.1f}, pad_b={pad_bot:.1f}")
        assert pad_left >= 16, f"pad_left {pad_left} < 16"
        assert pad_right >= 16, f"pad_right {pad_right} < 16"
        assert pad_top >= 16, f"pad_top {pad_top} < 16"
        assert pad_bot >= 16, f"pad_bot {pad_bot} < 16"
    else:
        for ts in tspans:
            # if ts has children tspans, handle them
            txt = "".join(ts.itertext()).strip()
            fs = float(ts.attrib.get('font-size', elem.attrib.get('font-size', 24)))
            x = ts.attrib.get('x')
            if x is None:
                continue # child tspan inside parent tspan
            x = float(x)
            y = float(ts.attrib.get('y', by + 30))
            is_mono = ts.attrib.get('font-family') == 'monospace' or elem.attrib.get('font-family') == 'monospace'
            w = len(txt) * (0.62 if is_mono else 0.6) * fs
            pad_left = x - bx
            pad_right = (bx + bw) - (x + w)
            pad_top = y - 0.75 * fs - by
            pad_bot = (by + bh) - (y + 0.25 * fs)
            print(f"  Line: '{txt[:30]}...' -> pad_l={pad_left:.1f}, pad_r={pad_right:.1f}, pad_t={pad_top:.1f}, pad_b={pad_bot:.1f}")
            assert pad_left >= 16, f"pad_left {pad_left:.1f} < 16 in {b_key}"
            assert pad_right >= 16, f"pad_right {pad_right:.1f} < 16 in {b_key}"
            assert pad_top >= 16, f"pad_top {pad_top:.1f} < 16 in {b_key}"
            assert pad_bot >= 16, f"pad_bot {pad_bot:.1f} < 16 in {b_key}"

print("\nEVERY SINGLE LINE HAS >= 16px PADDING ON ALL 4 SIDES!")
