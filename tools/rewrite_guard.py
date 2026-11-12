#!/usr/bin/env python3
"""Compare a chapter before and after a voice rewrite.

Usage:
  python3 tools/rewrite_guard.py BASE_REF HEAD_REF PATH...        # git refs, e.g. 9394a58~1 9394a58 docs/part-01-linux
  python3 tools/rewrite_guard.py BASE_REF WORKTREE PATH...        # compare a ref with the files on disk

A voice rewrite may change wording. It must not change facts. For every chapter the report lists:
  code blocks   : fenced blocks added, removed or edited (must be zero for a pure voice rewrite)
  numbers       : numeric tokens that appear only in the new text (possible invented facts) or only in the old text (possible lost facts)
  commands      : inline code spans that appear only in one version
  structure     : front matter, headings, Mermaid blocks, checkpoint summary count, tables
  length        : words before and after
  residue       : leftover drafting words in the body (Volume N, the book, untested here, I ran, Example N-N)
Exit status 1 when any hard check fails (code blocks, front matter, checkpoint count).
"""
import re, subprocess, sys, pathlib, glob

ROOT = pathlib.Path(__file__).resolve().parents[1]


def git_show(ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def read(ref, path):
    if ref == "WORKTREE":
        p = ROOT / path
        return p.read_text() if p.exists() else None
    return git_show(ref, path)


def split(t):
    m = re.match(r"^---\n(.*?)\n---\n", t, re.S)
    fm = m.group(1) if m else ""
    body = t[m.end():] if m else t
    return fm, body


def fences(body):
    return [b.strip() for b in re.findall(r"```.*?\n(.*?)```", body, re.S)]


def prose(body):
    b = re.sub(r"```.*?```", " ", body, flags=re.S)
    return b


NUM = re.compile(r"(?<![\w.])\d[\d,]*\.?\d*%?")


def numbers(body):
    p = prose(body)
    p = re.sub(r"^#{1,6} .*$", " ", p, flags=re.M)          # headings carry section numbers
    p = re.sub(r"\b\d+\.\d+\b(?= (and|to) \d+\.\d+)", " ", p)  # chapter cross references
    out = {}
    for n in NUM.findall(p):
        n = n.rstrip(".,")
        out[n] = out.get(n, 0) + 1
    return out


def spans(body):
    return set(re.findall(r"`([^`\n]{2,80})`", prose(body)))


RES = {
    "Volume N": r"[Vv]olume[- ]\d+",
    "the book": r"\b[Tt]he book\b",
    "untested here": r"untested here",
    "Example N-N": r"\bExample \d+-\d+",
    "I ran / my tool": r"\b(I (ran|did not|have not|could not|confirmed|checked)|my (inference|reasoning|tool|lab|mock))\b",
}


def residue(body):
    main = re.split(r"\n## Sources and review notes", body)[0]
    main = re.sub(r"```.*?```", " ", main, flags=re.S)
    return {k: len(re.findall(p, main)) for k, p in RES.items() if re.search(p, main)}


def review(base_ref, head_ref, path):
    old, new = read(base_ref, path), read(head_ref, path)
    if old is None or new is None:
        return None
    ofm, ob = split(old)
    nfm, nb = split(new)
    hard = []
    soft = []
    if ofm != nfm:
        hard.append("front matter changed")
    oc, nc = fences(ob), fences(nb)
    if oc != nc:
        added = [c for c in nc if c not in oc]
        removed = [c for c in oc if c not in nc]
        hard.append(f"code blocks changed: +{len(added)} -{len(removed)}")
    osum, nsum = ob.count("<summary>"), nb.count("<summary>")
    if osum != nsum:
        hard.append(f"checkpoint summaries {osum}->{nsum}")
    omm, nmm = ob.count("```mermaid"), nb.count("```mermaid")
    if omm != nmm:
        soft.append(f"mermaid {omm}->{nmm}")
    oh = re.findall(r"^## .*$", ob, re.M)
    nh = re.findall(r"^## .*$", nb, re.M)
    if oh != nh:
        gone = [h for h in oh if h not in nh]
        new_h = [h for h in nh if h not in oh]
        soft.append(f"H2 headings changed: -{len(gone)} +{len(new_h)}")
    on, nn = numbers(ob), numbers(nb)
    added_nums = sorted(k for k in nn if k not in on)
    lost_nums = sorted(k for k in on if k not in nn)
    os_, ns_ = spans(ob), spans(nb)
    added_spans = sorted(ns_ - os_)
    lost_spans = sorted(os_ - ns_)
    ow, nw = len(prose(ob).split()), len(prose(nb).split())
    return dict(path=path, hard=hard, soft=soft, added_nums=added_nums, lost_nums=lost_nums,
                added_spans=added_spans, lost_spans=lost_spans, ow=ow, nw=nw,
                res_old=residue(ob), res_new=residue(nb))


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    base, head, *paths = sys.argv[1:]
    files = []
    for p in paths:
        pp = ROOT / p
        if pp.is_dir():
            if head == "WORKTREE":
                files += sorted(str(x.relative_to(ROOT)) for x in pp.glob("*.md"))
            else:
                ls = subprocess.run(["git", "ls-tree", "-r", "--name-only", head, p], cwd=ROOT, capture_output=True, text=True).stdout.split()
                files += [x for x in ls if x.endswith(".md")]
        else:
            files.append(p)
    fail = 0
    tot = dict(ow=0, nw=0, an=0, ln=0, asp=0, lsp=0)
    for f in files:
        r = review(base, head, f)
        if r is None:
            continue
        flag = "FAIL" if r["hard"] else "ok  "
        fail += bool(r["hard"])
        tot["ow"] += r["ow"]; tot["nw"] += r["nw"]
        tot["an"] += len(r["added_nums"]); tot["ln"] += len(r["lost_nums"])
        tot["asp"] += len(r["added_spans"]); tot["lsp"] += len(r["lost_spans"])
        print(f"{flag} {f.split('/')[-1][:60]:60s} words {r['ow']:6d}->{r['nw']:6d}  new numbers {len(r['added_nums']):3d}  lost numbers {len(r['lost_nums']):3d}  new code spans {len(r['added_spans']):3d} lost {len(r['lost_spans']):3d}  residue {sum(r['res_old'].values())}->{sum(r['res_new'].values())}")
        for h in r["hard"]:
            print("      HARD:", h)
        for s in r["soft"]:
            print("      note:", s)
        if r["added_nums"]:
            print("      new numbers:", ", ".join(r["added_nums"][:25]))
    print(f"\n{len(files)} chapters, {fail} with hard failures. words {tot['ow']} -> {tot['nw']}. new numbers {tot['an']}, lost numbers {tot['ln']}, new code spans {tot['asp']}, lost {tot['lsp']}")
    sys.exit(1 if fail else 0)


main()
