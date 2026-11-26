import re

def est_w(text, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(text) * fs * rate

# Left box: x=40, y=140, w=480, h=440
# Middle arrow zone: x=540..1060 (w=520)
# Right box: x=1080, y=140, w=480, h=440

# In Left box:
# Card 1: site.fact (x=60, y=160, w=440, h=160)
lines_site = [
    ("site.fact (INI):", 24, False),
    ("[location] rack=r07, rail=3", 24, True)
]
print("=== LEFT BOX: site.fact ===")
for txt, fs, mono in lines_site:
    w = est_w(txt, fs, mono)
    pad = (440 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 440={pad:.1f}")
    assert pad >= 16

# Card 2: gpu.fact (x=60, y=340, w=440, h=220)
lines_gpu = [
    ("gpu.fact (executable, mode 0755):", 24, False),
    ("#!/bin/sh;", 24, True),
    ("n=$(nvidia-smi -L 2>/dev/null", 24, True),
    ("| wc -l); echo {\"count\": $n}", 24, True)
]
print("\n=== LEFT BOX: gpu.fact ===")
for txt, fs, mono in lines_gpu:
    w = est_w(txt, fs, mono)
    pad = (440 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 440={pad:.1f}")
    assert pad >= 16

# Middle arrow text: x=550..1050 (w=500)
lines_arrow = [
    ("placed in /etc/ansible/facts.d/", 24, True),
    ("on the target; any .fact file,", 24, False),
    ("or any executable, is picked up", 24, False),
    ("during fact gathering; INI or JSON,", 24, False),
    ("or an executable printing JSON", 24, False)
]
print("\n=== MIDDLE: Arrow Text ===")
for txt, fs, mono in lines_arrow:
    w = est_w(txt, fs, mono)
    pad = (500 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 500={pad:.1f}")
    assert pad >= 16

# Right box: x=1080, y=140, w=480, h=440
# Header: ansible_local.<name>
# Card 1: ansible_local.location.rack
# Card 2: ansible_local.gpu.count
lines_right = [
    ("ansible_local.<name>", 28, True),
    ("ansible_local.location.rack", 24, True),
    ("ansible_local.gpu.count", 24, True)
]
print("\n=== RIGHT BOX ===")
for txt, fs, mono in lines_right:
    w = est_w(txt, fs, mono)
    pad = (440 - w) / 2
    print(f"'{txt}': w={w:.1f}, pad in 440={pad:.1f}")
    assert pad >= 16

print("\nALL FLOW PADDINGS PASS >= 16px STRICTLY!")
