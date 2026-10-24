#!/usr/bin/env python3
"""Import reference PDFs (vendor guides, specs) into the study corpus as *_chunks.jsonl + outline files.
Usage: ingest_pdfs.py file.pdf [file2.pdf ...]   (private research aid; output stays outside the published site)"""
import json, os, re, subprocess, sys
from pypdf import PdfReader

CORPUS = os.path.expanduser(os.environ.get("STUDY_CORPUS", "~/Desktop/books-toon-rag"))
OUTL = os.path.join(os.path.dirname(__file__), "..", "..", "planning", "source-outlines")
CH = 14000      # chars per chunk (~3.5k tokens)
OV = 800

def slugify(name): return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

def outline_entries(reader):
    out = []
    def walk(items, depth):
        for it in items:
            if isinstance(it, list): walk(it, depth + 1)
            else:
                try: out.append((depth, str(it.title).strip(), reader.get_destination_page_number(it)))
                except Exception: pass
    try: walk(reader.outline, 0)
    except Exception: pass
    return out

def main(path):
    title = os.path.splitext(os.path.basename(path))[0]
    slug = slugify(title)
    txt = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True, check=True).stdout
    pages = txt.split("\f")
    if pages and not pages[-1].strip(): pages.pop()
    reader = PdfReader(path)
    ents = outline_entries(reader)
    top = [(t, p) for d, t, p in ents if d == 0]
    if len(top) < 3: top = [(t, p) for d, t, p in ents if d <= 1]
    if len(top) < 3:   # no usable bookmarks: fixed 25-page sections
        top = [(f"Pages {i+1}-{min(i+25, len(pages))}", i) for i in range(0, len(pages), 25)]
    top.sort(key=lambda x: x[1])
    chapters = []
    for i, (t, p) in enumerate(top):
        end = top[i + 1][1] if i + 1 < len(top) else len(pages)
        chapters.append((t, p, max(end, p + 1)))
    if chapters and chapters[0][1] > 0: chapters.insert(0, ("Front matter", 0, chapters[0][1]))
    d = os.path.join(CORPUS, slug); os.makedirs(d, exist_ok=True)
    cid = 0; rows = []
    for ci, (t, a, b) in enumerate(chapters):
        text = "\n".join(f"[p.{a+k+1}] " + pg.strip() for k, pg in enumerate(pages[a:b])).strip()
        start = 0
        while text and start < len(text):
            end = min(start + CH, len(text))
            chunk = text[start:end].strip()
            if chunk:
                rows.append({"content": chunk, "token_count": int(len(chunk.split()) * 1.3), "start_offset": start, "end_offset": end,
                             "chunk_id": cid, "chapter_index": ci, "chapter_title": t, "chapter_filename": f"pp{a+1}-{b}", "book_title": title})
                cid += 1
            if end >= len(text): break
            start = end - OV
    with open(os.path.join(d, f"{slug}_chunks.jsonl"), "w", encoding="utf-8") as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.makedirs(OUTL, exist_ok=True)
    with open(os.path.join(OUTL, slug + ".md"), "w") as f:
        f.write(f"# {title} ({len(pages)} pages)\n\n")
        for dpt, t, p in ents: f.write("  " * dpt + f"- {t} (p.{p+1})\n")
        if not ents: f.write("(no bookmarks; chunked in 25-page sections)\n")
    print(f"{slug}: {len(pages)} pages, {len(chapters)} sections, {len(rows)} chunks, {len(ents)} bookmarks")

for p in sys.argv[1:]: main(p)
