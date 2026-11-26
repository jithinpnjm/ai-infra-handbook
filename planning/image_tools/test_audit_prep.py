import xml.etree.ElementTree as ET
import re

source_labels = [
    "Where Jinja appears in a playbook, and the quoting rule for each place",
    "Place",
    "Rule",
    "task arguments, vars, loop",
    'a YAML value that starts with {{ must be quoted: msg: "{{ var }}"; mixing is fine: path: "/data/{{ project }}/{{ env }}"',
    "when, failed_when, changed_when",
    'already a Jinja expression: write when: ansible_distribution == Ubuntu, not when: "{{ ... }}"',
    "template module files",
    "src: nccl.conf.j2 rendered on the control node",
    "inventory variables",
    "Ansible evaluates templates on the control node, not on the servers: a template task fills its blanks on your laptop or CI runner then copies finished text to the target; a shell task runs on the target",
    "AnsibleUndefinedVariable on one host while the same playbook works on others: the variable is defined only in a different inventory group, or in a file the play never loads",
    "Know where Ansible evaluates the template to know where to look first"
]

print("Script template ready")
