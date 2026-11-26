import re

title = "Reading facts: three setup commands and the facts list"
cmd1 = "ansible gpu001 -m ansible.builtin.setup | less: every fact for one host, scroll the whole dictionary"
cmd2 = "setup -a filter=ansible_default_ipv4: narrows to the default network route"
cmd3 = "setup -a gather_subset=!all,!min,network,hardware: excludes all and min, gathers only network and hardware: the command to run when a node misbehaves"

right_hdr = "What facts cover"
right_text = "distribution, kernel, CPU count, memory, mounts, network interfaces and addresses, DMI info (the hardware identity the BIOS reports, such as vendor and model), environment, date and time, SELinux, user, Python"

ex_line = "inventory_hostname: ansible_facts[distribution] ansible_facts[distribution_version], kernel ansible_facts[kernel], ansible_facts[processor_vcpus] vCPUs, (ansible_facts[memtotal_mb] / 1024) | round(1) GiB RAM, primary IP ansible_facts[default_ipv4][address]"
ex_note = "GiB is binary: 1 GiB is 1024 MiB; the value is a plain number so the division needs no conversion"

prefer_text = "ansible_facts[distribution] instead of the short injected names such as ansible_distribution: older names share one global space, so a host-reported value can sit next to your own variable of the same name; inject_facts_as_vars controls the short names"

cost_text = "each fact is a probe on each host: seconds per host before your first real task, minutes on hundreds of nodes"

bottom_text = "Facts describe what the host actually is"

labels = [
    title,
    cmd1, cmd2, cmd3,
    right_hdr, right_text,
    ex_line, ex_note,
    prefer_text,
    cost_text,
    bottom_text
]

print("Total labels:", len(labels))
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. len={len(l):3d} | {l}")
