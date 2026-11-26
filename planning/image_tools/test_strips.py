def text_w(text, is_mono=False, fs=24):
    rate = 0.62 if is_mono else 0.60
    return len(text) * fs * rate

box_x = 40
box_w = 1520
box_right = 1560
icon_w = 56
icon_x = 64
text_x = 138

print(f"Full width box: right={box_right}, text_x={text_x}, available={box_right - text_x}")

# Example line:
ex_lines = [
    ("inventory_hostname: ansible_facts[distribution] ansible_facts[distribution_version],", True),
    ("kernel ansible_facts[kernel], ansible_facts[processor_vcpus] vCPUs,", True),
    ("(ansible_facts[memtotal_mb] / 1024) | round(1) GiB RAM, primary IP ansible_facts[default_ipv4][address]", True)
]
original_ex = "inventory_hostname: ansible_facts[distribution] ansible_facts[distribution_version], kernel ansible_facts[kernel], ansible_facts[processor_vcpus] vCPUs, (ansible_facts[memtotal_mb] / 1024) | round(1) GiB RAM, primary IP ansible_facts[default_ipv4][address]"
joined_ex = " ".join([l for l, m in ex_lines])
print("Example line match:", joined_ex == original_ex)
for l, m in ex_lines:
    w = text_w(l, m)
    pad = box_right - (text_x + w)
    print(f"  Ex line: len={len(l)} w={w:.1f} pad={pad:.1f}")

# Example note:
original_note = "GiB is binary: 1 GiB is 1024 MiB; the value is a plain number so the division needs no conversion"
note_lines = [
    "GiB is binary: 1 GiB is 1024 MiB; the value is a plain number so the division needs no conversion"
]
print("Note len:", len(original_note), "w:", text_w(original_note, False), "pad:", box_right - (text_x + text_w(original_note, False)))

# Prefer strip (orange):
original_prefer = "ansible_facts[distribution] instead of the short injected names such as ansible_distribution: older names share one global space, so a host-reported value can sit next to your own variable of the same name; inject_facts_as_vars controls the short names"
prefer_lines = [
    "ansible_facts[distribution] instead of the short injected names such as ansible_distribution:",
    "older names share one global space, so a host-reported value can sit next to your own variable",
    "of the same name; inject_facts_as_vars controls the short names"
]
print("Prefer match:", " ".join(prefer_lines) == original_prefer)
for l in prefer_lines:
    w = text_w(l, False)
    pad = box_right - (text_x + w)
    print(f"  Prefer line: len={len(l)} w={w:.1f} pad={pad:.1f}")

# Cost strip:
original_cost = "each fact is a probe on each host: seconds per host before your first real task, minutes on hundreds of nodes"
cost_lines = [
    "each fact is a probe on each host: seconds per host before your first real task, minutes on hundreds of nodes"
]
print("Cost match:", " ".join(cost_lines) == original_cost)
w = text_w(cost_lines[0], False)
pad = box_right - (text_x + w)
print(f"  Cost line: len={len(cost_lines[0])} w={w:.1f} pad={pad:.1f}")

# Bottom bar:
original_bottom = "Facts describe what the host actually is"
w_bot = text_w(original_bottom, False, 30) # 30px bold
print(f"Bottom line (30px): len={len(original_bottom)} w={w_bot:.1f} (centered at 800)")
