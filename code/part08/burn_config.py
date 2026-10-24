#!/usr/bin/env python3
"""Check a BCM burn configuration XML against the rules in Installation Manual chapter 11, and read burn status lines.

  burn_config.py FILE.xml

Rules checked: phases section exists in pre-install or post-install; phase names unique and in alphanumeric order;
every phase has a test; a phase with only endless tests never ends; post-burn-install is AUTO/FULL/MAIN/NOSYNC;
memtest86 never ends by itself. The real schema is burnconfig.xsd on the head node ('cmsh -c "main xsdschema burnconfig"').
"""
import re, sys
import xml.etree.ElementTree as ET

INSTALL_MODES = {"AUTO", "FULL", "MAIN", "NOSYNC"}
LETTERS = {"S": "started", "W": "warning", "F": "failed", "P": "passed"}


def check(xml_text):
    problems = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return [f"not well-formed XML: {e}"]
    if root.tag != "burnconfig":
        return [f"root element is <{root.tag}>, expected <burnconfig>"]
    sections = [s for s in root if s.tag in ("pre-install", "post-install")]
    if not sections:
        problems.append("no <pre-install> or <post-install> section: nothing would run")
    names = []
    for sec in sections:
        phases = [p for p in sec if p.tag == "phase"]
        if not phases:
            problems.append(f"<{sec.tag}> has no phases (the tags must exist, but an empty section does nothing)")
        order = [p.get("name") for p in phases]
        if order != sorted(order):
            problems.append(f"<{sec.tag}> phases are not in alphanumeric order: {order}")
        for p in phases:
            n = p.get("name")
            if not n:
                problems.append(f"<{sec.tag}> has a phase with no name"); continue
            if n in names:
                problems.append(f"phase name {n} is used twice: names must be unique")
            names.append(n)
            tests = [t for t in p if t.tag == "test"]
            if not tests:
                problems.append(f"phase {n} has no tests")
            elif all(t.get("endless") == "1" for t in tests):
                problems.append(f"phase {n} has only endless tests: endless tests end only when a non-endless test in the phase ends, so it never finishes")
            for t in tests:
                if t.get("name") == "memtest86":
                    problems.append(f"phase {n}: memtest86 runs endlessly unless someone ends it at the console or power resets; large clusters rely on hpl and memtester")
    pbi = root.find("post-burn-install")
    if pbi is not None and (pbi.text or "").strip() not in INSTALL_MODES:
        problems.append(f"<post-burn-install> is '{(pbi.text or '').strip()}': must be one of {sorted(INSTALL_MODES)}")
    for a in root.findall("./mail/address"):
        if not re.match(r"^[^@\s]+@[^@\s]+$", (a.text or "").strip()):
            problems.append(f"mail address '{(a.text or '').strip()}' does not look like an address")
    return problems


def parse_status(line):
    """'node001 (00000000a000) - W(0) phase 02-disks 00:02:58 (D:H:M) FAILED, mce_check (SP), disktest (SF,61), kmon (SP)'"""
    m = re.match(r"^(\S+) \((\w+)\) - W\((\d+)\) phase (\S+) (\S+) \(D:H:M\) (\w+),\s*(.*)$", line.strip())
    if not m:
        raise ValueError("not a burn status line")
    tests = {}
    for t in re.findall(r"(\w+) \(([SWFP]+)(?:,([^)]*))?\)", m.group(7)):
        tests[t[0]] = {"letters": t[1], "meaning": [LETTERS[c] for c in t[1]], "custom": t[2] or None, "failed": "F" in t[1]}
    return {"node": m.group(1), "warnings": int(m.group(3)), "phase": m.group(4), "since": m.group(5), "state": m.group(6), "tests": tests}


if __name__ == "__main__":
    ps = check(open(sys.argv[1]).read())
    for p in ps:
        print("-", p)
    print("OK" if not ps else f"{len(ps)} problem(s)")
    sys.exit(1 if ps else 0)
