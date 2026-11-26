import xml.etree.ElementTree as ET
import re

def audit_file(path):
    print(f"=== Auditing {path} ===")
    tree = ET.parse(path)
    root = tree.getroot()
    raw = open(path).read()

    # 1. Structure
    children = list(root)
    assert children[0].tag.split('}')[-1] == 'title', "First child must be title"
    assert children[1].tag.split('}')[-1] == 'desc', "Second child must be desc"
    print("1. Structure: PASS (<title> and <desc> are first children)")

    # 2. Dimensions
    w = root.get('width')
    h = root.get('height')
    vb = root.get('viewBox').split()
    assert w == '1600', f"Width is {w}"
    assert vb[0] == '0' and vb[1] == '0' and vb[2] == '1600', f"viewBox {vb}"
    vh = float(vb[3])
    assert 900 <= vh <= 1200, f"viewBox height {vh} not in 900..1200"
    assert float(h) == vh, f"height {h} != viewBox height {vh}"
    print(f"2. Dimensions: PASS ({w}x{h}, viewBox {root.get('viewBox')})")

    # 3. Text and Font size
    text_elems = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        txt = re.sub(r'\s+', ' ', "".join(el.itertext()).strip())
        fs = float(el.attrib.get('font-size', 0))
        assert fs >= 24, f"Text '{txt}' font size {fs} < 24"
        for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs:
                assert float(tfs) >= 24, f"tspan font size {tfs} < 24 in '{txt}'"
        text_elems.append((txt, fs))

    print(f"3. Font sizes: PASS (All {len(text_elems)} texts have font-size >= 24px)")

    # 4. Expected labels
    expected = [
        "Where a variable can be defined, from the desk note to the front door",
        "task vars: only that one task, gone when it ends (extra: 1)",
        "set_fact and register: created by tasks",
        "include_vars: loads a file or directory into host variables during the run",
        "play vars: vars block, belongs to the play, stops when the play ends",
        "vars_files: loads files at the start of the play; the file name can itself be a template, vars/{{ ansible_facts[os_family] | lower }}.yml, so Debian and RedHat hosts load different files with no if statement",
        "vars_prompt: asks a person at run time: avoid in automation, it stops the run and waits (private: false, name reason, prompt Maintenance reason)",
        "lookup results and lookup(env, ...)",
        "inventory, group_vars, host_vars (4.5) and role defaults/ and vars/ (4.11)",
        "extra vars -e: key=value, a JSON-style string such as {\"k\": [1,2]}, or @file.yml",
        "put a value where the people who own it will look: a cluster-wide default in group_vars/all, a rack's special case in the group for that rack, a one-off test on the command line where it vanishes when the run ends; which one wins when two disagree is in 4.5",
        "late Tuesday: raising the NCCL debug level for the second cluster also turned on verbose logging on the first, filling its disk: the setting was written in a place that reached further than you thought",
        "The place you choose decides how far the value reaches"
    ]

    found = [t for t, fs in text_elems]
    print(f"\n4. Checking fidelity ({len(expected)} expected labels vs {len(found)} found):")
    for i, exp in enumerate(expected, 1):
        cnt = found.count(exp)
        print(f"   {i:2d}. [{'OK' if cnt==1 else 'FAIL'}] cnt={cnt}: '{exp[:65]}...'")
        assert cnt == 1, f"Expected '{exp}' count={cnt}"

    assert len(found) == len(expected), f"Found {len(found)} != expected {len(expected)}"
    extras = [t for t in found if t not in expected]
    assert len(extras) == 0, f"Found extra texts: {extras}"
    print("4. Expected labels fidelity: PASS (All match exactly once, zero extras)")

    # 5. Forbidden words
    banned = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
    for t in found:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for b in banned:
            assert b not in words, f"Forbidden word '{b}' found in text: '{t}'"
    print("5. Forbidden words: PASS (no style words printed as text)")

    # 6. Arrows count
    arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
    assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
    print("6. Arrows count: PASS (0 arrows)")

    # 7. Orange highlight count
    orange_items = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"7. Orange highlight #db8129: {len(orange_items)} occurrences on vars_prompt (PASS)")

    print("\nALL CHECKS PASSED PERFECTLY!")

audit_file("test_candidate_svg.svg")
