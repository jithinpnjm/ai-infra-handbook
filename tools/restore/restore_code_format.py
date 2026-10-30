#!/usr/bin/env python3
"""Re-wrap in backticks commands/options/paths/identifiers that lost code format. Usage: restore_code_format.py OLD NEW"""
import re, sys
o, n = open(sys.argv[1], encoding='utf8').read(), open(sys.argv[2], encoding='utf8').read()
strip = lambda s: re.sub(r'```.*?```', '', s, flags=re.S)
cs = lambda s: set(re.findall(r'`([^`\n]{3,40})`', strip(s)))
dem = [x for x in cs(o)-cs(n) if re.match(r'^(-{1,2}[\w-]+|/[\w./-]+|[A-Z][A-Za-z]+(?:[A-Z]\w+)+|\w+_\w+)$', x) and x in re.sub(r'`[^`\n]*`','',strip(n))]
parts = re.split(r'(```.*?```|`[^`\n]*`)', n, flags=re.S)
cnt = 0
for i in range(0, len(parts), 2):
    for x in dem:
        parts[i], k = re.subn(r'(?<![\w`-])' + re.escape(x) + r'(?![\w`])', '`' + x + '`', parts[i]); cnt += k
open(sys.argv[2], 'w', encoding='utf8').write(''.join(parts)); print('re-wrapped', cnt, 'occurrences of', len(dem), 'terms')
