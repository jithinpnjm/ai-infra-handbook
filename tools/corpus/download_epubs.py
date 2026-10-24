#!/usr/bin/env python3
"""Download EPUBs for every O'Reilly book in the corpus that is not already in ~/Desktop/epubs.
Usage: download_epubs.py [--dry-run]   (run with ~/oreilly-downloader/.venv/bin/python; keep cookies fresh as for download_books.py)"""
import glob, os, re, shutil, sys, threading, time
sys.path.insert(0, os.path.expanduser("~/oreilly-downloader")); os.chdir(os.path.expanduser("~/oreilly-downloader"))
from pathlib import Path

CORPUS = os.path.expanduser("~/Desktop/books-toon-rag"); EPUBS = Path(os.path.expanduser("~/Desktop/epubs"))
STAGE = Path(os.path.expanduser("~/oreilly-downloader/output-epub-staging"))
norm = lambda s: re.sub(r"[^a-z0-9]+", "", s.lower())

have = {norm(p.stem) for p in EPUBS.glob("*.epub")}
todo = []
for d in sorted(glob.glob(CORPUS + "/*/")):
    bid = os.path.join(d, ".book_id")
    toon = glob.glob(d + "*.toon")
    if not os.path.exists(bid) or not toon: continue
    title = re.search(r"title: (.*)", open(toon[0], encoding="utf-8").read(2000)).group(1).strip('"')
    key = norm(title)
    if any(key in h or h in key or key[:40] == h[:40] for h in have): continue
    todo.append((open(bid).read().strip(), title))
print(f"{len(todo)} missing from {EPUBS}:"); [print(f"  {b}  {t}") for b, t in todo]
if "--dry-run" in sys.argv: sys.exit(0)

from core import create_default_kernel
k = create_default_kernel()
def reload():
    while True:
        time.sleep(20)
        try: k.http.reload_cookies()
        except Exception as e: print("reload err", e, flush=True)
threading.Thread(target=reload, daemon=True).start()
STAGE.mkdir(exist_ok=True); fail = 0
for bid, title in todo:
    for attempt in range(40):
        try:
            r = k["downloader"].download(book_id=bid, output_dir=STAGE, formats=["epub"])
            src = r.files.get("epub")
            if src and os.path.exists(src):
                shutil.copy2(src, EPUBS / os.path.basename(src)); print("OK", title, "->", os.path.basename(src), flush=True); break
            raise RuntimeError("no epub in result")
        except Exception as e:
            print("RETRY", bid, attempt, str(e)[:120], flush=True); time.sleep(45)
    else:
        fail += 1; print("FAIL", bid, title, flush=True)
print("done, failures:", fail)
