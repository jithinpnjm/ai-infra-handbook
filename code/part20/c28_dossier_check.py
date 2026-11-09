#!/usr/bin/env python3
"""Check a project dossier written from c28_dossier_template.md.

Reports missing sections, unfilled placeholders, claims without a number,
decisions without two alternatives and incomplete failure write-ups.
Standard library only.

Usage: c28_dossier_check.py DOSSIER.md [--json]   (exit 1 if any finding)
"""
import json
import re
import sys

SECTIONS = {
    "context": "Context",
    "role": "My role and the team",
    "constraints": "Constraints",
    "numbers": "Numbers",
    "architecture": "Architecture",
    "decisions": "Decisions",
    "failures": "Failures",
    "changes": "What I would change",
    "metrics": "Metrics of success",
}
ALIASES = {
    "context": ("context",),
    "role": ("my role", "role", "team"),
    "constraints": ("constraints",),
    "numbers": ("numbers", "scale"),
    "architecture": ("architecture",),
    "decisions": ("decisions",),
    "failures": ("failures", "what broke"),
    "changes": ("what i would change", "what i would do differently"),
    "metrics": ("metrics of success", "metrics", "results"),
}
MIN_NUMERIC_LINES = {"numbers": 3, "metrics": 2, "failures": 1}
MIN_BLOCKS = {"decisions": 3, "failures": 1}
BLOCK_LABELS = {
    "decisions": ("chosen", "alternatives", "why", "cost accepted"),
    "failures": ("what broke", "how it was detected", "root cause",
                 "what changed afterwards"),
}
PLACEHOLDER = re.compile(
    r"\[YOUR[^\]]*\]|\[YES OR NO[^\]]*\]|\bTODO\b|\bTBD\b|\[\.\.\.\]|<fill[^>]*>")
CLAIM = re.compile(
    r"\b(faster|slower|improv\w*|reduc\w*|increas\w*|decreas\w*|fewer|saved"
    r"|significant\w*|massive\w*|huge|dramatic\w*|a lot|lots of|greatly"
    r"|much (?:more|less|better|faster))\b", re.I)
HEADING = re.compile(r"^(#{2,3})\s+(.*?)\s*$")
LABEL = re.compile(r"^\s*[-*]\s+([A-Za-z][A-Za-z ]*?):\s*(.*)$")
SUBBULLET = re.compile(r"^\s{2,}[-*]\s+(.*)$")


def strip_comments(text):
    """Remove HTML comments but keep line numbers stable."""
    return re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"),
                  text, flags=re.S)


def clean(s):
    return PLACEHOLDER.sub("", s).strip(" -*:.,")


def filled(line):
    """Text of a line after its 'label:' part, with placeholders removed."""
    body = line.split(":", 1)[1] if ":" in line else line
    return clean(body)


def parse(text):
    """Return {key: {'line': n, 'lines': [(n, text)], 'blocks': [...]}}."""
    out, cur, block = {}, None, None
    for n, raw in enumerate(strip_comments(text).splitlines(), 1):
        m = HEADING.match(raw)
        if m and len(m.group(1)) == 2:
            title = re.sub(r"^\d+[.)]?\s*", "", m.group(2)).lower()
            cur = next((k for k, names in ALIASES.items()
                        if any(title.startswith(a) for a in names)), None)
            block = None
            if cur and cur not in out:
                out[cur] = {"line": n, "lines": [], "blocks": []}
            elif cur:
                cur = None
            continue
        if cur is None:
            continue
        if m and len(m.group(1)) == 3:
            block = {"line": n, "title": m.group(2), "lines": []}
            out[cur]["blocks"].append(block)
            continue
        out[cur]["lines"].append((n, raw))
        if block is not None:
            block["lines"].append((n, raw))
    return out


def block_fields(block):
    """Map label -> list of item strings (inline text plus sub-bullets)."""
    fields, label = {}, None
    for _, raw in block["lines"]:
        m = LABEL.match(raw)
        sub = SUBBULLET.match(raw)
        if m and not sub:
            label = m.group(1).strip().lower()
            inline = [x for x in m.group(2).split(";") if x.strip()]
            fields[label] = inline
        elif sub and label:
            fields[label].append(sub.group(1))
    return fields


def find_field(fields, prefix):
    for k, v in fields.items():
        if k.startswith(prefix):
            return v
    return None


def check(text):
    findings = []

    def add(kind, line, msg):
        findings.append({"kind": kind, "line": line, "message": msg})

    secs = parse(text)
    for key, name in SECTIONS.items():
        if key not in secs:
            add("missing_section", 0, f"section '{name}' is missing")
            continue
        sec = secs[key]
        body = [(n, t) for n, t in sec["lines"] if filled(t)]
        if not body:
            add("empty_section", sec["line"],
                f"section '{name}' has no filled content")
        need = MIN_NUMERIC_LINES.get(key, 0)
        have = sum(1 for _, t in body if re.search(r"\d", filled(t)))
        if body and have < need:
            add("too_few_numbers", sec["line"],
                f"section '{name}' needs {need} lines with a number, has {have}")
        need = MIN_BLOCKS.get(key, 0)
        if need and len(sec["blocks"]) < need:
            add("too_few_blocks", sec["line"],
                f"section '{name}' needs {need} entries, has {len(sec['blocks'])}")

    for key in ("decisions", "failures"):
        for block in secs.get(key, {}).get("blocks", []):
            fields = block_fields(block)
            title = clean(block["title"].split(":", 1)[-1]) or "(untitled)"
            for label in BLOCK_LABELS[key]:
                items = find_field(fields, label)
                if items is None or not any(clean(i) for i in items):
                    kind = ("decision_no_alternatives"
                            if label == "alternatives" else "entry_incomplete")
                    add(kind, block["line"],
                        f"{key[:-1]} '{title}': '{label}' is missing or unfilled")
                elif label == "alternatives":
                    real = [i for i in items if clean(i)]
                    if len(real) < 2:
                        add("decision_no_alternatives", block["line"],
                            f"decision '{title}': needs two alternatives, "
                            f"has {len(real)}")

    in_code = False
    for n, raw in enumerate(strip_comments(text).splitlines(), 1):
        if raw.lstrip().startswith("```"):
            in_code = not in_code
        if in_code or HEADING.match(raw) or raw.startswith("# "):
            continue
        plain = PLACEHOLDER.sub("", raw)
        if not clean(plain.split(":", 1)[-1]):
            continue
        if CLAIM.search(plain) and not re.search(r"\d", plain):
            add("unquantified", n,
                f"claim without a number: {raw.strip()[:70]}")
    for n, raw in enumerate(strip_comments(text).splitlines(), 1):
        if PLACEHOLDER.search(raw):
            add("placeholder", n, f"unfilled: {PLACEHOLDER.search(raw).group(0)}")
    findings.sort(key=lambda f: (f["line"], f["kind"]))
    return findings


def summarize(findings):
    counts = {}
    for f in findings:
        counts[f["kind"]] = counts.get(f["kind"], 0) + 1
    return counts


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    with open(args[0], encoding="utf-8") as fh:
        findings = check(fh.read())
    if "--json" in argv:
        print(json.dumps({"findings": findings,
                          "counts": summarize(findings)}, indent=2))
    else:
        for f in findings:
            if f["kind"] == "placeholder" and len(findings) > 40:
                continue
            print(f"line {f['line']:>3}  {f['kind']:<26} {f['message']}")
        print("summary:", summarize(findings) or "clean")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
