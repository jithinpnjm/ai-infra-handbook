#!/usr/bin/env python3
"""Build a local SQLite FTS5 index over *_chunks.jsonl book exports. Data stays outside the repo."""
import glob, json, os, sqlite3, sys

CORPUS = os.path.expanduser(os.environ.get("STUDY_CORPUS", "~/Desktop/books-toon-rag"))
DB = os.path.join(CORPUS, "_index", "chunks.db")

os.makedirs(os.path.dirname(DB), exist_ok=True)
if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.execute("CREATE VIRTUAL TABLE chunks USING fts5(content, book UNINDEXED, chapter UNINDEXED, chunk_id UNINDEXED, tokenize='porter unicode61')")
n = 0
for path in sorted(glob.glob(os.path.join(CORPUS, "*", "*_chunks.jsonl"))):
    slug = os.path.basename(os.path.dirname(path))
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f]
    con.executemany(
        "INSERT INTO chunks VALUES (?,?,?,?)",
        [(r["content"], r.get("book_title") or slug, r.get("chapter_title", ""), r["chunk_id"]) for r in rows],
    )
    n += len(rows)
    print(f"{slug}: {len(rows)} chunks")
con.commit()
print(f"indexed {n} chunks -> {DB}")
