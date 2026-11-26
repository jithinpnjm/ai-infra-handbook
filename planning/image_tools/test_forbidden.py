import re

forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']

labels = [
    "Reading facts: three setup commands and the facts list",
    "ansible gpu001 -m ansible.builtin.setup | less: every fact for one host, scroll the whole dictionary",
    "setup -a filter=ansible_default_ipv4: narrows to the default network route",
    "setup -a gather_subset=!all,!min,network,hardware: excludes all and min, gathers only network and hardware: the command to run when a node misbehaves",
    "What facts cover",
    "distribution, kernel, CPU count, memory, mounts, network interfaces and addresses, DMI info (the hardware identity the BIOS reports, such as vendor and model), environment, date and time, SELinux, user, Python",
    "inventory_hostname: ansible_facts[distribution] ansible_facts[distribution_version], kernel ansible_facts[kernel], ansible_facts[processor_vcpus] vCPUs, (ansible_facts[memtotal_mb] / 1024) | round(1) GiB RAM, primary IP ansible_facts[default_ipv4][address]",
    "GiB is binary: 1 GiB is 1024 MiB; the value is a plain number so the division needs no conversion",
    "ansible_facts[distribution] instead of the short injected names such as ansible_distribution: older names share one global space, so a host-reported value can sit next to your own variable of the same name; inject_facts_as_vars controls the short names",
    "each fact is a probe on each host: seconds per host before your first real task, minutes on hundreds of nodes",
    "Facts describe what the host actually is"
]

for l in labels:
    words = re.findall(r'\b[a-zA-Z]+\b', l.lower())
    for f in forbidden:
        if f in words:
            print(f"FORBIDDEN '{f}' in '{l}'")
print("Forbidden check complete.")
