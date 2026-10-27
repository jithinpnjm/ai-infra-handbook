#!/usr/bin/env python3
"""Build a ready-to-paste NotebookLM brief for one handbook chapter: the chapter's place in the book, its outline,
the exact source chapters and notes to use, the gem-book chapters mapped to it (from the triage and deferred tables),
and one prompt per section.
Usage: python3 tools/notebooklm_brief.py 6.7 [> planning/notebooklm/6-07.md]     All chapters of a part: --part 6"""
import re, os, sys, glob, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def structure():
    parts, cur = {}, None
    for l in open(f'{ROOT}/planning/structure.txt', encoding='utf-8'):
        m = re.match(r'@PART (\d+) \| ([^|]*)\|([^|]*)\|', l)
        if m: cur = int(m.group(1)); parts[cur] = dict(slug=m.group(2).strip(), title=m.group(3).strip(), ch={}); continue
        m = re.match(r'^(\d\d) \| ([^|]*)\|([^|]*)\|([^|]*)', l.strip())
        if m and cur is not None: parts[cur]['ch'][int(m.group(1))] = (m.group(2).strip(), m.group(3).strip(), m.group(4).strip())
    return parts
S = structure()
def read_doc(p, c):
    fs = glob.glob(f'{ROOT}/docs/part-{p:02d}-*/{c:02d}-*.md')
    return open(fs[0], errors='ignore').read() if fs else ''
def outline(text):
    sections, cur = [], None
    for l in text.splitlines():
        if re.match(r'^## ', l):
            h = l[3:].strip()
            if h.startswith(('Checkpoint', 'Sources', 'Exercises', 'Interview', 'Common first', 'How it fails', 'Hands-on', 'Commands', 'Prerequisites', 'Why this matters', 'Concepts')): cur = None; continue
            cur = (re.sub(r'^\d+\.\s*', '', h), []); sections.append(cur)
        elif re.match(r'^### ', l) and cur: cur[1].append(re.sub(r'^[\d.]+\s*', '', l[4:].strip()))
    return sections
def gem_rows(label):
    rows = []
    for tf in glob.glob(f'{ROOT}/planning/gem_books/*_triage.md'):
        book = os.path.basename(tf).replace('_triage.md', '')
        for line in open(tf):
            if line.startswith('| ') and not line.startswith(('| Book', '|---')):
                c = [x.strip() for x in line.strip().strip('|').split('|')]
                if len(c) >= 5 and c[1].startswith(('YES', 'PARTLY')) and label in re.findall(r'\b\d{1,2}\.\d{1,2}\b', c[3]):
                    rows.append((book, c[0], c[1], c[2]))
    return rows
def brief(p, c):
    title, level, srcs = S[p]['ch'][c]; label = f'{p}.{c}'
    doc = read_doc(p, c); prev = [f'{p}.{k} {v[0]}' for k, v in sorted(S[p]['ch'].items()) if k < c][-4:]
    nxt = [f'{p}.{k} {v[0]}' for k, v in sorted(S[p]['ch'].items()) if k > c][:2]
    pre = re.search(r'\*\*Prerequisites:?\*\*(.*?)(?:\n\*\*Outcomes|\n---)', doc, re.S)
    bf = subprocess.run([sys.executable, f'{ROOT}/tools/study_rag/brief.py', label], capture_output=True, text=True).stdout
    heads = re.search(r'SOURCE HEADINGS FOR THIS CHAPTER[^\n]*\n(.*?)\n\nNVIDIA-DEVOPS', bf, re.S)
    files = re.search(r'NVIDIA-DEVOPS FILES[^\n]*\n(.*)', bf, re.S)
    sec = outline(doc)
    o = [f'# NotebookLM brief: chapter {label}, {title}', '',
         f'Part {p}: {S[p]["title"]}. Level: {level}. Source codes in structure.txt: {srcs}.', '',
         '## 1. Where this chapter sits', f'Earlier chapters the reader already knows: {"; ".join(prev) or "none (first chapter of the part)"}.',
         f'Next chapters (do not teach their content here): {"; ".join(nxt) or "none"}.']
    if pre: o += ['', 'Prerequisites stated in the current draft:', pre.group(1).strip()]
    o += ['', '## 2. Outline to follow']
    if sec:
        o += ['(taken from the current draft; keep this order, improve the depth)']
        for i, (h, subs) in enumerate(sec, 1): o.append(f'{i}. {h}' + (' | topics: ' + '; '.join(subs) if subs else ''))
    else:
        o += ['(no draft yet: build the outline from the source headings below, in the order the books teach them)']
    o += ['', '## 3. Sources to use (and only these)', '### Book and manual chapters (headings to cover)', (heads.group(1).strip() if heads else '- none routed')]
    g = gem_rows(label)
    if g:
        o += ['', '### Gem-book chapters that must be fully used here (from the triage tables)']
        o += [f'- {b[:60]}: {ch} ({r}). {why[:160]}' for b, ch, r, why in g]
    o += ['', '### Author notes (nvidia-devops) to read and merge', (files.group(1).strip() if files else '- none')]
    o += ['', '## 4. Prompts, one per section (paste each into the notebook chat, in order)', '']
    sections = sec or [(t, []) for t in ['<section from the source headings>']]
    for i, (h, subs) in enumerate(sections, 1):
        o += [f'### Prompt {i}', '```text',
              f'Write section {i}, "{h}", of chapter {label}, "{title}", of the handbook.',
              f'Use only these sources: see the list below; pick the passages that belong to this section.',
              f'Sources: {(heads.group(1).strip().replace(chr(10), " ")[:700] if heads else "see the notebook sources")}',
              f'The reader already knows: {"; ".join(prev) or "nothing from this book yet"}. Give one sentence of reminder at most, do not re-teach.',
              f'Cover, in this order: {"; ".join(subs) if subs else h}.',
              'Length: about 900 to 1,400 words. Follow the notebook instruction (voice, depth, citations).',
              'After the section list: (a) every number used and its source, (b) every source paragraph, example, script or story in the named chapters that belongs here and that you did NOT use, with a one-line reason.',
              '```', '']
    o += ['## 5. After the last section', '```text',
          f'Compare the sections written for chapter {label} with the named source chapters. List every concept, example, script, story, warning and number in those source chapters that is missing or reduced to one sentence or a table row. Show the missing ones first.',
          '```']
    return '\n'.join(o)
if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == '--part':
        p = int(a[1]); os.makedirs(f'{ROOT}/planning/notebooklm', exist_ok=True)
        for c in sorted(S[p]['ch']):
            open(f'{ROOT}/planning/notebooklm/{p}-{c:02d}.md', 'w').write(brief(p, c) + '\n'); print('wrote', p, c)
    else:
        p, c = map(int, a[0].split('.')); print(brief(p, c))
