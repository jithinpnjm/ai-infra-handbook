#!/usr/bin/env python3
"""Search the local book index. Usage: query.py "infiniband subnet manager" [-n 8] [--book SUBSTR] [--full]"""
import argparse, os, re, sqlite3

DB = os.path.join(os.path.expanduser(os.environ.get("STUDY_CORPUS", "~/Desktop/books-toon-rag")), "_index", "chunks.db")
ap = argparse.ArgumentParser()
ap.add_argument("query"); ap.add_argument("-n", type=int, default=8)
ap.add_argument("--book", default=""); ap.add_argument("--full", action="store_true")
a = ap.parse_args()
terms = re.findall(r"[A-Za-z0-9_\-\.]+", a.query)
match = " OR ".join('"%s"' % t for t in terms)
sql = "SELECT book, chapter, chunk_id, content, bm25(chunks) s FROM chunks WHERE chunks MATCH ?"
args = [match]
if a.book:
    sql += " AND book LIKE ?"; args.append(f"%{a.book}%")
sql += " ORDER BY s LIMIT ?"; args.append(a.n)
for book, ch, cid, text, s in sqlite3.connect(DB).execute(sql, args):
    print(f"[{book} | {ch} | chunk {cid}]")
    print(text if a.full else text[:400].replace("\n", " ") + " ...")
    print()
