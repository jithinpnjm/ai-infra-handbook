#!/usr/bin/env python3
"""Generate the book scaffold from planning/structure.txt.
Creates docs/part-NN-slug/_category_.json and NN-slug.md per chapter, docs/index.md, planning/STRUCTURE.md and planning/STATUS.md.
Never overwrites a chapter whose frontmatter status is not 'scaffold' (written work is safe). Run: python3 tools/scaffold/generate.py"""
import json, os, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
STRUCT = os.path.join(ROOT, "planning", "structure.txt")
DOCS = os.path.join(ROOT, "docs")
VENUE = {"M": "Mac", "G": "GCP / GKE", "N": "Nebius GPU", "-": "none (design / reading)", "": "Mac or GCP"}
LEVEL = {"B": "Basics", "I": "Intermediate", "A": "Advanced", "all": "All levels"}

def slugify(t):
    t = t.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:70].strip("-")

def parse():
    parts, cur = [], None
    for raw in open(STRUCT, encoding="utf-8"):
        line = raw.rstrip("\n")
        if not line.strip() or line.startswith("#"): continue
        f = [x.strip() for x in line.split("|")]
        if f[0].startswith("@PART"):
            cur = {"num": f[0].split()[1], "slug": f[1], "title": f[2], "tier": f[3], "venue": f[4], "chapters": []}
            parts.append(cur)
        else:
            f += [""] * (6 - len(f))
            cur["chapters"].append({"num": f[0], "title": f[1], "level": f[2], "sources": f[3], "venue": f[4] or cur["venue"], "tier": f[5] or cur["tier"]})
    return parts

def lvl(code):
    return " → ".join(LEVEL.get(c.strip(), c.strip()) for c in re.split(r"→|-", code)) if code else ""

def write_chapter(part, ch):
    pdir = os.path.join(DOCS, f"part-{part['num']}-{part['slug']}")
    os.makedirs(pdir, exist_ok=True)
    fname = f"{ch['num']}-{slugify(ch['title'])}.md"
    path = os.path.join(pdir, fname)
    label = f"{int(part['num'])}.{int(ch['num'])}"
    ch["label"], ch["path"] = label, os.path.relpath(path, ROOT)
    if os.path.exists(path):
        head = open(path, encoding="utf-8").read(600)
        if not re.search(r'status:\s*"?scaffold"?', head): return "kept"
    cov = f"planning/coverage/chapters/{part['num']}-{ch['num']}.md"
    fm = {"id": f"c{part['num']}-{ch['num']}", "title": f"{label} {ch['title']}", "sidebar_label": f"{label} {ch['title']}",
          "sidebar_position": int(ch["num"]), "description": ch["title"], "status": "scaffold", "tier": ch["tier"],
          "level": ch["level"], "lab_venue": VENUE.get(ch["venue"], ch["venue"])}
    body = ["---"] + [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in fm.items()] + ["---", "",
        f"# {label} {ch['title']}", "",
        ":::caution Scaffold only",
        "This chapter has not been written yet. Do not treat any heading below as content. See `planning/PROJECT_MAP.md` and `planning/HANDOFF_PROMPT.md` for how to write it.",
        ":::", "",
        "| | |", "|---|---|",
        f"| Level | {lvl(ch['level'])} |", f"| Priority tier | {ch['tier']} |", f"| Lab venue | {VENUE.get(ch['venue'], ch['venue'])} |",
        f"| Part | {part['title']} |", f"| Sources to use | {ch['sources'] or 'to be assigned'} |",
        f"| Coverage file | `{cov}` (create before writing) |", "",
        "## Why this matters for AI infrastructure", "", "TODO", "",
        "## Prerequisites and outcomes", "", "TODO", "",
        "## Concepts: basics → intermediate → advanced", "", "TODO (large Mermaid mental-model diagrams)", "",
        "## Commands and configurations that matter", "", "TODO", "",
        "## How it fails", "", "TODO (4 to 6 failure modes: symptom, diagnosis, fix)", "",
        "## Hands-on lab", "", "TODO (state the venue, expected output; mark `untested` until run)", "",
        "## Checkpoint questions", "", "TODO (8 to 12 questions with answers)", "",
        "## Sources and further reading", "", "TODO (credit sources; flag facts to verify)", ""]
    open(path, "w", encoding="utf-8").write("\n".join(body))
    return "new"

def main():
    parts = parse()
    counts = {"new": 0, "kept": 0, "removed": 0}
    for p in parts:
        pdir = os.path.join(DOCS, f"part-{p['num']}-{p['slug']}")
        os.makedirs(pdir, exist_ok=True)
        expected = {f"{c['num']}-{slugify(c['title'])}.md" for c in p["chapters"]}
        for old in os.listdir(pdir):                      # remove scaffolds that are no longer in structure.txt
            if old.endswith(".md") and old not in expected:
                op = os.path.join(pdir, old)
                if re.search(r'status:\s*"?scaffold"?', open(op, encoding="utf-8").read(600)):
                    os.remove(op); counts["removed"] = counts.get("removed", 0) + 1
                else:
                    print("WARNING: written chapter not in structure.txt, left in place:", op)
        cat = {"label": p["title"], "position": int(p["num"]) + 1,
               "link": {"type": "generated-index", "description": f"{len(p['chapters'])} chapters. Default priority tier {p['tier']}."}}
        json.dump(cat, open(os.path.join(pdir, "_category_.json"), "w"), indent=2)
        for ch in p["chapters"]: counts[write_chapter(p, ch)] += 1
    total = sum(len(p["chapters"]) for p in parts)
    # docs/index.md
    idx = ["---", "id: index", "slug: /", "title: AI Infrastructure Handbook", "sidebar_label: Start here", "---", "",
           "# AI Infrastructure Handbook", "",
           "One book from Linux and networking basics to senior-level AI infrastructure: HPC and Slurm, Kubernetes with GPUs, BCM and Redfish, NVIDIA reference architectures, AI networking, distributed training, inference, MLOps and operations.", "",
           f"**{total} chapters in {len(parts)} parts.** Chapters marked *scaffold* are not written yet; progress is tracked in `planning/STATUS.md`.", "",
           "| Part | Chapters | Default tier |", "|---|---|---|"]
    idx += [f"| {p['title']} | {len(p['chapters'])} | {p['tier']} |" for p in parts]
    open(os.path.join(DOCS, "index.md"), "w").write("\n".join(idx) + "\n")
    # STRUCTURE.md and STATUS.md
    st = ["# Book structure (generated from planning/structure.txt; do not edit by hand)", "",
          f"{total} chapters in {len(parts)} parts. Chapter ids are part.chapter (for example 6.12 = Part 6, chapter 12). This file supersedes the numbering used in earlier CURRICULUM_MAP revisions.", ""]
    for p in parts:
        st += [f"## {p['title']}  (tier {p['tier']}, {len(p['chapters'])} chapters)", "", "| # | Chapter | Level | Tier | Sources |", "|---|---|---|---|---|"]
        st += [f"| {c['label']} | {c['title']} | {c['level']} | {c['tier']} | {c['sources']} |" for c in p["chapters"]] + [""]
    open(os.path.join(ROOT, "planning", "STRUCTURE.md"), "w").write("\n".join(st))
    ss = ["# Status tracker (regenerate the skeleton with tools/scaffold/generate.py; update Status by hand or script)", "",
          "Legend: scaffold · outline · drafted (labs untested) · reviewed · done", "",
          "Legacy pilot drafts (superseded, kept as reference for the rewrite): `planning/pilots/` (2.5 Linux networking toolbox, 7.1 GPU architecture, 8.3 InfiniBand). Rebuild as series 2.17-2.21, 10.01-10.10 and 12.06-12.09.", ""]
    notes = {}
    if os.path.exists(os.path.join(ROOT, "planning", "status_notes.json")):
        notes = json.load(open(os.path.join(ROOT, "planning", "status_notes.json")))
    def state(c):
        txt = open(os.path.join(ROOT, c["path"]), encoding="utf-8").read()
        m = re.search(r'^status:\s*"?([^"\n]+)"?', txt, re.M)
        words = len(txt.split()) if (m and m.group(1) != "scaffold") else ""
        return (m.group(1) if m else "scaffold"), words
    tier_names = {"0": "Tier 0: foundations (write first, everything builds on these)", "1": "Tier 1: interview- and job-critical", "1b": "Tier 1b: NVIDIA platform operations", "2": "Tier 2: senior-loop depth", "3": "Tier 3: breadth"}
    for tier in ("0", "1", "1b", "2", "3"):
        rows = [(p, c) for p in parts for c in p["chapters"] if c["tier"] == tier]
        ss += [f"## {tier_names[tier]}: {len(rows)} chapters", "", "| # | Chapter | Status | Words | Notes |", "|---|---|---|---|---|"]
        for p, c in rows:
            stt, w = state(c)
            ss.append(f"| {c['label']} | {c['title']} | {stt} | {w} | {notes.get(c['label'], '')} |")
        ss.append("")
    open(os.path.join(ROOT, "planning", "STATUS.md"), "w").write("\n".join(ss))
    print(f"{len(parts)} parts, {total} chapters; created {counts['new']}, kept {counts['kept']}, removed stale {counts['removed']}")

main()
