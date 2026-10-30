#!/usr/bin/env python3
"""Find '<' followed by a digit/space outside code (breaks MDX). Usage: mdx_guard.py [paths...]"""
import re, sys, glob
files = sys.argv[1:] or glob.glob('docs/**/*.md', recursive=True)
bad = 0
for f in files:
    t = re.sub(r'```.*?```', lambda m: '\n' * m.group(0).count('\n'), open(f, encoding='utf8').read(), flags=re.S)
    for i, l in enumerate(t.split('\n'), 1):
        s = re.sub(r'`[^`]*`', '', l)
        if re.search(r'<[0-9]', s): print(f'{f}:{i}: {l[:100]}'); bad += 1
print('mdx_guard:', bad, 'problem lines')
