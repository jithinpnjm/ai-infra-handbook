#!/usr/bin/env python3
"""Syntax-check python code blocks that are new compared with a backup. Usage: pycheck.py FILE BACKUP"""
import sys, ast, re
def blocks(t):
    out, cur, lang = [], None, None
    for l in t.split('\n'):
        m = re.match(r'^\s*```(\w*)\s*$', l)
        if m:
            if cur is None: cur, lang = [], m.group(1)
            else:
                out.append((lang, '\n'.join(cur))); cur = None
        elif cur is not None: cur.append(l)
    return out
n, o = open(sys.argv[1], encoding='utf8').read(), open(sys.argv[2], encoding='utf8').read()
ob = {b for _, b in blocks(o)}; new = bad = 0
for lang, b in blocks(n):
    pyish = lang in ('python','py') or (lang=='' and re.search(r'^\s*(def |class |import |from \w+ import|for \w+ in |while |if .*:$|print\()', b, re.M) and not re.search(r'^\s*(\$|#!|sudo |kubectl |apiVersion)', b, re.M))
    if not pyish or b in ob or re.search(r'^\s*(>>>|\.\.\.|\$)', b, re.M): continue
    new += 1
    try: ast.parse(b)
    except SyntaxError as e:
        if '…' in b or '...' in b and 'def ' not in b: continue
        bad += 1; print('SYNTAX', e.msg, '|', b[:90].replace('\n', ' / '))
print(sys.argv[1].split('/')[-1][:30], new, 'new python blocks', bad, 'bad')
