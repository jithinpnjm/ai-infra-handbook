#!/usr/bin/env python3
"""Flag prose (outside code fences/inline code) that Docusaurus MDX would parse as JSX/expressions: <letter, </, <digit, { }."""
import re, sys
for path in sys.argv[1:]:
    inc = False
    for i, l in enumerate(open(path).read().split('\n'), 1):
        if l.startswith('```'): inc = not inc; continue
        if inc or l.startswith('---'): continue
        s = re.sub(r'`[^`]*`', '', l)
        if re.search(r'<[A-Za-z/0-9=]', s) or re.search(r'[{}]', s):
            print(f"{path}:{i}: {s[:110]}")
