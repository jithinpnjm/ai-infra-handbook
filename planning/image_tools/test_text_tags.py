import re
import xml.etree.ElementTree as ET

# Define the exact 18 labels
expected_labels = [
    "Reading hosts.ini: hosts, groups, groups of groups",
    "[gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12",
    "[login] login01 ansible_host=10.0.10.5",
    "[cluster:children] gpu login",
    "[cluster:vars] ansible_user=automation, ansible_python_interpreter=/usr/bin/python3",
    "cluster",
    "gpu",
    "gpu01",
    "gpu02",
    "login",
    "login01",
    "ansible_user and interpreter apply to all three machines",
    "each host has a name and optionally an address",
    "a group collects hosts that share a role",
    "a group of groups, written with :children, lets one command reach every member: a play aimed at cluster reaches all three machines",
    "ansible-inventory --graph (run first: shows the nesting at a glance), --list, --host gpu01",
    "a node missing from the inventory quietly misses every change you make",
    "The inventory is the phone book of your fleet"
]

print("Total expected labels:", len(expected_labels))
