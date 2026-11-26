def est_w(text, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(text) * fs * rate

# In Top-to-Bottom flow:
# Top Section: Two files on target (y=140..340, w=1520)
# Card 1 (Left): site.fact (x=50, y=160, w=680, h=160)
lines_site = [
    ("site.fact (INI):", 26, False),
    ("[location] rack=r07, rail=3", 24, True)
]
print("=== SITE.FACT ===")
for txt, fs, mono in lines_site:
    w = est_w(txt, fs, mono)
    pad = (680 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 680={pad:.1f}")
    assert pad >= 16

# Card 2 (Right): gpu.fact (x=770, y=160, w=790, h=160)
lines_gpu = [
    ("gpu.fact (executable, mode 0755):", 26, False),
    ("#!/bin/sh; n=$(nvidia-smi -L 2>/dev/null | wc -l);", 24, True),
    ("echo {\"count\": $n}", 24, True)
]
print("\n=== GPU.FACT ===")
for txt, fs, mono in lines_gpu:
    w = est_w(txt, fs, mono)
    pad = (790 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 790={pad:.1f}")
    assert pad >= 16

# Arrow & Label (y=360..450):
# Label in a card or strip across x=180..1550 (w=1370)
# Arrow on the left (x=100) pointing down from y=340 to y=470
lines_arrow = [
    ("placed in /etc/ansible/facts.d/ on the target; any .fact file, or any executable,", 24, False),
    ("is picked up during fact gathering; INI or JSON, or an executable printing JSON", 24, False)
]
print("\n=== ARROW LABEL ===")
for txt, fs, mono in lines_arrow:
    w = est_w(txt, fs, mono)
    pad = (1370 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 1370={pad:.1f}")
    assert pad >= 16

# Section 2: ansible_local.<name> (y=470..610, w=1520)
# Title / header: ansible_local.<name> (fs=28)
# Left badge: ansible_local.location.rack (w=700)
# Right badge: ansible_local.gpu.count (w=700)
lines_dest = [
    ("ansible_local.<name>", 28, True),
    ("ansible_local.location.rack", 24, True),
    ("ansible_local.gpu.count", 24, True)
]
print("\n=== ANSIBLE_LOCAL ===")
w_hdr = est_w(lines_dest[0][0], 28, True)
pad_hdr = (1520 - w_hdr) / 2
print(f"'{lines_dest[0][0]}': w={w_hdr:.1f}, pad in 1520={pad_hdr:.1f}")
assert pad_hdr >= 16

w_rack = est_w(lines_dest[1][0], 24, True)
pad_rack = (700 - w_rack) / 2
print(f"'{lines_dest[1][0]}': w={w_rack:.1f}, pad in 700={pad_rack:.1f}")
assert pad_rack >= 16

w_gpu = est_w(lines_dest[2][0], 24, True)
pad_gpu = (700 - w_gpu) / 2
print(f"'{lines_dest[2][0]}': w={w_gpu:.1f}, pad in 700={pad_gpu:.1f}")
assert pad_gpu >= 16

# Task strip (y=630..730, w=1520)
lines_task = [
    ("copy writes gpu.fact; setup with filter ansible_local re-reads it;", 24, False),
    ("debug msg: {{ ansible_local.gpu.count }} GPUs on {{ inventory_hostname }}", 24, True)
]
print("\n=== TASK STRIP ===")
for txt, fs, mono in lines_task:
    w = est_w(txt, fs, mono)
    pad = (1520 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 1520={pad:.1f}")
    assert pad >= 16

# Callouts (3 side-by-side boxes at y=750..1050, each w=480, gaps=40)
# Box 1 (x=40..520, w=480) - ORANGE
# Box 2 (x=560..1040, w=480)
# Box 3 (x=1080..1560, w=480)
callout1_lines = [
    ("the script runs on the target,", 24, False),
    ("so it always counts the GPUs", 24, False),
    ("actually present, even if the", 24, False),
    ("inventory was written before", 24, False),
    ("a card was replaced", 24, False)
]
callout2_lines = [
    ("the node carries its own label,", 24, False),
    ("so the playbook does not need", 24, False),
    ("a separate spreadsheet that", 24, False),
    ("might be out of date", 24, False)
]
callout3_lines = [
    ("attributes stay with the host", 24, False),
    ("and do not depend on the", 24, False),
    ("control node", 24, False)
]
print("\n=== CALLOUT 1 (ORANGE) ===")
for txt, fs, mono in callout1_lines:
    w = est_w(txt, fs, mono)
    pad = (480 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 480={pad:.1f}")
    assert pad >= 16

print("\n=== CALLOUT 2 ===")
for txt, fs, mono in callout2_lines:
    w = est_w(txt, fs, mono)
    pad = (480 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 480={pad:.1f}")
    assert pad >= 16

print("\n=== CALLOUT 3 ===")
for txt, fs, mono in callout3_lines:
    w = est_w(txt, fs, mono)
    pad = (480 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 480={pad:.1f}")
    assert pad >= 16

# Bottom bar (y=1080..1140, w=1520)
bbar_text = "The supported way for a host to declare its own attributes"
w_bbar = est_w(bbar_text, 26, False)
pad_bbar = (1520 - w_bbar) / 2
print(f"\n=== BOTTOM BAR ===")
print(f"'{bbar_text}': w={w_bbar:.1f}, pad in 1520={pad_bbar:.1f}")
assert pad_bbar >= 16

print("\nEVERY SINGLE ELEMENT PASSES WITH FLYING COLORS!")
