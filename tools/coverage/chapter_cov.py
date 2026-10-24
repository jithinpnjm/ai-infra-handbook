#!/usr/bin/env python3
"""Check a written chapter against the section headings of the source chapters it cites.
Usage: chapter_cov.py 1.1   -> writes planning/coverage/chapters/01-01.md  (auto status: covered / CHECK)
A heading is 'covered' when >=60% of its significant words appear in the chapter text. CHECK rows need a human decision:
add content, mark moved (to a named chapter) or skipped (with a reason) by editing the generated file's Note column and re-running keeps notes."""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
exec(open(os.path.join(os.path.dirname(__file__), "map_sources.py")).read().split("def expand")[0].split("CODES =")[0])  # imports only
src = open(os.path.join(os.path.dirname(__file__), "map_sources.py")).read()
CODES = eval(re.search(r"CODES = (\{.*?\})\nSKIP", src, re.S).group(1))
STOP = set("the and for with from that this into your are how what when why you not use using about their they them have has can will its our out all any more than then also over under into between".split())

def expand(txt):
    out = set()
    for part in re.split(r"\s*,\s*", txt):
        m = re.match(r"^(\d+)-(\d+)$", part)
        if m: out.update(range(int(m.group(1)), int(m.group(2)) + 1))
        elif part.isdigit(): out.add(int(part))
    return out

def find(label):
    part = None
    for raw in open(os.path.join(ROOT, "planning", "structure.txt"), encoding="utf-8"):
        line = raw.strip()
        if line.startswith("@PART"): part = line.split("|")[0].split()[1]; continue
        m = re.match(r"^(\d\d) \| ([^|]*)\|[^|]*\| ([^|]*)", line)
        if m and f"{int(part)}.{int(m.group(1))}" == label: return part, m.group(1), m.group(2).strip(), m.group(3)
    sys.exit("chapter not found")

def chapter_text(part, num):
    for f in glob.glob(os.path.join(ROOT, "docs", f"part-{part}-*", f"{num}-*.md")): return open(f, encoding="utf-8").read().lower()
    sys.exit("chapter file missing")

def source_headings(slug, numbers):
    toon = glob.glob(os.path.expanduser(f"~/Desktop/books-toon-rag/{slug}/*.toon"))
    outline = open(os.path.join(ROOT, "planning", "source-outlines", slug + ".md"), encoding="utf-8").read()
    blocks = dict(zip(re.findall(r"<!-- file: (.*?) -->", outline), re.split(r"<!-- file: .*? -->", outline)[1:]))
    res = {}
    if not toon: return res
    for blk in re.split(r"\n  - index: ", open(toon[0], encoding="utf-8").read())[1:]:
        tt = re.search(r"\n    title: (.*)", blk); fn = re.search(r"\n    filename: (.*)", blk)
        if not tt or not fn: continue
        t = tt.group(1).strip().strip('"'); m = re.match(r"^(?:chapter|ch\.?)?\s*(\d+)(?:[\.\:\s\-]|$)", t, re.I)
        if m and int(m.group(1)) in numbers:
            body = blocks.get(os.path.basename(fn.group(1).strip()), "")
            res[int(m.group(1))] = (t, [re.sub(r"\s+", " ", l.strip()[2:]) for l in body.splitlines() if re.match(r"^\s*- ", l)])
    return res

def words(s):
    s = re.sub(r"^\s*\d+(\.\d+)*\.?\s+", "", s)
    return {w for w in re.findall(r"[a-z0-9\-\+/\.]{4,}", s.lower()) if w not in STOP}

label = sys.argv[1]; part, num, title, srcs = find(label); text = chapter_text(part, num)
outp = os.path.join(ROOT, "planning", "coverage", "chapters", f"{part}-{num}.md")
old = {}
if os.path.exists(outp):
    for l in open(outp, encoding="utf-8"):
        m = re.match(r"^\| (.*?) \| (CHECK|covered|moved|skipped|gap-doc).*? \| (.*?) \|$", l)
        if m and m.group(3).strip(): old[m.group(1)] = (m.group(2), m.group(3))
routes = []
rp = os.path.join(ROOT, "planning", "coverage", "routing.txt")
if os.path.exists(rp):
    for l in open(rp, encoding="utf-8"):
        if l.startswith("#") or l.count("|") < 3: continue
        parts = [x.strip() for x in l.strip().split(" | ")]
        if len(parts) >= 4: routes.append((parts[0], parts[1], parts[2], parts[3]))
rows, miss, tot = [], 0, 0
for code, slug in CODES.items():
    for mm in re.finditer(rf"\b{code}\s+((?:\d+(?:-\d+)?)(?:\s*,\s*\d+(?:-\d+)?)*)", srcs):
        nums = expand(mm.group(1))
        for n, (t, heads) in sorted(source_headings(slug, nums).items()):
            rows.append(f"| **{code} {n}: {t[:60]}** | | |")
            for h in heads:
                tot += 1; w = words(h); hit = (len(w & words(text)) / len(w)) if w else 1
                key = f"{code}{n}: {h[:70]}"
                if key in old: st, note = old[key]
                else:
                    st, note = ("covered" if hit >= 0.6 else "CHECK"), ""
                    for rcode, rx, tgt, rnote in routes:
                        if rcode == f"{code}{n}" and re.search(rx, h):
                            if tgt == "skip": st, note = "skipped", rnote
                            elif tgt == label: st, note = ("covered" if hit >= 0.6 else "CHECK"), ""
                            else: st, note = "moved", f"{tgt} {rnote}"
                            break
                if st == "CHECK": miss += 1
                rows.append(f"| {key} | {st} | {note} |")
open(outp, "w", encoding="utf-8").write(f"# Coverage: {label} {title}\n\nAuto-checked against source headings by tools/coverage/chapter_cov.py. Edit the status of CHECK rows to `moved` (name chapter), `skipped` (reason) or `gap-doc`, add content, then rerun; notes are kept.\n\n| Source heading | Status | Note |\n|---|---|---|\n" + "\n".join(rows) + f"\n\nRows: {tot}, needing a decision: {miss}\n")
print(f"{label}: {tot} source headings, {miss} need a decision -> {os.path.relpath(outp, ROOT)}")
