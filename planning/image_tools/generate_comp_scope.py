import re
import xml.etree.ElementTree as ET

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Comprehension scope: the loop variable stays inside, the walrus target leaks</title>
  <desc>Visual infographic explaining comprehension scope rules, loop variable isolation, walrus operator leakage, clause placement, matrix patterns, and best practices.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Main Title (48px bold) -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36"><tspan x="800" dy="0">Comprehension scope: the loop variable stays inside, </tspan><tspan x="800" dy="56">the walrus target leaks</tspan></text>

  <!-- ==================== ROW 1: TWO CODE BLOCKS WITH SCOPE BOXES ==================== -->
  <!-- Block 1: Comprehension Scope vs For Loop Scope (x=40, y=135, w=740, h=215) -->
  <g id="block-1">
    <rect x="40" y="135" width="740" height="215" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- Lock / Scope Icon (56px) -->
    <g transform="translate(58, 155)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="20" width="40" height="30" rx="4"/>
      <path d="M 18 20 V 12 A 10 10 0 0 1 38 12 V 20"/>
      <circle cx="28" cy="33" r="3" fill="#207448"/>
      <line x1="28" y1="36" x2="28" y2="42"/>
    </g>

    <!-- Scope Box 1: Comprehension Scope (inner X isolated) -->
    <rect x="128" y="145" width="632" height="94" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <rect x="260" y="162" width="326" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>
    <text x="146" y="186" font-family="monospace" font-size="24" fill="#303a36"><tspan x="146" dy="0">X = 99; [X for X in range(5)] gives </tspan><tspan x="146" dy="34">[0, 1, 2, 3, 4]; outer X is still 99</tspan></text>

    <!-- Scope Box 2: Regular For Loop (outer X mutated) -->
    <rect x="128" y="247" width="632" height="94" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text x="146" y="288" font-family="monospace" font-size="24" fill="#303a36"><tspan x="146" dy="0">for X in range(5): pass </tspan><tspan x="146" dy="34">changes outer X to 4</tspan></text>
  </g>

  <!-- Block 2 (Orange): Walrus Operator Leaks into Enclosing Scope (x=820, y=135, w=740, h=215) -->
  <g id="block-2">
    <rect x="820" y="135" width="740" height="215" rx="14" fill="#e8f1ea" stroke="#db8129" stroke-width="3"/>
    
    <!-- Walrus Leak / Warning Icon (56px, orange) -->
    <g transform="translate(838, 155)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 12 L 44 44 M 44 12 L 12 44"/>
      <circle cx="28" cy="28" r="22"/>
    </g>

    <!-- Scope Box: Walrus Target Leaking Out -->
    <rect x="908" y="137" width="632" height="206" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="2"/>
    <rect x="918" y="185" width="456" height="58" rx="6" fill="#fdf4eb" stroke="#db8129" stroke-width="1.5" stroke-dasharray="4 3"/>
    <text x="930" y="178" font-family="monospace" font-size="24" fill="#303a36"><tspan x="930" dy="0">S = 'hack'; </tspan><tspan x="930" dy="30">[(temp := S[i]) + temp.upper() </tspan><tspan x="930" dy="30">for i in range(len(S))] gives </tspan><tspan x="930" dy="30">['hH', 'aA', 'cC', 'kK']; temp is 'k' </tspan><tspan x="930" dy="30">in the enclosing scope, i raises </tspan><tspan x="930" dy="29">NameError: name i is not defined</tspan></text>
  </g>

  <!-- ==================== ROW 2: RULES STRIP (x=40, y=390, w=1520, h=84) ==================== -->
  <g id="rules-strip">
    <rect x="40" y="390" width="1520" height="84" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- Document / Rules Icon (56px) -->
    <g transform="translate(65, 404)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 6 H 40 L 48 14 V 50 H 8 Z"/>
      <path d="M 40 6 V 14 H 48"/>
      <line x1="16" y1="24" x2="36" y2="24"/>
      <line x1="16" y1="34" x2="36" y2="34"/>
      <line x1="16" y1="42" x2="28" y2="42"/>
    </g>

    <text x="140" y="430" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="140" dy="0">a for variable in a list, set, dict or generator comprehension lives in the comprehension's own </tspan><tspan x="140" dy="28">scope; := binds its target in the enclosing scope; a yield inside a comprehension is forbidden</tspan></text>
  </g>

  <!-- ==================== ROW 3: PLACEMENT STRIP (x=40, y=514, w=1520, h=116) ==================== -->
  <g id="placement-strip">
    <rect x="40" y="514" width="1520" height="116" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- Filter Pipeline / Sliders Icon (56px) -->
    <g transform="translate(65, 544)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="8" y1="16" x2="48" y2="16"/>
      <line x1="8" y1="30" x2="48" y2="30"/>
      <line x1="8" y1="44" x2="48" y2="44"/>
      <circle cx="20" cy="16" r="4" fill="#207448"/>
      <circle cx="36" cy="30" r="4" fill="#207448"/>
      <circle cx="24" cy="44" r="4" fill="#207448"/>
    </g>

    <text x="140" y="555" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="140" dy="0">a filter if sits after the for; a conditional expression that picks a value sits before it: </tspan><tspan x="140" dy="31">["even" if n % 2 == 0 else "odd" for n in range(5)]; nested for clauses read left to right like </tspan><tspan x="140" dy="28">nested for statements</tspan></text>
  </g>

  <!-- ==================== ROW 4: LOWER CARDS (y=670 to 1056) ==================== -->
  <!-- Left Column Top: Walrus Use (x=40, y=670, w=740, h=118) -->
  <g id="walrus-use">
    <rect x="40" y="670" width="740" height="118" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- Lightning / Efficiency Icon (56px) -->
    <g transform="translate(65, 701)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="30,6 12,32 28,32 24,50 42,24 26,24" fill="#e8f1ea"/>
    </g>

    <text x="145" y="710" font-family="monospace" font-size="24" fill="#303a36"><tspan x="145" dy="0">[y for x in data if </tspan><tspan x="145" dy="30">(y := expensive(x)) is not None] </tspan><tspan x="145" dy="30" font-family="sans-serif">calls expensive once per item</tspan></text>
  </g>

  <!-- Left Column Bottom: Matrix Examples (x=40, y=828, w=740, h=228) -->
  <g id="matrix-examples">
    <rect x="40" y="828" width="740" height="228" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- 3x3 Grid / Matrix Table Icon (56px) -->
    <g transform="translate(65, 914)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="4"/>
      <line x1="8" y1="21" x2="48" y2="21"/>
      <line x1="8" y1="35" x2="48" y2="35"/>
      <line x1="21" y1="8" x2="21" y2="48"/>
      <line x1="35" y1="8" x2="35" y2="48"/>
    </g>

    <text x="145" y="868" font-family="monospace" font-size="24" fill="#303a36"><tspan x="145" dy="0">M = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]: </tspan><tspan x="145" dy="28">column [row[1] for row in M] is </tspan><tspan x="145" dy="28">[2, 5, 8]; diagonal [M[i][i] ...] is </tspan><tspan x="145" dy="28">[1, 5, 9]; anti-diagonal is [3, 5, 7]; </tspan><tspan x="145" dy="28">[col + 10 for row in M for col in row] </tspan><tspan x="145" dy="28">is flat while [[col + 10 for col in row] </tspan><tspan x="145" dy="28">for row in M] keeps rows</tspan></text>
  </g>

  <!-- Right Column: Rules of Thumb (x=820, y=670, w=740, h=386) -->
  <g id="rules-of-thumb">
    <rect x="820" y="670" width="740" height="386" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    
    <!-- Shield / Best Practices Icon (56px) -->
    <g transform="translate(845, 695)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 V 14 Z"/>
      <polyline points="20,26 26,32 36,20"/>
    </g>

    <text x="855" y="792" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="855" dy="0">more than two for or if clauses, or side </tspan><tspan x="855" dy="32">effects: use a loop; never [print(x) for x </tspan><tspan x="855" dy="32">in xs]; you cannot catch exceptions inside a </tspan><tspan x="855" dy="32">comprehension, wrap risky code in a function; </tspan><tspan x="855" dy="32">use [[0]*c for _ in range(r)]; generator </tspan><tspan x="855" dy="32">expressions for sum, any, all, max, sorted, </tspan><tspan x="855" dy="32">join, set, tuple; comprehensions are usually </tspan><tspan x="855" dy="32">20 to 50% faster than the equivalent loops</tspan></text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR (x=40, y=1096, w=1520, h=64) ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1096" width="1520" height="64" rx="12" fill="#207448"/>
    <text x="800" y="1138" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">If a comprehension needs a second look to understand, split it into a loop</text>
  </g>
</svg>'''

with open("comp_scope_final.svg", "w") as f:
    f.write(svg_content)

print("Saved to comp_scope_final.svg")

tree = ET.parse("comp_scope_final.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
assert tag1 == "title", f"Expected title, got {tag1}"
assert tag2 == "desc", f"Expected desc, got {tag2}"
print("[PASS] 1. First children are <title> and <desc>")

# 2. Dimensions check
w = root.attrib.get('width')
vb = root.attrib.get('viewBox')
assert w == "1600", f"Width must be 1600, got {w}"
assert vb == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {vb}"
print("[PASS] 2. Dimensions are width=1600, viewBox='0 0 1600 1200'")

# 3. Check font sizes
font_sizes = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', '0'))
    assert fs >= 24, f"Font size {fs} < 24 in {el}"
    font_sizes.append(fs)
    for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
        tfs = float(ts.attrib.get('font-size', fs))
        assert tfs >= 24, f"tspan font size {tfs} < 24 in {ts}"
        font_sizes.append(tfs)

print(f"[PASS] 3. All font sizes >= 24px (sizes present: {set(font_sizes)})")

# 4. Check labels
source_labels = [
    "Comprehension scope: the loop variable stays inside, the walrus target leaks",
    "X = 99; [X for X in range(5)] gives [0, 1, 2, 3, 4]; outer X is still 99",
    "for X in range(5): pass changes outer X to 4",
    "S = 'hack'; [(temp := S[i]) + temp.upper() for i in range(len(S))] gives ['hH', 'aA', 'cC', 'kK']; temp is 'k' in the enclosing scope, i raises NameError: name i is not defined",
    "a for variable in a list, set, dict or generator comprehension lives in the comprehension's own scope; := binds its target in the enclosing scope; a yield inside a comprehension is forbidden",
    'a filter if sits after the for; a conditional expression that picks a value sits before it: ["even" if n % 2 == 0 else "odd" for n in range(5)]; nested for clauses read left to right like nested for statements',
    "[y for x in data if (y := expensive(x)) is not None] calls expensive once per item",
    "M = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]: column [row[1] for row in M] is [2, 5, 8]; diagonal [M[i][i] ...] is [1, 5, 9]; anti-diagonal is [3, 5, 7]; [col + 10 for row in M for col in row] is flat while [[col + 10 for col in row] for row in M] keeps rows",
    "more than two for or if clauses, or side effects: use a loop; never [print(x) for x in xs]; you cannot catch exceptions inside a comprehension, wrap risky code in a function; use [[0]*c for _ in range(r)]; generator expressions for sum, any, all, max, sorted, join, set, tuple; comprehensions are usually 20 to 50% faster than the equivalent loops",
    "If a comprehension needs a second look to understand, split it into a loop"
]

full_texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    # Join tspans or direct text exactly
    text_parts = []
    if el.text:
        text_parts.append(el.text)
    for child in el:
        if child.text:
            text_parts.append(child.text)
        if child.tail:
            text_parts.append(child.tail)
    combined = "".join(text_parts).strip()
    full_texts.append(combined)

print(f"\nFound {len(full_texts)} text elements, expected {len(source_labels)}:")
for i, (ft, exp) in enumerate(zip(full_texts, source_labels), 1):
    assert ft == exp, f"Mismatch at {i}:\n  Found:    '{ft}'\n  Expected: '{exp}'"
    print(f"  [OK] Label {i:2d}: '{ft[:45]}...'")

assert len(full_texts) == len(source_labels), f"Count mismatch: {len(full_texts)} != {len(source_labels)}"
print("[PASS] 4. All 10 source labels present verbatim and 1-to-1 matched!")

# 5. Check zero extra words
def get_all_text(elem):
    text = elem.text or ""
    for child in elem:
        text += get_all_text(child)
        if child.tail:
            text += child.tail
    return text

root_copy = ET.parse("comp_scope_final.svg").getroot()
root_copy.remove(root_copy.find('{http://www.w3.org/2000/svg}title'))
root_copy.remove(root_copy.find('{http://www.w3.org/2000/svg}desc'))
rem_text = " ".join(get_all_text(root_copy).split())
for sl in source_labels:
    norm_sl = " ".join(sl.split())
    rem_text = rem_text.replace(norm_sl, "", 1)
rem_text = " ".join(rem_text.split())
assert rem_text == "", f"Extra text found: '{rem_text}'"
print("[PASS] 5. Exactly zero extra words or labels in SVG!")

# 6. Check banned style words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'callout', 'takeaway']
found_banned = []
for ft in full_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', ft.lower())
    for f in forbidden:
        if f in words:
            found_banned.append((f, ft))
assert len(found_banned) == 0, f"Found banned words: {found_banned}"
print("[PASS] 6. Zero banned style words printed as text!")

# 7. Check orange usage
raw_svg = open("comp_scope_final.svg").read()
orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"Orange count: {len(orange_matches)}")
assert len(orange_matches) >= 1
b2_elem = root.find('.//*[@id="block-2"]')
b2_str = ET.tostring(b2_elem, encoding="unicode")
b2_oranges = re.findall(r'#db8129', b2_str, re.IGNORECASE)
assert len(b2_oranges) == len(orange_matches), "Orange must only be used on Block 2!"
print("[PASS] 7. Orange strictly isolated to Block 2 (the single most important item)!")

print("\n>>> ALL TESTS PASSED TO PERFECTION! <<<")
