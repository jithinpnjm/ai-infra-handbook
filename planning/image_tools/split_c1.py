def measure_line(segments):
    total = 0
    for text, is_mono, fs in segments:
        cw = (0.62 if is_mono else 0.6) * fs
        total += len(text) * cw
    return total

lines_c1 = [
    [("Collect as you go:", False, 30)],  # Title
    [("incident log with UTC timeline, ", False, 24)],
    [("observations, commands run, changes made, ", False, 24)],
    [("who did what; exact error strings; ", False, 24)],
    [("kubectl get -o yaml", True, 24), (" snapshots, ", False, 24)],
    [("describe", True, 24), (" output, pod logs including ", False, 24), ("--previous", True, 24), (", ", False, 24)],
    [("node journals, ", False, 24), ("dmesg", True, 24), (", ", False, 24), ("pcaps", True, 24), (", ", False, 24)],
    [("metric screenshots with time ranges, ", False, 24)],
    [("nvidia-bug-report", True, 24), (", ", False, 24), ("Hubble", True, 24), (" flows, ", False, 24)],
    [("audit log excerpts; for support ", False, 24)],
    [("kubectl cluster-info dump", True, 24), (", ", False, 24), ("sosreport", True, 24), (", ", False, 24)],
    [("vendor bundles", False, 24)]
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
print("Card 1: ALL LINES <= 620px! (PASS)")
