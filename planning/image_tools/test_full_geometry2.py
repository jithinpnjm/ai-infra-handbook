import re

def mono_w(text, fs=24):
    return len(text) * 0.62 * fs

def sans_w(text, fs=24):
    return len(text) * 0.6 * fs

# Check table columns:
# Col 1: x=40, w=540 (usable: max_w = 508)
# Col 2: x=590, w=350 (usable: max_w = 318)
# Col 3: x=950, w=610 (usable: max_w = 578)

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
        ("v.cores_per_socket | ", True),
        ("default(48) }}", True)
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
for full, splits in col1_checks:
    recombined = "".join(s[0] for s in splits).strip()
    assert recombined == full, f"Mismatch: '{recombined}' != '{full}'"
    for s, is_m in splits:
        w = mono_w(s) if is_m else sans_w(s)
        assert w <= max_w1, f"Overflow in Col 1: '{s}' width {w} > {max_w1}"
print("Col 1 splits: ALL PASS!")

# Also check header and footer:
# Header 1: 'ClusterName={{ slurm_cluster_name }}'
# Header 2: 'SlurmctldHost={{ groups[slurm_controller][0] }}'
# In header panel: w=1520, split into two boxes:
# Box 1: w=740 -> max_w = 708. 'ClusterName={{ slurm_cluster_name }}' mono_w = 36 * 14.88 = 535.7 <= 708!
# Box 2: w=740 -> max_w = 708. 'SlurmctldHost={{ groups[slurm_controller][0] }}' mono_w = 46 * 14.88 = 684.5 <= 708!
assert mono_w('ClusterName={{ slurm_cluster_name }}') <= 708
assert mono_w('SlurmctldHost={{ groups[slurm_controller][0] }}') <= 708
print("Header panel: ALL PASS!")

# Footer panel:
# Box width = 1520 -> max_w = 1488.
# PartitionName line:
part_splits = [
    ("PartitionName=gpu Nodes={{ groups[gpu] | sort | join(,) }} ", True),
    ("Default=YES MaxTime=INFINITE State=UP", True)
]
recombined = "".join(s[0] for s in part_splits).strip()
assert recombined == 'PartitionName=gpu Nodes={{ groups[gpu] | sort | join(,) }} Default=YES MaxTime=INFINITE State=UP'
for s, is_m in part_splits:
    w = mono_w(s) if is_m else sans_w(s)
    assert w <= 1400, f"Overflow in Footer Part line: '{s}' width {w}"

desc_s = "a partition is Slurm's name for a pool of nodes that a user submits jobs to"
assert sans_w(desc_s) <= 1400
print("Footer panel: ALL PASS!")

# Tip strip:
tip_splits = [
    ("set v = hostvars[h] gives the long path a short name; ", False),
    ("for large clusters compress the node list into Slurm hostlist syntax ", False),
    ("such as gpu[001-032] with a custom filter or a precomputed variable", False)
]
recombined = "".join(s[0] for s in tip_splits).strip()
assert recombined == 'set v = hostvars[h] gives the long path a short name; for large clusters compress the node list into Slurm hostlist syntax such as gpu[001-032] with a custom filter or a precomputed variable'
for s, is_m in tip_splits:
    w = mono_w(s) if is_m else sans_w(s)
    assert w <= 1400, f"Overflow in Tip strip: '{s}' width {w}"
print("Tip strip: ALL PASS!")

# Bottom bar:
bot_s = "Defaults fill the gaps where data is missing"
assert sans_w(bot_s) <= 1400
print("Bottom bar: ALL PASS!")
