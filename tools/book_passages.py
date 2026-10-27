#!/usr/bin/env python3
"""Passage-level coverage: which paragraphs of a book chapter are NOT in the handbook chapter(s)?
Usage: python3 tools/book_passages.py <book-folder> "<chapter title prefix>" <handbook labels...> [--min 0.35] [--show 40]
Example: python3 tools/book_passages.py supercomputers-for-linux-sysadmins-managing-modern-hpc-clusters-and-supercomputers-from-software-to-hardware "11. " 1.6 6.7
For every paragraph of the book chapter (40+ words) it takes the distinctive words (rare in the whole corpus),
numbers and identifiers, and measures how many appear in the named handbook chapters. Paragraphs below --min are
printed as 'NOT COVERED': these are the explanations, examples, scripts and stories still missing.
A summary-style rewrite of a section scores low here even when its headings match."""
import re, sys, os, glob, sqlite3, collections, math
book, prefix = sys.argv[1], sys.argv[2]
labels = [a for a in sys.argv[3:] if re.match(r'^\d+\.\d+$', a)]
mn = float(sys.argv[sys.argv.index('--min') + 1]) if '--min' in sys.argv else 0.35
show = int(sys.argv[sys.argv.index('--show') + 1]) if '--show' in sys.argv else 40
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db = sqlite3.connect(os.path.expanduser('~/Desktop/books-toon-rag/_index/chunks.db'))
word = re.compile(r"[A-Za-z][A-Za-z0-9_'-]{5,}|\d+(?:\.\d+)?|[\w./-]*[_/.][\w./-]+")
def toks(t): return {w.lower().strip("'-") for w in word.findall(t)}
df = collections.Counter(); n = 0
for (c,) in db.execute('select content from chunks'):
    n += 1
    for w in toks(c): df[w] += 1
rows = db.execute('select content from chunks where book like ? and chapter like ? order by chunk_id', (book[:60] + '%', prefix + '%')).fetchall()
if not rows:
    print('no such book chapter'); sys.exit(2)
text = '\n'.join(r[0] for r in rows)
hb = ''
for l in labels:
    p, c = l.split('.')
    for f in glob.glob(f'{ROOT}/docs/part-{int(p):02d}-*/{int(c):02d}-*.md'):
        s = open(f, errors='ignore').read(); i = s.find('## Sources and review notes'); hb += s[:i if i > 0 else None]
hbt = toks(hb)
paras, buf = [], []
for line in text.split('\n'):
    if not line.strip(): continue
    buf.append(line.strip())
    if len(' '.join(buf).split()) >= 60 and re.search(r'[.!?:]$', line.strip()):
        paras.append(' '.join(buf)); buf = []
if len(' '.join(buf).split()) >= 40: paras.append(' '.join(buf))
res = []
for p in paras:
    ts = {w for w in toks(p) if df[w] <= max(3, 0.02 * n)}
    if len(ts) < 6: continue
    cov = len(ts & hbt) / len(ts); res.append((cov, p))
tot = sum(len(p.split()) for _, p in res); miss = sum(len(p.split()) for c, p in res if c < mn)
print(f'{book[:50]} chapter "{prefix}": {len(res)} paragraphs checked, {len(text.split())} words; handbook chapters {labels}')
print(f'NOT COVERED (< {mn:.0%} of distinctive terms present): {sum(1 for c,_ in res if c<mn)} paragraphs = {miss} words = {miss/max(tot,1):.0%} of the checked text')
for c, p in sorted([x for x in res if x[0] < mn])[:show]:
    print(f'\n[{c:.0%}] {p[:260].replace(chr(10), " ")}...')
