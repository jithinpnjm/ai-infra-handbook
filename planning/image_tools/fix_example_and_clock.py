with open("generate_and_audit.py", "r") as f:
    code = f.read()

# Example pairing:
code = code.replace('y="772"', 'y="768"')
# Replace dy="34" in example pairing
code = code.replace("""    <text x="75" y="768" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="75" dy="0">the client capture shows a SYN-ACK arriving and the server capture shows</tspan>
      <tspan x="75" dy="34">the same SYN-ACK leaving with the same sequence numbers: the packet is gone</tspan>
      <tspan x="75" dy="34">between the two hosts, not inside the server; check route and NAT next</tspan>
    </text>""",
"""    <text x="75" y="768" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="75" dy="0">the client capture shows a SYN-ACK arriving and the server capture shows</tspan>
      <tspan x="75" dy="32">the same SYN-ACK leaving with the same sequence numbers: the packet is gone</tspan>
      <tspan x="75" dy="32">between the two hosts, not inside the server; check route and NAT next</tspan>
    </text>""")

# Clock note:
code = code.replace("""    <text x="145" y="918" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="145" dy="0">if the two captures disagree on order, check clocks first, then match</tspan>
      <tspan x="145" dy="34">by sequence number or IP ID, not by time; PTP with hardware timestamps</tspan>
      <tspan x="145" dy="34">is precise, NTP is good to about a millisecond; merge with <tspan font-family="monospace">mergecap -a</tspan></tspan>
    </text>""",
"""    <text x="145" y="914" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="145" dy="0">if the two captures disagree on order, check clocks first, then match</tspan>
      <tspan x="145" dy="32">by sequence number or IP ID, not by time; PTP with hardware timestamps</tspan>
      <tspan x="145" dy="32">is precise, NTP is good to about a millisecond; merge with <tspan font-family="monospace">mergecap -a</tspan></tspan>
    </text>""")

with open("generate_and_audit.py", "w") as f:
    f.write(code)

