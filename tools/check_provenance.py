#!/usr/bin/env python3
"""Number-provenance check: does every numeric fact in a chapter appear in its cited sources?
Usage: python3 tools/check_provenance.py 10.7 [--all-hits]
Sources = files named in the chapter's ledger/sources section (nvidia-devops notes, gem books), plus the
chapter's own code (derived numbers).  Numbers found only in OTHER handbook chapters are reported separately."""
import re, sys, glob, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
NOTES = pathlib.Path.home() / "Documents/GitHub/nvidia-devops/docs"
BOOKS = pathlib.Path.home() / "Desktop/books-toon-rag"
ch = sys.argv[1]; P, C = ch.split("."); PP, CC = f"{int(P):02d}", f"{int(C):02d}"
doc = glob.glob(str(ROOT / f"docs/part-{PP}-*/{CC}-*.md"))[0]
text = pathlib.Path(doc).read_text()
ledger = ROOT / f"planning/ledgers/{P}-{CC}.md"
refs = text.split("## Sources and review notes")[-1] + (ledger.read_text() if ledger.exists() else "")

STOP = set("which their there these those would could should about because between through while where other being using across within without under after before every each only over into more most than then them this that with from have been were will also such when what your you can not but and for the are its has had may per via".split())
def words(s): return {w for w in re.findall(r"[a-z][a-z0-9]{4,}", s.lower()) if w not in STOP}
def norm(s): return re.sub(r"(?<=\d),(?=\d{3})", "", s)
# gather source corpus
corpus = []; codecorpus = []
index = {p.name: p for p in NOTES.rglob("*.md")}
for name in set(re.findall(r"[\w\-]+\.md", refs)):
    if name in index: corpus.append(index[name].read_text(errors="ignore"))
for v in set(re.findall(r"[Vv]olume[ -](\d+)", refs)):  # whole volume if only cited generally
    for p in NOTES.rglob(f"volume-{int(v):02d}/**/*.md"):
        corpus.append(p.read_text(errors="ignore"))
for book in [d.name for d in BOOKS.iterdir() if d.is_dir() and d.name in refs]:
    for j in (BOOKS / book).glob("*_chunks.jsonl"):
        corpus += [json.loads(l)["content"] for l in open(j)]
for py in re.findall(r"code/part\d+/[\w]+\.py", text): 
    f = ROOT / py
    if f.exists(): codecorpus.append(f.read_text())
for py in glob.glob(str(ROOT / f"code/part{PP}/*.py")):
    if pathlib.Path(py).stem in text: codecorpus.append(pathlib.Path(py).read_text())
src = norm("\n".join(corpus)); csrc = norm("\n".join(codecorpus)); print(f"source corpus: {len(corpus)} files, {len(src)//1000} KB")
others = norm("\n".join(p.read_text() for p in (ROOT/"docs").rglob("*.md") if str(p) != doc))

body = re.sub(r"```.*?```", "", text.split("## Sources and review notes")[0], flags=re.S)
body = re.sub(r"^---\n.*?\n---\n", "", body, flags=re.S)
TOK = re.compile(r"(?<![\w.-])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s?(%|×|x\b|kW|MW|W\b|GB/s|TB/s|GB|TB|MB|ms|µs|μs|Gbps|TFLOPS|PFLOPS|EFLOPS|exaFLOPS|CFM|GT/s|bytes|MHz|GHz|°C|seconds?|secs?|minutes?|hours?|days?|weeks?)?")
codeonly = set(); seen = {}; HEX = re.compile(r'0x[0-9A-Fa-f]{1,16}')

for ln, line in enumerate(body.split("\n"), 1):
    if re.match(r"\s*#{1,6} ", line) or line.lstrip().startswith("<summary>") and False: pass
    for hm in HEX.finditer(line):
        h = hm.group(0).lower().lstrip('0x').lstrip('0') or '0'
        if len(h) < 1: continue
        key = ('hex', h)
        if key in seen: continue
        hp = r'0x0*' + re.escape(h) + r'\b'
        hits = list(re.finditer(hp, src, re.I)); sw = words(line)
        best = max((len(sw & words(src[max(0, x.start()-220):x.end()+220])) for x in hits), default=-1)
        if best < 0 and re.search(hp, csrc, re.I): codeonly.add(key)
        seen[key] = (ln, hm.group(0), line.strip()[:150], best >= 0, best)
    for m in TOK.finditer(line):
        num, unit = norm(m.group(1)), m.group(2) or ""
        raw = m.group(0).strip()
        if not unit and (len(num.replace(".", "")) < 3 or re.fullmatch(r"(19|20)\d\d", num)): continue   # small ints/years
        if re.search(r"(Chapter|Ch|Section|Fig|§|V\d|Volume|Part)\.?\s*$", line[:m.start()].rstrip("` ") ): continue
        if unit == "" and re.search(r"\d+\.\d+$", num) and len(num) <= 4 and not "." in num[-1]: pass
        key = (num, unit)
        if key in seen: continue
        pat = re.escape(num) + (r"\s?(%|percent)" if unit == "%" else r"\s?(×|x)" if unit in ("×", "x") else "")
        hits = list(re.finditer(r"(?<![\d.])" + pat + r"(?![\d])", src))
        sw = words(line)
        best = max((len(sw & words(src[max(0, h.start()-220):h.end()+220])) for h in hits), default=-1)
        if best < 0 and re.search(r"(?<![\d.])" + pat + r"(?![\d])", csrc): codeonly.add(key)
        seen[key] = (ln, raw, line.strip()[:150], best >= 0, best)
miss = [(k, v) for k, v in seen.items() if not v[3]]
weak = [(k, v) for k, v in seen.items() if v[3] and v[4] < 3]
derived = [(k, v) for k, v in miss if k not in codeonly and re.search(r"(?<![\d.])" + re.escape(k[0]) + r"(?![\d])", others)]
rest = [(k, v) for k, v in miss if (k, v) not in derived and k not in codeonly]
conly = [(k, v) for k, v in miss if k in codeonly]
print(f"numeric facts checked: {len(seen)}; found in cited sources/code: {len(seen)-len(miss)}; "
      f"only in other handbook chapters: {len(derived)}; NOT FOUND ANYWHERE CITED: {len(rest)}\n")
print(f"numbers found ONLY in the chapter's own lab code (fine if arithmetic the lab computes; SUSPICIOUS if a fact like a hex value, spec or price): {len(conly)}")
for k, (ln, raw, ctx, *_) in conly: print(f"  L{ln}: {raw!r:14} | {ctx}")
print("\n== NOT FOUND in cited sources, code, or other chapters (highest risk) ==")
for k, (ln, raw, ctx, *_) in rest: print(f"  L{ln}: {raw!r:14} | {ctx}")
print(f"\n== number exists in sources but with a DIFFERENT context (check for drift): {len(weak)} ==")
for k, (ln, raw, ctx, ok, best) in weak: print(f"  L{ln}: {raw!r:14} ctx-match={best} | {ctx}")
if "--all-hits" in sys.argv:
    print("\n== only in other handbook chapters (check they are cross-refs) ==")
    for k, (ln, raw, ctx, *_) in derived: print(f"  L{ln}: {raw!r:14} | {ctx}")
