#!/usr/bin/env python3
"""Lossless-rewrite check: what did a rewrite drop?
Usage: python3 tools/loss_check.py OLD.md NEW.md [--list]
Compares numbers, technical terms (code spans such as commands, flags, paths, API and metric names),
headings, table rows, code blocks, checkpoint questions and cited sources. Every item in the 'lost'
lists must be restored (in plain book-style wording) or justified in writing. See planning/LANGUAGE_RULE.md."""
import re, sys, os
def norm(t):
    t = t.lower().replace('`', '').replace('*', '').replace('\\', '').replace('$', '')
    t = re.sub(r'(?<=\d),(?=\d{3})', '', t); t = re.sub(r'(\d+)\.0+\b', r'\1', t)
    return re.sub(r'\s+', ' ', t)
span = re.compile(r'`([^`\n]{3,60})`')
tech = re.compile(r'^(?:--?[a-z][\w-]*|[\w./:=-]*[_./\d=:-][\w./:=-]*|[A-Za-z]+[A-Z][A-Za-z0-9]*)$')
def items(t): return sorted({s for s in span.findall(t) if tech.match(s) and not re.match(r'^[\d.,%x×-]+$', s)})
def nums(t): return set(re.findall(r'\d+(?:\.\d+)?', norm(t)))
old, new = open(sys.argv[1]).read(), open(sys.argv[2]).read()
nl = norm(new)
lost_items = [s for s in items(old) if norm(s) not in nl]
lost_nums = sorted(nums(old) - nums(new), key=float)
rows = lambda t: len([l for l in t.splitlines() if l.startswith('|')])
code = lambda t: len(re.findall(r'```', t)) // 2
heads = lambda t: [norm(l.lstrip('#').strip()) for l in t.splitlines() if l.startswith('#')]
books = [b for b in os.listdir(os.path.expanduser('~/Desktop/books-toon-rag')) if not b.startswith(('_', '.'))]
lost_books = [b for b in books if b in old and b not in new]
src = lambda t: set(re.findall(r'chapter-\d+[\w-]*\.md|volume-\d+/[\w./-]+\.md', t))
lost_src = sorted(src(old) - src(new))
w = lambda t: len(t.split())
print(f"words {w(old)} -> {w(new)} ({(w(new)/w(old)-1)*100:+.0f}%) | table rows {rows(old)} -> {rows(new)} | code blocks {code(old)} -> {code(new)} | questions {old.count('<summary>')} -> {new.count('<summary>')} | headings {len(heads(old))} -> {len(heads(new))}")
print(f"technical terms lost: {len(lost_items)} of {len(items(old))} | numbers lost: {len(lost_nums)} of {len(nums(old))} | gem books no longer cited: {lost_books} | source files no longer cited: {len(lost_src)}")
if '--list' in sys.argv:
    print('LOST TERMS:', lost_items); print('LOST NUMBERS:', lost_nums); print('LOST SOURCE FILES:', lost_src)
sys.exit(1 if (lost_items or lost_nums or lost_books or lost_src) else 0)
