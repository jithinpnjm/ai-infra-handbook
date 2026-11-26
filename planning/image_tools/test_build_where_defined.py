import xml.etree.ElementTree as ET
import re

# Exact labels from prompt:
title_text = "Where a variable can be defined, from the desk note to the front door"

labels = [
    "task vars: only that one task, gone when it ends (extra: 1)",
    "set_fact and register: created by tasks",
    "include_vars: loads a file or directory into host variables during the run",
    "play vars: vars block, belongs to the play, stops when the play ends",
    "vars_files: loads files at the start of the play; the file name can itself be a template, vars/{{ ansible_facts[os_family] | lower }}.yml, so Debian and RedHat hosts load different files with no if statement",
    "vars_prompt: asks a person at run time: avoid in automation, it stops the run and waits (private: false, name reason, prompt Maintenance reason)",
    "lookup results and lookup(env, ...)",
    "inventory, group_vars, host_vars (4.5) and role defaults/ and vars/ (4.11)",
    "extra vars -e: key=value, a JSON-style string such as {\"k\": [1,2]}, or @file.yml",
    "put a value where the people who own it will look: a cluster-wide default in group_vars/all, a rack's special case in the group for that rack, a one-off test on the command line where it vanishes when the run ends; which one wins when two disagree is in 4.5",
    "late Tuesday: raising the NCCL debug level for the second cluster also turned on verbose logging on the first, filling its disk: the setting was written in a place that reached further than you thought",
    "The place you choose decides how far the value reaches"
]

print("Total labels to place:", len(labels))
