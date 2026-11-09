"""Index a corpus (directory of .txt files) into the local vector index and print a snapshot id."""
import argparse, hashlib, sys
from pathlib import Path
import mlplat_local as P

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--corpus", required=True); ap.add_argument("--embedding-model", default="bow-v1")
    ap.add_argument("--output-milvus", default="local"); a = ap.parse_args(argv)
    if "://" in a.corpus: print("only a local directory runs offline"); return 2
    docs = {f.name: f.read_text() for f in sorted(Path(a.corpus).glob("*.txt"))}
    snap = hashlib.sha256("".join(k + v for k, v in docs.items()).encode()).hexdigest()[:12]
    P.save(f"index_{snap}.json", {"model": a.embedding_model, "docs": {k: {"text": v, "vec": P.embed(v)} for k, v in docs.items()}})
    meta = P.load("index_meta.json", {}); meta[snap] = {"n_docs": len(docs), "corpus": a.corpus, "model": a.embedding_model}; P.save("index_meta.json", meta)
    print(f"snapshot {snap} ({len(docs)} docs)"); return 0

if __name__ == "__main__": sys.exit(main())
