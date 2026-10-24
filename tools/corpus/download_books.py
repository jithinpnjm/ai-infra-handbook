import sys, glob, os
sys.path.insert(0, "/Users/jithinpjoseph/oreilly-downloader")
os.chdir("/Users/jithinpjoseph/oreilly-downloader")
from pathlib import Path
from core import create_default_kernel
ids = sys.argv[1:] or sorted({open(f).read().strip() for f in glob.glob("output/*/.book_id")})
dest = Path("/Users/jithinpjoseph/Desktop/books-toon-rag")
k = create_default_kernel()
import threading, time
def _reload():
    while True:
        time.sleep(20)
        try: k["auth"] and k.http.reload_cookies()
        except Exception as e: print("reload err", e, flush=True)
threading.Thread(target=_reload, daemon=True).start()
print("auth:", k["auth"].__class__.__name__, flush=True)
fail = 0
import glob as _g, shutil
for b in ids:
    done=[d for d in _g.glob(str(dest)+'/*/') if os.path.exists(d+'.book_id') and open(d+'.book_id').read().strip()==b and _g.glob(d+'*_chunks.jsonl') and _g.glob(d+'*.toon')]
    if done:
        print('SKIP (done)', b, flush=True); continue
    for d in _g.glob(str(dest)+'/*/'):
        if os.path.exists(d+'.book_id') and open(d+'.book_id').read().strip()==b: shutil.rmtree(d)
    print('START', b, flush=True)
    for attempt in range(40):
        try:
            r = k["downloader"].download(book_id=b, output_dir=dest, formats=["toon", "chunks"])
            print("OK", r.title, flush=True)
            break
        except Exception as e:
            print("RETRY", b, attempt, str(e)[:150], flush=True)
            time.sleep(45)
            for d in _g.glob(str(dest)+'/*/'):
                if os.path.exists(d+'.book_id') and open(d+'.book_id').read().strip()==b and not (_g.glob(d+'*.toon') and _g.glob(d+'*_chunks.jsonl')): shutil.rmtree(d)
    else:
        fail += 1
        print("FAIL", b, flush=True)
print("done, failures:", fail)
