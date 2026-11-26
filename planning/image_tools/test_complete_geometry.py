import re

# Geometry definitions
W = 1600
H = 1080

X_LEFT = 40
W_COL = 740
X_RIGHT = 820

Y_ROW1 = 150
H_ROW1 = 380

Y_ROW2 = 570
H_ROW2 = 360

Y_BAR = 970
H_BAR = 70
W_BAR = 1520

# Titles / lines
title_lines = [
    "The GPU count probe, ",
    "and the pipe that hides a failure"
]

lines1 = [
    "Count visible GPUs:",
    "shell nvidia-smi -L | wc -l,",
    "args executable /bin/bash,",
    "register gpu_count,",
    "changed_when false (read-only, never changed),",
    "failed_when gpu_count.rc != 0 or",
    "(gpu_count.stdout | int) != expected_gpus,",
    "check_mode false (run even under --check,",
    "safe because read-only)"
]

lines2 = [
    "Ansible starts /bin/bash, which runs",
    "nvidia-smi -L and pipes the listing into",
    "wc -l; the count comes back as text in",
    "gpu_count.stdout; failed_when converts",
    "it with int and compares with the expected",
    "count; a node showing seven GPUs when eight",
    "are expected fails the task at once and",
    "the message names the task"
]

lines3 = [
    "nvidia-smi fails with an error while wc",
    "succeeds on empty output: the pipeline",
    "reports success and the playbook believes",
    "the node has no GPUs and moves on"
]

lines4 = [
    "set -o pipefail works only in bash, so the",
    "probe needs executable /bin/bash and",
    "set -o pipefail; if that gets fragile keep",
    "the probe simple or split it into a module",
    "call plus Jinja filters"
]

line5 = "A pipe takes the exit code of its last command"

# Check Title
print("=== Checking Title ===")
for i, tl in enumerate(title_lines):
    w = len(tl) * 0.60 * 48
    pl = 800 - w / 2
    pr = 1600 - (800 + w / 2)
    print(f"Title L{i+1}: w={w:.1f}px, pl={pl:.1f}, pr={pr:.1f}")
    assert pl >= 40 and pr >= 40

# Check Card 1 (Top Left)
print("\n=== Checking Card 1 ===")
start_x1 = X_LEFT + 30
cur_y1 = Y_ROW1 + 52
for i, l in enumerate(lines1):
    fs = 30 if i == 0 else 24
    ft = 'sans' if i == 0 else 'mono' # conservative
    cw = 0.62 * fs if ft == 'mono' else 0.60 * fs
    w = len(l) * cw
    pl = start_x1 - X_LEFT
    pr = (X_LEFT + W_COL) - (start_x1 + w)
    pb = (Y_ROW1 + H_ROW1) - cur_y1
    print(f"Card 1 L{i+1} [{fs}px]: w={w:.1f}px, pl={pl:.1f}, pr={pr:.1f}, pb={pb:.1f}")
    assert pl >= 16, f"pl {pl} < 16"
    assert pr >= 16, f"pr {pr} < 16 on line {i+1}: {l}"
    assert pb >= 16, f"pb {pb} < 16"
    cur_y1 += 42 if i == 0 else 36

# Check Card 2 (Bottom Left)
print("\n=== Checking Card 2 ===")
start_x2 = X_LEFT + 30
cur_y2 = Y_ROW2 + 52
for i, l in enumerate(lines2):
    fs = 24
    cw = 0.60 * fs # sans
    w = len(l) * cw
    pl = start_x2 - X_LEFT
    pr = (X_LEFT + W_COL) - (start_x2 + w)
    pb = (Y_ROW2 + H_ROW2) - cur_y2
    print(f"Card 2 L{i+1} [{fs}px]: w={w:.1f}px, pl={pl:.1f}, pr={pr:.1f}, pb={pb:.1f}")
    assert pl >= 16, f"pl {pl} < 16"
    assert pr >= 16, f"pr {pr} < 16 on line {i+1}: {l}"
    assert pb >= 16, f"pb {pb} < 16"
    cur_y2 += 38

# Check Card 3 (Top Right)
print("\n=== Checking Card 3 ===")
start_x3 = X_RIGHT + 30
cur_y3 = Y_ROW1 + 65
for i, l in enumerate(lines3):
    fs = 24
    cw = 0.60 * fs
    w = len(l) * cw
    pl = start_x3 - X_RIGHT
    pr = (X_RIGHT + W_COL) - (start_x3 + w)
    pb = (Y_ROW1 + H_ROW1) - cur_y3
    print(f"Card 3 L{i+1} [{fs}px]: w={w:.1f}px, pl={pl:.1f}, pr={pr:.1f}, pb={pb:.1f}")
    assert pl >= 16, f"pl {pl} < 16"
    assert pr >= 16, f"pr {pr} < 16 on line {i+1}: {l}"
    assert pb >= 16, f"pb {pb} < 16"
    cur_y3 += 42

# Check Card 4 (Bottom Right)
print("\n=== Checking Card 4 ===")
start_x4 = X_RIGHT + 30
cur_y4 = Y_ROW2 + 65
for i, l in enumerate(lines4):
    fs = 24
    cw = 0.60 * fs
    w = len(l) * cw
    pl = start_x4 - X_RIGHT
    pr = (X_RIGHT + W_COL) - (start_x4 + w)
    pb = (Y_ROW2 + H_ROW2) - cur_y4
    print(f"Card 4 L{i+1} [{fs}px]: w={w:.1f}px, pl={pl:.1f}, pr={pr:.1f}, pb={pb:.1f}")
    assert pl >= 16, f"pl {pl} < 16"
    assert pr >= 16, f"pr {pr} < 16 on line {i+1}: {l}"
    assert pb >= 16, f"pb {pb} < 16"
    cur_y4 += 42

# Check Bottom Bar
print("\n=== Checking Bottom Bar ===")
w5 = len(line5) * 0.60 * 30
pl5 = 800 - w5 / 2 - X_LEFT
pr5 = (X_LEFT + W_BAR) - (800 + w5 / 2)
pb5 = (Y_BAR + H_BAR) - (Y_BAR + 44)
print(f"Bottom bar [30px]: w={w5:.1f}px, pl={pl5:.1f}, pr={pr5:.1f}, pb={pb5:.1f}")
assert pl5 >= 16 and pr5 >= 16 and pb5 >= 16

print("\nALL PADDING CHECKS PASSED PERFECTLY!")
