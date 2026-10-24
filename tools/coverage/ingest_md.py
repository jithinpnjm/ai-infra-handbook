#!/usr/bin/env python3
"""Import the author's nvidia-devops markdown volumes into the study corpus (chunks + heading outlines).
Corpus slugs: nvidia-devops-zth-vNN (zero-to-hero), nvidia-devops-legacy-vNN, nvidia-devops-core-interview."""
import json, os, re, glob

SRC = os.path.expanduser(os.environ.get("NVIDIA_DEVOPS_DOCS", "~/Documents/GitHub/nvidia-devops/docs"))
CORPUS = os.path.expanduser(os.environ.get("STUDY_CORPUS", "~/Desktop/books-toon-rag"))
OUTL = os.path.join(os.path.dirname(__file__), "..", "..", "planning", "source-outlines")
CH = 14000

def front(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    meta, body = {}, text
    if m:
        body = text[m.end():]
        t = re.search(r"^title:\s*[\"']?(.*?)[\"']?\s*$", m.group(1), re.M)
        if t: meta["title"] = t.group(1)
    return meta, body

def collect(slug, root):
    files = sorted(glob.glob(os.path.join(root, "**", "*.md"), recursive=True) + glob.glob(os.path.join(root, "**", "*.mdx"), recursive=True))
    rows, outline, cid = [], [f"# {slug}\n"], 0
    for ci, f in enumerate(files):
        raw = open(f, encoding="utf-8", errors="ignore").read()
        meta, body = front(raw)
        h1 = re.search(r"^#\s+(.*)$", body, re.M)
        title = meta.get("title") or (h1.group(1) if h1 else os.path.basename(f))
        rel = os.path.relpath(f, root)
        outline.append(f"\n## {title}  ({rel})")
        in_code = False
        for line in body.splitlines():
            if line.startswith("```"): in_code = not in_code
            m = re.match(r"^(#{2,4})\s+(.*)$", line)
            if m and not in_code: outline.append("  " * (len(m.group(1)) - 2) + f"- {m.group(2).strip()}")
        parts = re.split(r"\n(?=## )", body); cur = ""
        sections = []
        for p in parts:
            if len(cur) + len(p) > CH and cur: sections.append(cur); cur = p
            else: cur += "\n" + p
        if cur.strip(): sections.append(cur)
        for s in sections:
            for i in range(0, len(s), CH):     # hard-split oversize sections
                piece = s[i:i + CH].strip()
                if piece:
                    rows.append({"content": piece, "token_count": int(len(piece.split()) * 1.3), "start_offset": i, "end_offset": i + len(piece),
                                 "chunk_id": cid, "chapter_index": ci, "chapter_title": title, "chapter_filename": rel, "book_title": slug})
                    cid += 1
    if rows:
        d = os.path.join(CORPUS, slug); os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{slug}_chunks.jsonl"), "w", encoding="utf-8") as fh:
            for r in rows: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        open(os.path.join(OUTL, slug + ".md"), "w").write("\n".join(outline) + "\n")
        print(f"{slug}: {len(files)} files, {len(rows)} chunks")

for v in sorted(glob.glob(os.path.join(SRC, "nvidia-zero-to-hero", "volume-*"))):
    n = re.search(r"volume-(\d+)", v).group(1)
    collect(f"nvidia-devops-zth-v{n}", v)
for v in sorted(glob.glob(os.path.join(SRC, "volume-[0-9]*"))):
    n = re.search(r"volume-(\d+)", v).group(1)
    collect(f"nvidia-devops-legacy-v{n}", v)
collect("nvidia-devops-core-interview", os.path.join(SRC, "core-interview-questions"))
collect("nvidia-devops-intro", os.path.join(SRC, "intro"))
