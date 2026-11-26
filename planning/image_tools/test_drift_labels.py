#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

labels = [
    "Code, state and the real cloud: reading drift",
    "Code (what you want)",
    "State (Terraform's notebook of what it built)",
    "Cloud (what really exists)",
    "plan compares code and state, after refreshing state from the cloud",
    "drift is the gap between code and reality: someone scaled a pool from the console during an incident, the next apply would undo it",
    "import brings an object created by hand into state so apply does not collide; plan only knows what is in state",
    "terraform plan -refresh-only updates state to match the outside world without proposing changes to resources",
    "terraform plan -detailed-exitcode returns 0 for no changes, 1 for error, 2 for changes present",
    "exit code 2 opens a ticket without a human reading the whole plan",
    "if the emergency change was right, fix the code; if wrong, re-apply; never leave it",
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. len={len(l):3d} | {l}")
