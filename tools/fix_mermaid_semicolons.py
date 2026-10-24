#!/usr/bin/env python3
"""Mermaid sequence/state diagrams treat ';' as a statement separator: replace ';' inside message text with ','."""
import re, sys
for p in sys.argv[1:]:
    s = open(p).read(); changed = False
    def fix(m):
        global changed
        body = m.group(1)
        if not re.match(r'\s*(sequenceDiagram|stateDiagram|stateDiagram-v2)', body): return m.group(0)
        out = []
        for line in body.split('\n'):
            if ';' in line and (':' in line):
                head, _, text = line.partition(':')
                nt = text.replace(';', ',')
                if nt != text: changed = True
                line = head + ':' + nt
            out.append(line)
        return '```mermaid\n' + '\n'.join(out) + '```'
    s2 = re.sub(r'```mermaid\n(.*?)```', fix, s, flags=re.S)
    if changed: open(p, 'w').write(s2); print('fixed', p)
