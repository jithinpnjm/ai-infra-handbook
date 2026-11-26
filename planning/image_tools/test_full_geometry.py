import re

# Font measurements
# sans: 0.6 * fs
# mono: 0.62 * fs

def mono_w(text, fs=24):
    return len(text) * 0.62 * fs

def sans_w(text, fs=24):
    return len(text) * 0.6 * fs

# Check table columns:
# Col 1: x=40, w=540 (usable: 40+16=56 to 580-16=564, max_w = 508)
# Col 2: x=590, w=350 (usable: 590+16=606 to 940-16=924, max_w = 318)
# Col 3: x=950, w=610 (usable: 950+16=966 to 1560-16=1544, max_w = 578)

# Check col 1 splits:
col1_checks = [
    ("NodeName={{ h }}", [("NodeName={{ h }}", True)]),
    ("NodeAddr={{ v.ansible_host }}", [("NodeAddr={{ v.ansible_host }}", True)]),
    ("CPUs={{ v.ansible_facts.processor_vcpus }}", [
        ("CPUs={{ v.ansible_facts.", True),
        ("processor_vcpus }}", True)
    ]),
    ("Boards=1", [("Boards=1", True)]),
    ("SocketsPerBoard={{ v.sockets | default(2) }}", [
        ("SocketsPerBoard={{ ", True),
        ("v.sockets | default(2) }}", True)
    ]),
    ("CoresPerSocket={{ v.cores_per_socket | default(48) }}", [
        ("CoresPerSocket={{ ", True),
        ("v.cores_per_socket | default(48) }}", True)
    ]),
    ("ThreadsPerCore=1", [("ThreadsPerCore=1", True)]),
    ("RealMemory={{ (v.ansible_facts.memtotal_mb * 0.95) | int }}", [
        ("RealMemory={{ (v.ansible_facts.", True),
        ("memtotal_mb * 0.95) | int }}", True)
    ]),
    ("Gres=gpu:{{ v.gpu_model | default(h100) }}:{{ v.gpu_count | default(8) }}", [
        ("Gres=gpu:{{ v.gpu_model | ", True),
        ("default(h100) }}:", True),
        ("{{ v.gpu_count | default(8) }}", True)
    ]),
    ("State=UNKNOWN", [("State=UNKNOWN", True)])
]

max_w1 = 540 - 32
print("Max usable width in Col 1:", max_w1)
for full, splits in col1_checks:
    # check recombines correctly
    recombined = "".join(s[0] for s in splits).strip()
    assert recombined == full, f"Mismatch: '{recombined}' != '{full}'"
    for s, is_m in splits:
        w = mono_w(s) if is_m else sans_w(s)
        assert w <= max_w1, f"Overflow in Col 1: '{s}' width {w} > {max_w1}"
print("Col 1 splits: ALL PASS!")

# Check col 2 splits:
max_w2 = 350 - 32
print("Max usable width in Col 2:", max_w2)
col2_checks = [
    ("the host name from groups[gpu] | sort", [
        ("the host name from ", False),
        ("groups[gpu] | sort", False)
    ]),
    ("hostvars", [("hostvars", False)]),
    ("gathered fact", [("gathered fact", False)]),
    ("host variable", [("host variable", False)]),
    ("host variables", [("host variables", False)])
]
for full, splits in col2_checks:
    recombined = "".join(s[0] for s in splits).strip()
    assert recombined == full, f"Mismatch: '{recombined}' != '{full}'"
    for s, is_m in splits:
        w = mono_w(s) if is_m else sans_w(s)
        assert w <= max_w2, f"Overflow in Col 2: '{s}' width {w} > {max_w2}"
print("Col 2 splits: ALL PASS!")

# Check col 3 splits:
max_w3 = 610 - 32
print("Max usable width in Col 3:", max_w3)
col3_checks = [
    ("-", [("-", False)]),
    ("2", [("2", False)]),
    ("48", [("48", False)]),
    ("h100 and 8", [("h100 and 8", False)]),
    ("leave memory unused: the operating system and the Slurm daemon need room too, so the scheduler never promises every last byte to a job", [
        ("leave memory unused: the operating ", False),
        ("system and the Slurm daemon need ", False),
        ("room too, so the scheduler never ", False),
        ("promises every last byte to a job", False)
    ])
]
for full, splits in col3_checks:
    recombined = "".join(s[0] for s in splits).strip()
    assert recombined == full, f"Mismatch: '{recombined}' != '{full}'"
    for s, is_m in splits:
        w = mono_w(s) if is_m else sans_w(s)
        assert w <= max_w3, f"Overflow in Col 3: '{s}' width {w} > {max_w3}"
print("Col 3 splits: ALL PASS!")
