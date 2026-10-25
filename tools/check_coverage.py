#!/usr/bin/env python3
"""Source-coverage check: did the chapter use the sources that exist for its topic?
Usage: python3 tools/check_coverage.py 10.8 [--q "extra terms"]
Reports (1) nvidia-devops files mapped to this chapter but never cited, (2) gem books the corpus search
ranks as relevant to the chapter title/terms but the chapter never cites, (3) whether the ledger records
a 'Corpus search' section (queries run and what was found)."""
import re, sys, glob, sqlite3, pathlib, collections, os
ROOT = pathlib.Path(__file__).resolve().parents[1]
label = sys.argv[1]; P, C = label.split("."); PP, CC = f"{int(P):02d}", f"{int(C):02d}"
extra = [sys.argv[i+1] for i, a in enumerate(sys.argv) if a == "--q" and i+1 < len(sys.argv)]
doc = glob.glob(str(ROOT / f"docs/part-{PP}-*/{CC}-*.md"))[0]; text = open(doc).read()
ledger = ROOT / f"planning/ledgers/{P}-{CC}.md"; led = ledger.read_text() if ledger.exists() else ""
refs = text.split("## Sources and review notes")[-1] + led + text[:text.find("## ")]
title = re.search(r'^title: "(.*)"', text, re.M).group(1)
# (1) mapped notes
rows = []
for l in open(ROOT / "planning/MIGRATION_MAP.md"):
    c = [x.strip() for x in l.strip().strip("|").split("|")]
    if len(c) >= 4 and c[0].endswith(".md") and label in [x.strip() for x in c[3].split(",")]: rows.append(c[0])
def cited(path):
    """Strict: file name, or an explicit 'V<v> Ch/Chapter/Lab <n>' / 'Volume <v> ... Chapter <n>' reference, or a range 'Ch a-b' that includes n."""
    base = os.path.basename(path)
    if base in refs or base[:-3] in refs: return True
    m = re.search(r"volume-(\d+)/(?:labs/)?(chapter-(\d+)|lab-(\d+))", path)
    if not m: return False
    v = int(m.group(1)); n = int(m.group(3) or m.group(4)); kind = "Ch(?:apter)?" if m.group(3) else "Lab"
    if re.search(rf"volume-0?{v}/(?:labs/)?(?:chapter|lab)-0?{n}\b", refs): return True
    for mm in re.finditer(rf"(?:V|Volume[ -]?)0?{v}\b[^\n]{{0,60}}?\b{kind}s?\.?\s*0?(\d+)(?:\s*[–-]\s*0?(\d+))?", refs):
        lo = int(mm.group(1)); hi = int(mm.group(2) or lo)
        if lo <= n <= hi: return True
    return False
miss = [r for r in rows if not cited(r)]
print(f"[1] mapped nvidia-devops files: {len(rows)}; cited: {len(rows)-len(miss)}; NOT cited: {len(miss)}")
for r in miss: print("    not cited:", r)
# (2) relevant books: one query for the title and one for each H2 heading, scores added up (rank-weighted)
STOP = set("and the for with from into that this your what when how why are using use plus versus vs per".split())
def tq(s): return [w for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]{3,}", s) if w.lower() not in STOP]
heads = re.findall(r"^## (?:\d+\.\s*)?(.+)$", text, re.M)
skip = ("Why this matters", "Prerequisites", "Commands and", "How it fails", "How It Fails", "Hands-on", "Hands-On", "Exercises", "Checkpoint", "Sources")
queries = [tq(title + " " + " ".join(extra))] + [tq(h) for h in heads if not h.startswith(skip)][:8]
db = sqlite3.connect(os.path.expanduser("~/Desktop/books-toon-rag/_index/chunks.db"))
score = collections.Counter(); chaps = collections.defaultdict(collections.Counter)
for terms in queries:
    if len(terms) < 2: continue
    match = " OR ".join('"%s"' % w for w in terms)
    for rank, (b, c) in enumerate(db.execute("select book, chapter from chunks where chunks match ? order by bm25(chunks) limit 25", (match,)).fetchall()):
        if b.startswith("nvidia-devops"): continue          # the author's notes: covered by the mapping check
        score[b] += 1 + (25 - rank) / 25; chaps[b][c[:50]] += 1
books = score.most_common(8)
print(f"\n[2] {len(queries)} corpus queries (title + section headings)")
print("    book relevance (CITED / recorded-in-ledger / UNRECORDED), score, best chapters:")
unc = 0
for b, s in books:
    ok = b in refs
    rec = ok or (b in led) or (b in text)
    flag = (not rec) and s >= 3.0
    unc += flag
    print(f"    {'CITED   ' if ok else ('recorded' if rec else ('UNRECORDED' if flag else 'low     '))} {b[:48]:48} {s:5.1f}  {', '.join(k for k, _ in chaps[b].most_common(2))}")
print(f"    unrecorded relevant books (score>=3): {unc}   (read them; then cite them or record 'read, nothing new' in the ledger Corpus search)")
# (3) ledger
has = bool(re.search(r"corpus search", led, re.I))
print(f"\n[3] ledger has a 'Corpus search' section: {'yes' if has else 'NO (add queries run + top books found, even if nothing useful)'}")
print("\nVERDICT:", "OK" if not miss and unc == 0 and has else "REVIEW: " + ", ".join(
    x for x, bad in [("mapped notes uncited", miss), ("relevant books uncited", unc), ("no corpus-search record", not has)] if bad))
