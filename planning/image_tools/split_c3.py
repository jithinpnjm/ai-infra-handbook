def measure_line(segments):
    total = 0
    for text, is_mono, fs in segments:
        cw = (0.62 if is_mono else 0.6) * fs
        total += len(text) * cw
    return total

tokens_c3 = [
    "timeline, contributing factors ",
    "(not one single root cause), ",
    "detection gaps, how well ",
    "the mitigation worked, ",
    "action items with owners for ",
    "automation, alerts, guardrails, ",
    "docs and tests; turn recurring ",
    "manual diagnosis into automated checks"
]

lines = []
cur = ""
for tok in tokens_c3:
    if len(cur + tok) * 14.4 <= 580:
        cur += tok
    else:
        if cur:
            lines.append(cur)
        cur = tok
if cur:
    lines.append(cur)

for i, l in enumerate(lines):
    w = len(l) * 14.4
    print(f"Line {i:2d}: w={w:5.1f}px | '{l}'")
    assert w <= 580

exp_c3 = 'Blameless review: timeline, contributing factors (not one single root cause), detection gaps, how well the mitigation worked, action items with owners for automation, alerts, guardrails, docs and tests; turn recurring manual diagnosis into automated checks'
full = "Blameless review: " + "".join(lines)
full = " ".join(full.split())
print("Match:", full == exp_c3)
if full != exp_c3:
    print("Diff:\nExp:", exp_c3, "\nGot:", full)
