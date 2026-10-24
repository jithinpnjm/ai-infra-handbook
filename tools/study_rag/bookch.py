#!/usr/bin/env python3
"""Print the full text of one book chapter from the local book corpus.
Usage: bookch.py <book-folder-name> "<chapter title prefix>" [> out.txt]
Examples: bookch.py bcm11-admin "7 "      (Administrator Manual chapter 7)
          bookch.py bcm11-containerization "B "   (appendix B)
List a book's chapter titles: bookch.py bcm11-admin --list
Corpus: ~/Desktop/books-toon-rag/<book>/*_chunks.jsonl"""
import glob, json, os, sys
book = sys.argv[1]
f = glob.glob(os.path.expanduser(f"~/Desktop/books-toon-rag/{book}/*_chunks.jsonl"))[0]
rows = [json.loads(l) for l in open(f, encoding="utf-8")]
if sys.argv[2] == "--list":
    seen = []
    for r in rows:
        if r["chapter_title"] not in seen:
            seen.append(r["chapter_title"])
    print("\n".join(seen))
else:
    for r in rows:
        if r["chapter_title"].startswith(sys.argv[2]):
            print(r["content"])
