def measure_line(segments):
    total = 0
    for text, is_mono, fs in segments:
        cw = (0.62 if is_mono else 0.6) * fs
        total += len(text) * cw
    return total

# Card 1:
lines_c1 = [
    [("Collect as you go:", False, 30)],  # Title
    [("incident log with UTC timeline, ", False, 24)],
    [("observations, commands run, changes made, ", False, 24)],
    [("who did what; exact error strings; ", False, 24)],
    [("kubectl get -o yaml", True, 24), (" snapshots, ", False, 24), ("describe", True, 24), (" output, ", False, 24)],
    [("pod logs including ", False, 24), ("--previous", True, 24), (", node journals, ", False, 24)],
    [("dmesg", True, 24), (", ", False, 24), ("pcaps", True, 24), (", metric screenshots with time ranges, ", False, 24)],
    [("nvidia-bug-report", True, 24), (", ", False, 24), ("Hubble", True, 24), (" flows, audit log excerpts; ", False, 24)],
    [("for support ", False, 24), ("kubectl cluster-info dump", True, 24), (", ", False, 24)],
    [("sosreport", True, 24), (", vendor bundles", False, 24)]
]

print("=== Card 1 Lines ===")
for i, l in enumerate(lines_c1):
    w = measure_line(l)
    t = "".join(x[0] for x in l)
    print(f"Line {i:2d}: w={w:5.1f}px | '{t}'")
    assert w <= 620, f"Line {i} too wide: {w} > 620"

full_c1 = " ".join("".join(x[0] for x in l).strip() for l in lines_c1)
full_c1 = " ".join(full_c1.split())
exp_c1 = 'Collect as you go: incident log with UTC timeline, observations, commands run, changes made, who did what; exact error strings; kubectl get -o yaml snapshots, describe output, pod logs including --previous, node journals, dmesg, pcaps, metric screenshots with time ranges, nvidia-bug-report, Hubble flows, audit log excerpts; for support kubectl cluster-info dump, sosreport, vendor bundles'
assert full_c1 == exp_c1, f"Mismatch in Card 1!\nExp: {exp_c1}\nGot: {full_c1}"
print("Card 1: PASS!")

# Card 2:
# 'Communicate: status updates at fixed intervals, state the impact clearly, give an ETA only when you have a basis for it'
lines_c2 = [
    [("Communicate:", False, 30)],  # Title
    [("status updates at fixed intervals, ", False, 24)],
    [("state the impact clearly, give an ETA ", False, 24)],
    [("only when you have a basis for it", False, 24)]
]

print("\n=== Card 2 Lines ===")
for i, l in enumerate(lines_c2):
    w = measure_line(l)
    t = "".join(x[0] for x in l)
    print(f"Line {i:2d}: w={w:5.1f}px | '{t}'")
    assert w <= 620, f"Line {i} too wide: {w} > 620"

full_c2 = " ".join("".join(x[0] for x in l).strip() for l in lines_c2)
full_c2 = " ".join(full_c2.split())
exp_c2 = 'Communicate: status updates at fixed intervals, state the impact clearly, give an ETA only when you have a basis for it'
assert full_c2 == exp_c2, f"Mismatch in Card 2!\nExp: {exp_c2}\nGot: {full_c2}"
print("Card 2: PASS!")

# Card 3:
# 'Blameless review: timeline, contributing factors (not one single root cause), detection gaps, how well the mitigation worked, action items with owners for automation, alerts, guardrails, docs and tests; turn recurring manual diagnosis into automated checks'
lines_c3 = [
    [("Blameless review:", False, 30)],  # Title
    [("timeline, contributing factors ", False, 24)],
    [("(not one single root cause), detection gaps, ", False, 24)],
    [("how well the mitigation worked, action items ", False, 24)],
    [("with owners for automation, alerts, guardrails, ", False, 24)],
    [("docs and tests; turn recurring manual ", False, 24)],
    [("diagnosis into automated checks", False, 24)]
]

print("\n=== Card 3 Lines ===")
for i, l in enumerate(lines_c3):
    w = measure_line(l)
    t = "".join(x[0] for x in l)
    print(f"Line {i:2d}: w={w:5.1f}px | '{t}'")
    assert w <= 620, f"Line {i} too wide: {w} > 620"

full_c3 = " ".join("".join(x[0] for x in l).strip() for l in lines_c3)
full_c3 = " ".join(full_c3.split())
exp_c3 = 'Blameless review: timeline, contributing factors (not one single root cause), detection gaps, how well the mitigation worked, action items with owners for automation, alerts, guardrails, docs and tests; turn recurring manual diagnosis into automated checks'
assert full_c3 == exp_c3, f"Mismatch in Card 3!\nExp: {exp_c3}\nGot: {full_c3}"
print("Card 3: PASS!")

# Card 4:
# 'game day: planned drill with a fault the team has not seen; measure time-to-detect and time-to-recover; tools tc netem, Chaos Mesh NetworkChaos, kill pods and nodes, fill disks, stop kubelet, break CNI'
lines_c4 = [
    [("game day:", False, 30)],  # Title
    [("planned drill with a fault the team has not seen; ", False, 24)],
    [("measure time-to-detect and time-to-recover; ", False, 24)],
    [("tools ", False, 24), ("tc netem", True, 24), (", ", False, 24), ("Chaos Mesh NetworkChaos", True, 24), (", ", False, 24)],
    [("kill pods and nodes, fill disks, stop ", False, 24), ("kubelet", True, 24), (", ", False, 24)],
    [("break CNI", False, 24)]
]

print("\n=== Card 4 Lines ===")
for i, l in enumerate(lines_c4):
    w = measure_line(l)
    t = "".join(x[0] for x in l)
    print(f"Line {i:2d}: w={w:5.1f}px | '{t}'")
    assert w <= 620, f"Line {i} too wide: {w} > 620"

full_c4 = " ".join("".join(x[0] for x in l).strip() for l in lines_c4)
full_c4 = " ".join(full_c4.split())
exp_c4 = 'game day: planned drill with a fault the team has not seen; measure time-to-detect and time-to-recover; tools tc netem, Chaos Mesh NetworkChaos, kill pods and nodes, fill disks, stop kubelet, break CNI'
assert full_c4 == exp_c4, f"Mismatch in Card 4!\nExp: {exp_c4}\nGot: {full_c4}"
print("Card 4: PASS!")

