import sys, re, json, glob, os
from html.parser import HTMLParser
root = os.path.expanduser("~/Desktop/books-toon-rag")
class T(HTMLParser):
    def __init__(s): super().__init__(); s.t=[]; s.skip=0
    def handle_starttag(s,t,a):
        if t in("script","style"): s.skip+=1
    def handle_endtag(s,t):
        if t in("script","style"): s.skip-=1
    def handle_data(s,d):
        if not s.skip: s.t.append(d)
def words(path):
    p=T(); p.feed(open(path,encoding="utf-8",errors="ignore").read()); return len(" ".join(p.t).split())
for d in sorted(glob.glob(root+"/*/")):
    name=os.path.basename(d.rstrip("/"))
    toon=glob.glob(d+"*.toon"); ch=glob.glob(d+"*_chunks.jsonl")
    if not toon or not ch: print(f"{name}: INCOMPLETE (toon={bool(toon)} chunks={bool(ch)})"); continue
    xs=[f for ext in ("xhtml","html","htm") for f in glob.glob(d+"OEBPS/**/*."+ext,recursive=True)]
    src=sum(words(f) for f in xs)
    t=open(toon[0],encoding="utf-8").read()
    nch=int(re.search(r"chapters\[(\d+)\]",t).group(1))
    twc=sum(int(x) for x in re.findall(r"^\s+word_count: (\d+)",t,re.M))
    rows=[json.loads(l) for l in open(ch[0],encoding="utf-8")]
    gaps=0; last={}
    byc={}
    for r in rows: byc.setdefault(r["chapter_index"],[]).append(r)
    for c,rs in byc.items():
        e=0
        for r in rs:
            if r["start_offset"]>e+1: gaps+=1
            e=max(e,r["end_offset"])
    uniq=sum(r["end_offset"]-r["start_offset"] for r in rows)
    print(f"{name}: xhtml={len(xs)} toon_chapters={nch} src_words={src} toon_words={twc} ({twc/src:.1%}) chunks={len(rows)} chunk_chapters={len(byc)} gaps={gaps} imgs={len(glob.glob(d+'OEBPS/**/Images/*',recursive=True))}")
