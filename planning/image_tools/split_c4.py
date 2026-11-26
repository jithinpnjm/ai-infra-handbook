def measure_line(segments):
    total = 0
    for text, is_mono, fs in segments:
        cw = (0.62 if is_mono else 0.6) * fs
        total += len(text) * cw
    return total

tokens_c4 = [
    [("planned drill with a fault the team ", False, 24)],
    [("has not seen; measure time-to-detect ", False, 24)],
    [("and time-to-recover; tools ", False, 24), ("tc netem", True, 24), (", ", False, 24)],
    [("Chaos Mesh NetworkChaos", True, 24), (", ", False, 24)],
    [("kill pods and nodes, fill disks, ", False, 24)],
    [("stop ", False, 24), ("kubelet", True, 24), (", break CNI", False, 24)]
]

print("=== Card 4 Lines ===")
for i, l in enumerate(tokens_c4):
    w = measure_line(l)
    t = "".join(x[0] for x in l)
    print(f"Line {i:2d}: w={w:5.1f}px | '{t}'")
    assert w <= 580

exp_c4 = 'game day: planned drill with a fault the team has not seen; measure time-to-detect and time-to-recover; tools tc netem, Chaos Mesh NetworkChaos, kill pods and nodes, fill disks, stop kubelet, break CNI'
full = "game day: " + "".join("".join(x[0] for x in l) for l in tokens_c4)
full = " ".join(full.split())
print("Match:", full == exp_c4)
if full != exp_c4:
    print("Diff:\nExp:", exp_c4, "\nGot:", full)
