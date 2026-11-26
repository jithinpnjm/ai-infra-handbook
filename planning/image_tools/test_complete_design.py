import sys

def check_text_paddings(x, y, w, h, text_lines, fs=24, is_mono=False, is_bold=False):
    factor = 0.62 if is_mono else 0.60
    max_w = max(len(ln) * factor * fs for ln in text_lines)
    pad_h = (w - max_w) / 2
    line_h = fs * 1.35
    total_text_h = len(text_lines) * line_h
    pad_v = (h - total_text_h) / 2
    return max_w, pad_h, pad_v

# Test File Line 1
l1 = ["[gpu]", "gpu01 ansible_host=10.0.10.11,", "gpu02 ansible_host=10.0.10.12"]
w, ph, pv = check_text_paddings(65, 125, 690, 110, l1, fs=24, is_mono=True)
print(f"Line 1 in 690x110: max_w={w:.1f}, pad_h={ph:.1f}, pad_v={pv:.1f}")

# Test Callout 2
c2 = ["a group collects hosts that share a role"]
w, ph, pv = check_text_paddings(65, 245, 690, 50, c2, fs=24, is_mono=False)
print(f"Callout 2 in 690x50: max_w={w:.1f}, pad_h={ph:.1f}, pad_v={pv:.1f}")

# Test Callout 1
c1 = ["each host has a name and optionally an address"]
w, ph, pv = check_text_paddings(65, 305, 690, 50, c1, fs=24, is_mono=False)
print(f"Callout 1 in 690x50: max_w={w:.1f}, pad_h={ph:.1f}, pad_v={pv:.1f}")

# Test File Line 2
l2 = ["[login]", "login01 ansible_host=10.0.10.5"]
w, ph, pv = check_text_paddings(65, 365, 690, 80, l2, fs=24, is_mono=True)
print(f"Line 2 in 690x80: max_w={w:.1f}, pad_h={ph:.1f}, pad_v={pv:.1f}")

# Test File Line 3
l3 = ["[cluster:children]", "gpu login"]
w, ph, pv = check_text_paddings(65, 455, 690, 80, l3, fs=24, is_mono=True)
print(f"Line 3 in 690x80: max_w={w:.1f}, pad_h={ph:.1f}, pad_v={pv:.1f}")

# Test File Line 4
l4 = ["[cluster:vars]", "ansible_user=automation,", "ansible_python_interpreter=/usr/bin/python3"]
w, ph, pv = check_text_paddings(65, 545, 690, 110, l4, fs=24, is_mono=True)
print(f"Line 4 in 690x110: max_w={w:.1f}, pad_h={ph:.1f}, pad_v={pv:.1f}")

