def text_w(text, is_mono=False, fs=24):
    rate = 0.62 if is_mono else 0.60
    return len(text) * fs * rate

box_right = 1560
text_x = 138

print("=== Updated wraps ===")
# Example line (4 lines):
ex_lines = [
    ("inventory_hostname: ansible_facts[distribution] ansible_facts[distribution_version],", True),
    ("kernel ansible_facts[kernel], ansible_facts[processor_vcpus] vCPUs,", True),
    ("(ansible_facts[memtotal_mb] / 1024) | round(1) GiB RAM,", True),
    ("primary IP ansible_facts[default_ipv4][address]", True)
]
original_ex = "inventory_hostname: ansible_facts[distribution] ansible_facts[distribution_version], kernel ansible_facts[kernel], ansible_facts[processor_vcpus] vCPUs, (ansible_facts[memtotal_mb] / 1024) | round(1) GiB RAM, primary IP ansible_facts[default_ipv4][address]"
print("Ex line match:", " ".join([l for l, m in ex_lines]) == original_ex)
for l, m in ex_lines:
    w = text_w(l, m)
    pad = box_right - (text_x + w)
    print(f"  Ex: len={len(l)} w={w:.1f} pad={pad:.1f}")

# Note (2 lines):
original_note = "GiB is binary: 1 GiB is 1024 MiB; the value is a plain number so the division needs no conversion"
note_lines = [
    "GiB is binary: 1 GiB is 1024 MiB; the value is a plain number",
    "so the division needs no conversion"
]
print("Note match:", " ".join(note_lines) == original_note)
for l in note_lines:
    w = text_w(l, False)
    pad = box_right - (text_x + w)
    print(f"  Note: len={len(l)} w={w:.1f} pad={pad:.1f}")

# Cost (2 lines):
original_cost = "each fact is a probe on each host: seconds per host before your first real task, minutes on hundreds of nodes"
cost_lines = [
    "each fact is a probe on each host: seconds per host before your first real task,",
    "minutes on hundreds of nodes"
]
print("Cost match:", " ".join(cost_lines) == original_cost)
for l in cost_lines:
    w = text_w(l, False)
    pad = box_right - (text_x + w)
    print(f"  Cost: len={len(l)} w={w:.1f} pad={pad:.1f}")

# Prefer strip (3 lines):
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
    print(f"  Prefer: len={len(l)} w={w:.1f} pad={pad:.1f}")
