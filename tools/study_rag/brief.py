#!/usr/bin/env python3
"""One compact research brief per chapter (saves many tool calls and tokens).
Usage: brief.py 1.6 [--q "search terms" ...] [-n 3] [--chars 350]
Prints: chapter metadata and sources, the source headings that belong to THIS chapter (per routing table), the mapped nvidia-devops files with word counts and migration status, and optional search excerpts."""
import argparse, os, re, sqlite3, subprocess, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ap = argparse.ArgumentParser(); ap.add_argument("label"); ap.add_argument("--q", action="append", default=[]); ap.add_argument("-n", type=int, default=3); ap.add_argument("--chars", type=int, default=350)
a = ap.parse_args(); part, ch = a.label.split(".")
subprocess.run([sys.executable, os.path.join(ROOT, "tools", "coverage", "chapter_cov.py"), a.label], capture_output=True)
# metadata
cur = None
for raw in open(os.path.join(ROOT, "planning", "structure.txt"), encoding="utf-8"):
    l = raw.strip()
    if l.startswith("@PART"): cur = l.split("|")[0].split()[1]; continue
    m = re.match(r"^(\d\d) \| ([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)", l)
    if m and cur and f"{int(cur)}.{int(m.group(1))}" == a.label:
        print(f"CHAPTER {a.label}: {m.group(2).strip()} | level {m.group(3).strip()} | sources: {m.group(4).strip()} | venue {m.group(5).strip() or '-'}"); break
# source headings that belong here
cov = open(os.path.join(ROOT, "planning", "coverage", "chapters", f"{int(part):02d}-{int(ch):02d}.md"), encoding="utf-8").read().split("\n")
group, heads = None, {}
for l in cov:
    mm = re.match(r"^\| \*\*(.*?)\*\*", l)
    if mm: group = mm.group(1); heads[group] = []; continue
    r = re.match(r"^\| (.*?) \| (CHECK|covered|moved|skipped|gap-doc)", l)
    if r and group and r.group(2) in ("CHECK", "covered") and not r.group(1).endswith(": NOTE") and r.group(1) not in ("HLW2: NOTE", "HLW2: WARNING"):
        heads[group].append(re.sub(r"^[A-Z0-9]+: ", "", r.group(1)))
print("\nSOURCE HEADINGS FOR THIS CHAPTER (cover all of these):")
for g, hs in heads.items():
    if hs: print(f"- {g}: " + "; ".join(hs)[:900])
# migration files
mp = open(os.path.join(ROOT, "planning", "MIGRATION_MAP.md"), encoding="utf-8").read().split("\n")
rows = []
for l in mp:
    c = [x.strip() for x in l.strip().strip("|").split("|")]
    if len(c) >= 5 and c[0].endswith(".md") and a.label in [x.strip() for x in c[3].split(",")]:
        rows.append(f"- {c[0]} ({c[1]} words) {('[' + c[4] + ']') if c[4] else '[todo]'}")
print("\nNVIDIA-DEVOPS FILES TO MIGRATE INTO THIS CHAPTER (read and merge):\n" + ("\n".join(rows) if rows else "- none mapped"))
# search excerpts
if a.q:
    db = sqlite3.connect(os.path.expanduser("~/Desktop/books-toon-rag/_index/chunks.db"))
    for q in a.q:
        terms = re.findall(r"[A-Za-z0-9_\-\.]+", q)
        print(f"\nSEARCH '{q}':")
        res = []
        for joiner in (" AND ", " OR "):          # require all terms first, then fall back to any term
            match = joiner.join('"%s"' % t for t in terms)
            res = db.execute("select book, chapter, chunk_id, content from chunks where chunks match ? order by bm25(chunks) limit ?", (match, a.n)).fetchall()
            if res: break
        for book, chap, cid, text in res:
            print(f"- [{book[:28]} | {chap[:40]} | {cid}] " + re.sub(r"\s+", " ", text[:a.chars]))
