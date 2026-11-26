import xml.etree.ElementTree as ET
import re

title = "Investigation commands from cheapest to most targeted"

items = [
    "--syntax-check (parse only, touches no host)",
    "--list-tasks --list-tags --list-hosts",
    "--check --diff --limit gpu001 (what would change)",
    "--step (confirm every task y/n/c)",
    "--start-at-task Install driver",
    "-t config -l gpu001",
    "ad hoc setup with filter=ansible_default_ipv4",
    "ad hoc command which python3 with -vvv"
]

warning = "it skips earlier set_fact so the driver task fails on an undefined variable"

print("Items count:", len(items))
print("Warning length:", len(warning))
