import xml.etree.ElementTree as ET
import re

labels = [
    "The string false trap in when",
    "run with -e flag=false",
    "the value arrives as the string false",
    "when: flag treats a non-empty string as true",
    "task runs when it should skip",
    "fix with when: flag | bool",
    "string false becomes boolean false",
    "task skips",
    'write the bare expression when: var, not when: "{{ var }}"'
]

print("Labels count:", len(labels))
for i, l in enumerate(labels, 1):
    print(f"{i}. {l}")
