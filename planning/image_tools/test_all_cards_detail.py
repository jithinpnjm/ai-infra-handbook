import xml.etree.ElementTree as ET
import re

lines_c2 = [
    '<tspan x="1000" y="168" font-size="30" font-weight="bold" fill="#207448">Communicate: </tspan>',
    '<tspan x="875" y="245">status updates at fixed intervals, </tspan>',
    '<tspan x="875" dy="45">state the impact clearly, </tspan>',
    '<tspan x="875" dy="45">give an ETA only when you </tspan>',
    '<tspan x="875" dy="45">have a basis for it</tspan>'
]

lines_c3 = [
    '<tspan x="1000" y="718" font-size="30" font-weight="bold" fill="#207448">Blameless review: </tspan>',
    '<tspan x="875" y="775">timeline, contributing factors </tspan>',
    '<tspan x="875" dy="38">(not one single root cause), </tspan>',
    '<tspan x="875" dy="38">detection gaps, how well </tspan>',
    '<tspan x="875" dy="38">the mitigation worked, </tspan>',
    '<tspan x="875" dy="38">action items with owners for </tspan>',
    '<tspan x="875" dy="38">automation, alerts, guardrails, </tspan>',
    '<tspan x="875" dy="38">docs and tests; turn recurring </tspan>',
    '<tspan x="875" dy="38">manual diagnosis into automated checks</tspan>'
]

lines_c4 = [
    '<tspan x="155" y="718" font-size="30" font-weight="bold" fill="#207448">game day: </tspan>',
    '<tspan x="85" y="785">planned drill with a fault the team </tspan>',
    '<tspan x="85" dy="42">has not seen; measure time-to-detect </tspan>',
    '<tspan x="85" dy="42">and time-to-recover; tools <tspan font-family="monospace">tc netem</tspan>, </tspan>',
    '<tspan x="85" dy="42"><tspan font-family="monospace">Chaos Mesh NetworkChaos</tspan>, </tspan>',
    '<tspan x="85" dy="42">kill pods and nodes, fill disks, </tspan>',
    '<tspan x="85" dy="42">stop <tspan font-family="monospace">kubelet</tspan>, break CNI</tspan>'
]

def get_w(node):
    tot = 0
    is_m = (node.attrib.get('font-family') == 'monospace')
    fs = float(node.attrib.get('font-size', 24))
    cw = (0.62 if is_m else 0.6) * fs
    if node.text:
        tot += len(node.text) * cw
    for ch in node:
        tot += get_w(ch)
        if ch.tail:
            tot += len(ch.tail) * cw
    return tot

for name, lines in [('Card 2', lines_c2), ('Card 3', lines_c3), ('Card 4', lines_c4)]:
    print(f"\n=== {name} ===")
    for i, l in enumerate(lines):
        el = ET.fromstring(l)
        w = get_w(el)
        txt = "".join(el.itertext()).strip()
        print(f"Line {i}: w={w:5.1f}px | '{txt}'")
        assert w <= 620, f"Too wide: {w}"

print("\nALL LINES ACROSS ALL CARDS ARE <= 620px!")
