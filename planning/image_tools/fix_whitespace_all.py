import re
import xml.etree.ElementTree as ET

q1 = 'Collect as you go: incident log with UTC timeline, observations, commands run, changes made, who did what; exact error strings; kubectl get -o yaml snapshots, describe output, pod logs including --previous, node journals, dmesg, pcaps, metric screenshots with time ranges, nvidia-bug-report, Hubble flows, audit log excerpts; for support kubectl cluster-info dump, sosreport, vendor bundles'
q2 = 'Communicate: status updates at fixed intervals, state the impact clearly, give an ETA only when you have a basis for it'
q3 = 'Blameless review: timeline, contributing factors (not one single root cause), detection gaps, how well the mitigation worked, action items with owners for automation, alerts, guardrails, docs and tests; turn recurring manual diagnosis into automated checks'
q4 = 'game day: planned drill with a fault the team has not seen; measure time-to-detect and time-to-recover; tools tc netem, Chaos Mesh NetworkChaos, kill pods and nodes, fill disks, stop kubelet, break CNI'

c2_xml = """<text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1000" y="168" font-size="30" font-weight="bold" fill="#207448">Communicate: </tspan>
      <tspan x="875" y="245">status updates at fixed intervals, </tspan>
      <tspan x="875" dy="45">state the impact clearly, </tspan>
      <tspan x="875" dy="45">give an ETA only when you </tspan>
      <tspan x="875" dy="45">have a basis for it</tspan>
    </text>"""

c3_xml = """<text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1000" y="718" font-size="30" font-weight="bold" fill="#207448">Blameless review: </tspan>
      <tspan x="875" y="775">timeline, contributing factors </tspan>
      <tspan x="875" dy="38">(not one single root cause), </tspan>
      <tspan x="875" dy="38">detection gaps, how well </tspan>
      <tspan x="875" dy="38">the mitigation worked, </tspan>
      <tspan x="875" dy="38">action items with owners for </tspan>
      <tspan x="875" dy="38">automation, alerts, guardrails, </tspan>
      <tspan x="875" dy="38">docs and tests; turn recurring </tspan>
      <tspan x="875" dy="38">manual diagnosis into automated checks</tspan>
    </text>"""

c4_xml = """<text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="155" y="718" font-size="30" font-weight="bold" fill="#207448">game day: </tspan>
      <tspan x="85" y="785">planned drill with a fault the team </tspan>
      <tspan x="85" dy="42">has not seen; measure time-to-detect </tspan>
      <tspan x="85" dy="42">and time-to-recover; tools <tspan font-family="monospace">tc netem</tspan>, </tspan>
      <tspan x="85" dy="42"><tspan font-family="monospace">Chaos Mesh NetworkChaos</tspan>, </tspan>
      <tspan x="85" dy="42">kill pods and nodes, fill disks, </tspan>
      <tspan x="85" dy="42">stop <tspan font-family="monospace">kubelet</tspan>, break CNI</tspan>
    </text>"""

for name, xml, exp in [('Card 2', c2_xml, q2), ('Card 3', c3_xml, q3), ('Card 4', c4_xml, q4)]:
    elem = ET.fromstring(xml)
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    match = (full_text == exp)
    print(f"{name} match:", match)
    if not match:
        print("Diff:\nExp:", repr(exp), "\nGot:", repr(full_text))

