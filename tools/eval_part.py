#!/usr/bin/env python3
"""Compare Part 9 docs against the saved baseline.  Usage: python3 tools/eval_part.py [label]"""
import re, glob, sys, subprocess, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parents[1]
NEW = ROOT / "docs/part-09-nvidia-systems"; OLD = ROOT / "planning/eval/part09_baseline"
def chapters(d): return {p.name[:2]: p.read_text() for p in sorted(d.glob("[0-9][0-9]-*.md"))}
old, new = chapters(OLD), chapters(NEW)
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?\s?(?:kW|MW|GB/s|TB/s|GB|TB|W|ms|µs|Gbps|CFM|%|×|x|PFLOPS|TFLOPS|bytes|B/param)?")
def nums(t):
    t = re.sub(r"```.*?```", "", t, flags=re.S)
    return collections.Counter(m.strip() for m in NUM.findall(t) if len(m.strip()) > 1)
def words(t): return len(re.sub(r"```.*?```", "", t, flags=re.S).split())
def heads(t): return [h.strip() for h in re.findall(r"^#{2,3} (.+)$", t, re.M)]
def shingles(t, n=9):
    ws = re.findall(r"[a-z0-9]+", re.sub(r"```.*?```", "", t.lower(), flags=re.S))
    return {" ".join(ws[i:i+n]) for i in range(0, max(0, len(ws)-n), 1)}
def cross_dup(chs):
    seen = collections.Counter()
    sets = {k: shingles(v) for k, v in chs.items()}
    for s in sets.values():
        for sh in s: seen[sh] += 1
    return sum(1 for sh, c in seen.items() if c > 1)
print(f"{'ch':3} {'words old>new':>15} {'Q':>3} {'Ex':>3} {'!':>3} {'mmd':>3} {'code':>4} {'nums lost':>9} {'new nums':>8} {'heads lost':>10}")
tw_o = tw_n = 0; problems = []
for k in sorted(old):
    o, n = old[k], new.get(k, "")
    wo, wn = words(o), words(n); tw_o += wo; tw_n += wn
    q = n.count("<summary>"); ex = len(re.findall(r"^## Exercises", n, re.M))
    ex_ = len(re.findall(r"(?<=[\w)`*\"%\]])!(?=\s|$)", re.sub(r"```.*?```", "", n, flags=re.S)))
    no, nn = nums(o), nums(n)
    lost = sum((no - nn).values()); added = sum((nn - no).values())
    ho, hn = heads(o), set(heads(n)); hl = sum(1 for h in ho if h not in hn)
    print(f"{k:3} {wo:>6}>{wn:<8} {q:>3} {ex:>3} {ex_:>3} {n.count('```mermaid'):>3} {n.count(chr(96)*3)//2:>4} {lost:>9} {added:>8} {hl:>10}")
    if q != 20: problems.append(f"{k}: {q} questions")
    if not ex: problems.append(f"{k}: no Exercises")
    if "5,000 coax" in n or "5,000 coaxial" in n: problems.append(f"{k}: unsourced cable claim back")
print(f"\nTOTAL words {tw_o} -> {tw_n} ({(tw_n-tw_o)/tw_o*100:+.1f}%)")
do, dn = cross_dup(old), cross_dup(new)
print(f"Cross-chapter repeated 9-word phrases: {do} -> {dn} ({(dn-do)/max(do,1)*100:+.1f}%)")
print("Problems:", problems or "none")
if "--labs" in sys.argv or True:
    fails = 0
    for f in sorted(glob.glob(str(ROOT/"code/part09/*_lab.py"))):
        r = subprocess.run(["python3", "-B", f], capture_output=True, text=True)
        last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else "no output"
        if "0 failed" not in last: fails += 1; print("LAB FAIL", pathlib.Path(f).name, last)
    print("Labs:", "all pass" if not fails else f"{fails} failing")
