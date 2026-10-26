#!/usr/bin/env python3
"""Final validation for one chapter.  Usage: python3 tools/validate_chapter.py 10.7"""
import re, sys, glob, subprocess, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
P, C = sys.argv[1].split("."); PP, CC = f"{int(P):02d}", f"{int(C):02d}"
f = glob.glob(str(ROOT / f"docs/part-{PP}-*/{CC}-*.md"))[0]; t = open(f).read()
prose = re.sub(r"```.*?```", "", t, flags=re.S)
checks = []
def chk(name, ok, detail=""): checks.append((name, ok, detail))
chk("status is drafted/reviewed (not scaffold)", bool(re.search(r'^status: "(drafted|reviewed|draft)"', t, re.M)))
chk("20 checkpoint questions", t.count("<summary>") == 20, f"{t.count('<summary>')} found")
chk("Exercises section", "## Exercises" in t)
chk("sources section", "## Sources and review notes" in t)
chk("labelled inferences/unverified note", bool(re.search(r"inference|not verified|untested", t, re.I)))
chk("honest 'not run on live hardware' note", bool(re.search(r"untested|not (been )?(verified|executed|run)|not verified on live", t, re.I)), "template rule 5")
chk("no exclamation marks in prose", not re.search(r"(?<=[\w)`*\"%\]])!(?=\s|$)", prose))
chk("at least one mermaid diagram", "```mermaid" in t)
long_nodes = []
for k, m in enumerate(re.finditer(r"```mermaid\n(.*?)```", t, re.S), 1):
    for lab in re.findall(r'\["([^"]+)"\]|\{"([^"]+)"\}|\("([^"]+)"\)', m.group(1)):
        txt = next(x for x in lab if x)
        if len(txt.replace("<br/>", " ")) > 130: long_nodes.append((k, len(txt.replace("<br/>", " "))))
chk("diagram nodes are short (<= 130 characters; put detail in a table)", not long_nodes, f"diagram/length: {long_nodes[:6]}")
chk("no >15-word quote of a source", True, "manual: check any long quotation")
labs = glob.glob(str(ROOT / f"code/part{PP}/*lab*.py"))
txt = "".join(open(l).read() for l in labs)
mine = [l for l in labs if pathlib.Path(l).stem.replace("_lab", "") in t or pathlib.Path(l).name in t]
ok = True; det = []
for l in mine:
    r = subprocess.run(["python3", "-B", l], capture_output=True, text=True)
    last = (r.stdout.strip().splitlines() or ["no output"])[-1]; ok &= "0 failed" in last; det.append(f"{pathlib.Path(l).name}: {last}")
chk("chapter lab(s) pass", bool(mine) and ok, "; ".join(det) or "no lab found")
ledger = ROOT / f"planning/ledgers/{P}-{CC}.md"; chk("claim ledger exists", ledger.exists())
for n, ok, d in checks: print(("PASS " if ok else "FAIL ") + n + (f"  ({d})" if d else ""))

# --- readability report (warnings only; see planning/LANGUAGE_RULE.md) ---
def readability(text):
    body = re.sub(r"```.*?```", " ", text, flags=re.S)
    body = re.sub(r"<details>.*?</details>", " ", body, flags=re.S) if False else body
    lines = [l for l in body.splitlines() if l.strip() and not l.lstrip().startswith(("|", "#", ">", ":::", "<", "---", "!["))]
    para = " ".join(lines)
    words = len(re.sub(r"`[^`]*`", "X", para).split()) or 1
    spans = len(re.findall(r"`[^`]+`", para))
    nums = len(re.findall(r"\b\d[\d,]*\.?\d*\b", re.sub(r"`[^`]*`", "", para)))
    sents = [x for x in re.split(r"(?<=[.!?])\s+", re.sub(r"`[^`]*`", "X", para)) if len(x.split()) > 3]
    n = len(sents) or 1
    avg = sum(len(x.split()) for x in sents) / n
    longp = sum(1 for x in sents if len(x.split()) > 35) / n
    paren = sum(x.count("(") for x in sents) / n
    return dict(spans=100 * spans / words, nums=100 * nums / words, avg=avg, long=100 * longp, paren=paren)
r = readability(t)
lim = dict(spans=4.0, nums=6.0, avg=22.0, long=3.0, paren=0.5)
print("\n--- readability (warnings only; target: reads like a book, see planning/LANGUAGE_RULE.md) ---")
lab = dict(spans="code-formatted terms per 100 words", nums="numbers per 100 words", avg="average sentence length (words)", long="% of sentences over 35 words", paren="parentheses per sentence")
for k in lim:
    print(("WARN " if r[k] > lim[k] else "ok   ") + f"{lab[k]}: {r[k]:.1f} (target <= {lim[k]})")
print("\n--- number provenance ---")
subprocess.run(["python3", str(ROOT / "tools/check_provenance.py"), sys.argv[1]])
print("\n--- source coverage ---")
subprocess.run(["python3", str(ROOT / "tools/check_coverage.py"), sys.argv[1]])
print(f"\nwords: {len(prose.split())}")
