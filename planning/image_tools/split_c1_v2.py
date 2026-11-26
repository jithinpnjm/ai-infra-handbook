def measure_line(segments):
    total = 0
    for text, is_mono, fs in segments:
        cw = (0.62 if is_mono else 0.6) * fs
        total += len(text) * cw
    return total

lines_c1 = [
    [("Collect as you go:", False, 30)],  # Title
    [("incident log with UTC timeline, observations, ", False, 24)], # wait, let's check
    [("commands run, changes made, who did what; ", False, 24)],
    [("exact error strings; ", False, 24), ("kubectl get -o yaml", True, 24), (" snapshots, ", False, 24)],
    [("describe", True, 24), (" output, pod logs including ", False, 24), ("--previous", True, 24), (", ", False, 24)],
]

# Let's write an automatic word wrapper that greedily packs lines <= 600px
exp_c1 = 'Collect as you go: incident log with UTC timeline, observations, commands run, changes made, who did what; exact error strings; kubectl get -o yaml snapshots, describe output, pod logs including --previous, node journals, dmesg, pcaps, metric screenshots with time ranges, nvidia-bug-report, Hubble flows, audit log excerpts; for support kubectl cluster-info dump, sosreport, vendor bundles'

mono_words = {
    'kubectl get -o yaml', 'describe', '--previous', 'dmesg', 'pcaps',
    'nvidia-bug-report', 'Hubble', 'kubectl cluster-info dump', 'sosreport'
}

# Tokens with punctuation
# Let's inspect tokens
tokens = [
    ("incident log with UTC timeline, ", False),
    ("observations, commands run, ", False),
    ("changes made, who did what; ", False),
    ("exact error strings; ", False),
    ("kubectl get -o yaml", True),
    (" snapshots, ", False),
    ("describe", True),
    (" output, ", False),
    ("pod logs including ", False),
    ("--previous", True),
    (", node journals, ", False),
    ("dmesg", True),
    (", ", False),
    ("pcaps", True),
    (", ", False),
    ("metric screenshots with time ranges, ", False),
    ("nvidia-bug-report", True),
    (", ", False),
    ("Hubble", True),
    (" flows, audit log excerpts; ", False),
    ("for support ", False),
    ("kubectl cluster-info dump", True),
    (", ", False),
    ("sosreport", True),
    (", vendor bundles", False)
]

# Let's greedily merge tokens into lines <= 600px
lines = []
cur_line = []
cur_w = 0
for tok, is_m in tokens:
    tok_w = len(tok) * (0.62 if is_m else 0.6) * 24
    if cur_w + tok_w <= 610:
        cur_line.append((tok, is_m, 24))
        cur_w += tok_w
    else:
        if cur_line:
            lines.append(cur_line)
        cur_line = [(tok, is_m, 24)]
        cur_w = tok_w
if cur_line:
    lines.append(cur_line)

for i, l in enumerate(lines):
    w = measure_line(l)
    t = "".join(x[0] for x in l)
    print(f"Line {i:2d}: w={w:5.1f}px | '{t}'")
    assert w <= 610, f"Line {i} too wide: {w} > 610"

full = "Collect as you go: " + "".join("".join(x[0] for x in l) for l in lines)
full = " ".join(full.split())
print("Match:", full == exp_c1)
if full != exp_c1:
    print("Diff:\nExp:", exp_c1, "\nGot:", full)
