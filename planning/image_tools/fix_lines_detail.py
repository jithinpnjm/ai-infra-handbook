import xml.etree.ElementTree as ET
import re

# Let's inspect each line in Card 1:
# We want every line's estimated width to be <= 640px.
# Card 1 x from 50 to 760. Left pad = 85 - 50 = 35px. Right edge = 760.
# Max text width = 760 - 85 - 20 = 655px.
# So text width <= 620px ensures >= 55px right padding!

card1_lines = [
    # (xml_content)
]

lines_c1 = [
    '<tspan x="210" y="168" font-size="30" font-weight="bold" fill="#207448">Collect as you go: </tspan>',
    '<tspan x="85" y="225">incident log with UTC timeline, </tspan>',
    '<tspan x="85" dy="30">observations, commands run, </tspan>',
    '<tspan x="85" dy="30">changes made, who did what; </tspan>',
    '<tspan x="85" dy="30">exact error strings; </tspan>',
    '<tspan x="85" dy="30"><tspan font-family="monospace">kubectl get -o yaml</tspan> snapshots, </tspan>',
    '<tspan x="85" dy="30"><tspan font-family="monospace">describe</tspan> output, pod logs including </tspan>',
    '<tspan x="85" dy="30"><tspan font-family="monospace">--previous</tspan>, node journals, <tspan font-family="monospace">dmesg</tspan>, </tspan>',
    '<tspan x="85" dy="30"><tspan font-family="monospace">pcaps</tspan>, metric screenshots </tspan>',
    '<tspan x="85" dy="30">with time ranges, <tspan font-family="monospace">nvidia-bug-report</tspan>, </tspan>',
    '<tspan x="85" dy="30"><tspan font-family="monospace">Hubble</tspan> flows, audit log excerpts; </tspan>',
    '<tspan x="85" dy="30">for support <tspan font-family="monospace">kubectl cluster-info dump</tspan>, </tspan>',
    '<tspan x="85" dy="30"><tspan font-family="monospace">sosreport</tspan>, vendor bundles</tspan>'
]

text1_xml = '<text font-family="sans-serif" font-size="24" fill="#303a36">\n' + "\n".join(lines_c1) + "\n</text>"

q1 = 'Collect as you go: incident log with UTC timeline, observations, commands run, changes made, who did what; exact error strings; kubectl get -o yaml snapshots, describe output, pod logs including --previous, node journals, dmesg, pcaps, metric screenshots with time ranges, nvidia-bug-report, Hubble flows, audit log excerpts; for support kubectl cluster-info dump, sosreport, vendor bundles'

elem = ET.fromstring(text1_xml)
full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
print("Match:", full_text == q1)
if full_text != q1:
    print("Diff:\nExp:", repr(q1), "\nGot:", repr(full_text))

# Check widths of each line:
for i, l_xml in enumerate(lines_c1):
    el = ET.fromstring(l_xml)
    # calculate width
    w = 0
    # iterate text nodes
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
    w = get_w(el)
    txt = "".join(el.itertext()).strip()
    print(f"Line {i:2d}: w={w:5.1f}px | '{txt}'")
    assert w <= 620, f"Line {i} too wide: {w} > 620"

