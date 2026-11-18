#!/usr/bin/env python3
"""Build an EPUB for one part of the handbook.  Usage: python3 tools/epub/build_epub.py 9"""
import re, sys, glob, subprocess, hashlib, shutil, pathlib, textwrap
ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
part = int(sys.argv[1]) if len(sys.argv) > 1 else 9
pdir = glob.glob(str(ROOT / f"docs/part-{part:02d}-*"))[0]
pname = pathlib.Path(pdir).name
OUT = ROOT / "build-epub"; WORK = OUT / f"work-part-{part:02d}"
shutil.rmtree(WORK, ignore_errors=True); (WORK / "img").mkdir(parents=True)
MMDC = HERE / "node_modules/.bin/mmdc"

def front(t):
    m = re.match(r"---\n(.*?)\n---\n", t, re.S)
    meta = dict(re.findall(r'^(\w+):\s*"?(.*?)"?\s*$', m.group(1), re.M)) if m else {}
    return meta, t[m.end():] if m else t

def render_mermaid(code):
    h = hashlib.md5(code.encode()).hexdigest()[:10]
    png = WORK / "img" / f"d{h}.png"
    if not png.exists():
        src = WORK / f"{h}.mmd"; src.write_text(code)
        r = subprocess.run([str(MMDC), "-p", str(HERE/"puppeteer.json"), "-c", str(HERE/"mermaid.json"),
                            "-i", str(src), "-o", str(png), "-s", "2", "-b", "white"], capture_output=True, text=True)
        if r.returncode: print("mermaid failed:", r.stderr[-300:]); return None
    return f"img/{png.name}"

def convert(t):
    # mermaid -> png
    def mm(m):
        p = render_mermaid(m.group(1))
        return f"\n\n![Diagram]({p})\n\n" if p else m.group(0)
    t = re.sub(r"```mermaid\n(.*?)```", mm, t, flags=re.S)
    # admonitions
    def adm_open(m):
        kind = m.group(1); title = (m.group(2) or {"tip":"Tip","note":"Note","info":"Info","caution":"Caution","warning":"Warning","danger":"Danger"}.get(m.group(1), m.group(1))).strip()
        return f'<div class="callout {kind}">\n\n<p class="ctitle">{title}</p>\n\n'
    out = []; in_adm = False; fence = False
    for line in t.split("\n"):
        if line.startswith("```"): fence = not fence
        if not fence:
            m = re.match(r":::(\w+)(?:\s+(.*))?$", line)
            if m and not in_adm: out.append(adm_open(m)); in_adm = True; continue
            if line.strip() == ":::" and in_adm: out.append("\n</div>\n"); in_adm = False; continue
        out.append(line)
    t = "\n".join(out)
    # details -> Q/A boxes
    t = re.sub(r"<details>\s*<summary><strong>(.*?)</strong></summary>",
               lambda m: f'<div class="qa">\n\n<div class="q">\n\n**{m.group(1)}**\n\n</div>\n\n<div class="a">\n\n', t, flags=re.S)
    t = t.replace("</details>", "\n</div>\n\n</div>")
    # strip docusaurus-only 'Corpus scope note' stays as info. Drop markdown links to .md files (keep text)
    t = re.sub(r"\[([^\]]+)\]\((?!http)[^)]*\.md[^)]*\)", r"\1", t)
    return t

import json, os
FIG = json.loads((HERE / "figures.json").read_text()).get(str(part), {})
BOOKS = pathlib.Path.home() / "Desktop/books-toon-rag"

def add_figures(body, chnum):
    for fg in reversed(FIG.get(chnum, [])):
        src = BOOKS / fg["book"] / "OEBPS/Images" / fg["file"]
        if not src.exists(): print("missing image", src); continue
        dst = WORK / "img" / f"fig_{fg['file']}"; shutil.copy(src, dst)
        block = (f'\n\n<div class="figure">\n\n![{fg["caption"]}](img/{dst.name})\n\n'
                 f'<p class="figcap">{fg["caption"]} <span class="credit">Source: {fg["credit"]}.</span></p>\n\n</div>\n\n')
        m = re.search(r"^" + re.escape(fg["after"]) + r".*\n", body, re.M)
        if not m: print("anchor not found", fg["after"]); continue
        body = body[:m.end()] + block + body[m.end():]
    return body

parts = []
files = sorted(glob.glob(pdir + "/[0-9][0-9]-*.md"))
for f in files:
    meta, body = front(pathlib.Path(f).read_text())
    body = add_figures(body, pathlib.Path(f).name[:2])
    parts.append(convert(body).strip() + "\n")
book = "\n\n".join(parts)
(WORK / "book.md").write_text(book)

title = f"AI Infrastructure Handbook: Part {part}"
sub = {9: "NVIDIA Systems and Reference Architectures"}.get(part, pname)
# cover
cover_html = WORK / "cover.html"
cover_html.write_text(f"""<html><body style="margin:0;width:1600px;height:2400px;background:linear-gradient(160deg,#0f2747,#1b5fb4 60%,#2e9e5b);color:#fff;font-family:-apple-system,Helvetica,sans-serif;display:flex;flex-direction:column;justify-content:center;padding:0 140px;box-sizing:border-box">
<div style="font-size:60px;letter-spacing:8px;opacity:.8">AI INFRASTRUCTURE HANDBOOK</div>
<div style="font-size:230px;font-weight:800;line-height:1;margin:60px 0 40px">Part {part}</div>
<div style="font-size:90px;line-height:1.15;font-weight:600">{sub}</div>
<div style="font-size:48px;margin-top:140px;opacity:.75">{len(files)} chapters · labs · checkpoint questions</div></body></html>""")
subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless", "--disable-gpu", "--hide-scrollbars",
                f"--screenshot={WORK/'cover.png'}", "--window-size=1600,2400", f"file://{cover_html}"], capture_output=True)
(WORK / "meta.yaml").write_text(f"---\ntitle: \"{title}\"\nsubtitle: \"{sub}\"\nauthor: \"Jithin P. Joseph\"\nlang: en\n---\n")
epub = OUT / f"ai-infra-handbook-part-{part:02d}.epub"
cmd = ["pandoc", "-f", "gfm-tex_math_dollars+raw_html", "-t", "epub3", str(WORK/"meta.yaml"), str(WORK/"book.md"), "-o", str(epub),
       "--toc", "--toc-depth=2", "--split-level=1", "--no-highlight", "--css", str(HERE/"style.css"),
       "--epub-cover-image", str(WORK/"cover.png"), "--resource-path", f"{WORK}:{pdir}"]
r = subprocess.run(cmd, capture_output=True, text=True, cwd=WORK)
print(r.stderr[-1500:]); print("OK" if r.returncode == 0 else "FAILED", epub, round(epub.stat().st_size/1e6, 2), "MB")
