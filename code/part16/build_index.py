"""Alias for index_corpus that also prints the metadata row (the chapter's build-index step)."""
import argparse, sys
import index_corpus, mlplat_local as P

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--corpus", required=True); ap.add_argument("--output", default="local"); a = ap.parse_args(argv)
    rc = index_corpus.main(["--corpus", a.corpus])
    if rc == 0: print("index metadata:", P.load("index_meta.json", {}))
    return rc

if __name__ == "__main__": sys.exit(main())
