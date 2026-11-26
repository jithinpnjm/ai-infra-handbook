def text_w(text, is_mono=False, fs=24):
    rate = 0.62 if is_mono else 0.60
    return len(text) * fs * rate

# Test Right text lines with max 36 chars:
txt = "distribution, kernel, CPU count, memory, mounts, network interfaces and addresses, DMI info (the hardware identity the BIOS reports, such as vendor and model), environment, date and time, SELinux, user, Python"

# Manual break test:
lines = [
    "distribution, kernel, CPU count,",
    "memory, mounts, network interfaces",
    "and addresses, DMI info (the hardware",
    "identity the BIOS reports, such as",
    "vendor and model), environment,",
    "date and time, SELinux, user, Python"
]

print("Joined equals original?:", " ".join(lines) == txt)

rbox_x = 940
rbox_w = 620
rbox_right = 1560
rtext_x = 970

for l in lines:
    w = text_w(l)
    pad = rbox_right - (rtext_x + w)
    print(f"'{l}' (len {len(l)}): w={w:.1f}, pad_right={pad:.1f}")

# Check Left box with width 860 (x: 40 to 900):
lbox_x = 40
lbox_w = 860
lbox_right = 900
ltext_x = 126 # icon at 52 (56px), ends at 108, text at 126

print(f"\nLeft box (w=860, right=900, text_x=126):")
c1_lines = [
    ("ansible gpu001 -m ansible.builtin.setup | less:", True),
    ("every fact for one host, scroll the whole dictionary", False)
]
for l, mono in c1_lines:
    w = text_w(l, mono)
    pad = lbox_right - (ltext_x + w)
    print(f"C1: '{l[:30]}...' w={w:.1f}, pad_right={pad:.1f}")

c2_lines = [
    ("setup -a filter=ansible_default_ipv4:", True),
    ("narrows to the default network route", False)
]
for l, mono in c2_lines:
    w = text_w(l, mono)
    pad = lbox_right - (ltext_x + w)
    print(f"C2: '{l[:30]}...' w={w:.1f}, pad_right={pad:.1f}")

c3_lines = [
    ("setup -a gather_subset=!all,!min,network,hardware:", True),
    ("excludes all and min, gathers only network and", False),
    ("hardware: the command to run when a node misbehaves", False)
]
for l, mono in c3_lines:
    w = text_w(l, mono)
    pad = lbox_right - (ltext_x + w)
    print(f"C3: '{l[:30]}...' w={w:.1f}, pad_right={pad:.1f}")
