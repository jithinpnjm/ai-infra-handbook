import re

spec = """A table of generic aids, each with when to use it. 'Bottom-up: physical, link, network, transport, application; when many things fail at once or after a hardware change; physical problems are cheapest to rule out (a loose cable or dead optic shows in a light or counter)'. 'Top-down: when only one application misbehaves'. 'Divide and conquer (half-split): when the path is long'. 'Follow the path: trace the actual flow end to end, including NAT, overlays and load balancers'. 'Compare with a working peer: diff a good node against a bad one; check configs, firmware, ethtool, sysctls, routes and counters; configuration drift is the most common root cause in fleets' (orange). 'Change one thing at a time, and revert the experiments that fail'. 'Use the packet: a capture beats opinion'. Side contrast 'Two engineers, same alert: one changes settings at once and the evidence is gone by the time the cause would have shown; the other writes down the symptom, saves the counters, and only then changes one thing'. Bottom bar: 'Write the symptom in measurable terms before you touch a command'."""

quotes = re.findall(r"'([^']+)'", spec)
print(f"Quotes count: {len(quotes)}")
for i, q in enumerate(quotes):
    print(f"{i+1}: {q} (len: {len(q)})")
