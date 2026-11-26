import re
import xml.etree.ElementTree as ET

def generate_svg():
    svg_lines = []
    svg_lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg_lines.append('  <title>Numeric types and the quiet traps they hide</title>')
    svg_lines.append('  <desc>Visual infographic explaining Python numeric types, operator rules, and infrastructure arithmetic traps.</desc>')
    svg_lines.append('  <!-- Background -->')
    svg_lines.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    svg_lines.append('')
    svg_lines.append('  <!-- Main Title (48px bold) -->')
    svg_lines.append('  <text x="800" y="70" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Numeric types and the quiet traps they hide</text>')
    svg_lines.append('')
    
    # Left container: Table of six types
    svg_lines.append('  <!-- ==================== TABLE OF SIX TYPES ==================== -->')
    svg_lines.append('  <rect x="40" y="110" width="860" height="670" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    
    # Type 1: int (h=84, y=124..208)
    svg_lines.append('  <!-- Type 1: int -->')
    svg_lines.append('  <rect x="54" y="124" width="832" height="84" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    svg_lines.append('  <g transform="translate(68, 138)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <rect x="6" y="6" width="44" height="44" rx="8"/>')
    svg_lines.append('    <path d="M22 18 L28 18 L28 38 M23 38 L33 38"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="140" y="160" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="140" dy="0">int: arbitrary precision, no overflow;</tspan>')
    svg_lines.append('    <tspan x="140" dy="28">0x1f, 0o17, 0b101, 1_000_000</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Type 2: float (h=140, y=218..358)
    svg_lines.append('  <!-- Type 2: float -->')
    svg_lines.append('  <rect x="54" y="218" width="832" height="140" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    svg_lines.append('  <g transform="translate(68, 260)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <circle cx="28" cy="28" r="21"/>')
    svg_lines.append('    <path d="M14 28 Q21 16 28 28 T42 28"/>')
    svg_lines.append('    <circle cx="36" cy="38" r="3" fill="#207448"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="140" y="254" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="140" dy="0">float: IEEE 754 double, about 15 to 17</tspan>')
    svg_lines.append('    <tspan x="140" dy="28">significant digits; 0.1 + 0.2 != 0.3,</tspan>')
    svg_lines.append('    <tspan x="140" dy="28">use math.isclose; float("inf"),</tspan>')
    svg_lines.append('    <tspan x="140" dy="28">nan never equals itself</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Type 3: complex (h=60, y=368..428)
    svg_lines.append('  <!-- Type 3: complex -->')
    svg_lines.append('  <rect x="54" y="368" width="832" height="60" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    svg_lines.append('  <g transform="translate(68, 370)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <line x1="8" y1="46" x2="48" y2="46"/>')
    svg_lines.append('    <line x1="12" y1="50" x2="12" y2="10"/>')
    svg_lines.append('    <line x1="12" y1="46" x2="40" y2="18"/>')
    svg_lines.append('    <circle cx="40" cy="18" r="4" fill="#207448"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="140" y="406" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">complex: 3 + 4j, rarely used in infra</text>')
    svg_lines.append('')

    # Type 4: bool (h=84, y=438..522)
    svg_lines.append('  <!-- Type 4: bool -->')
    svg_lines.append('  <rect x="54" y="438" width="832" height="84" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    svg_lines.append('  <g transform="translate(68, 452)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <rect x="6" y="14" width="44" height="28" rx="14"/>')
    svg_lines.append('    <circle cx="36" cy="28" r="8" fill="#207448"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="140" y="474" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="140" dy="0">bool: subclass of int,</tspan>')
    svg_lines.append('    <tspan x="140" dy="28">True == 1, True + True == 2</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Type 5: decimal.Decimal (ORANGE, h=88, y=532..620)
    svg_lines.append('  <!-- Type 5: decimal.Decimal (orange) -->')
    svg_lines.append('  <rect x="54" y="532" width="832" height="88" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="2.5"/>')
    svg_lines.append('  <g transform="translate(68, 548)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <circle cx="28" cy="28" r="21"/>')
    svg_lines.append('    <path d="M28 14 L28 42 M22 20 Q28 16 34 20 Q36 24 28 27 Q20 30 22 35 Q28 40 34 36"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="140" y="568" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="140" dy="0">decimal.Decimal: exact decimal arithmetic</tspan>')
    svg_lines.append('    <tspan x="140" dy="28">for money and billing; construct from strings</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Type 6: fractions.Fraction (h=60, y=630..690)
    svg_lines.append('  <!-- Type 6: fractions.Fraction -->')
    svg_lines.append('  <rect x="54" y="630" width="832" height="60" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    svg_lines.append('  <g transform="translate(68, 632)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <circle cx="28" cy="16" r="6" fill="#207448"/>')
    svg_lines.append('    <line x1="10" y1="28" x2="46" y2="28"/>')
    svg_lines.append('    <circle cx="28" cy="40" r="6" fill="#207448"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="140" y="668" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">fractions.Fraction: exact rational numbers</text>')
    svg_lines.append('')

    # Right container: Operators Panel
    svg_lines.append('  <!-- ==================== RIGHT PANEL: OPERATORS ==================== -->')
    svg_lines.append('  <rect x="940" y="110" width="620" height="670" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    
    # Operators Header (h=56, y=124..180)
    svg_lines.append('  <!-- Operators Header -->')
    svg_lines.append('  <rect x="956" y="124" width="588" height="56" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    svg_lines.append('  <g transform="translate(970, 126)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <circle cx="26" cy="26" r="18"/>')
    svg_lines.append('    <path d="M18 26 L34 26 M26 18 L26 34"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="1040" y="162" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Operators</text>')
    svg_lines.append('')

    # Op 1: / (1-line, h=52, y=188..240)
    svg_lines.append('  <!-- Op 1 -->')
    svg_lines.append('  <rect x="956" y="188" width="588" height="52" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1"/>')
    svg_lines.append('  <text x="976" y="222" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">/ is always true division (float)</text>')
    svg_lines.append('')

    # Op 2: // (2-lines, h=78, y=246..324)
    svg_lines.append('  <!-- Op 2 -->')
    svg_lines.append('  <rect x="956" y="246" width="588" height="78" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1"/>')
    svg_lines.append('  <text x="976" y="278" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="976" dy="0">// floors toward negative</tspan>')
    svg_lines.append('    <tspan x="976" dy="28">infinity: -7 // 2 == -4</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Op 3: % (1-line, h=52, y=330..382)
    svg_lines.append('  <!-- Op 3 -->')
    svg_lines.append('  <rect x="956" y="330" width="588" height="52" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1"/>')
    svg_lines.append('  <text x="976" y="364" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">% takes the sign of the divisor</text>')
    svg_lines.append('')

    # Op 4: divmod(a, b) (1-line, h=52, y=388..440)
    svg_lines.append('  <!-- Op 4 -->')
    svg_lines.append('  <rect x="956" y="388" width="588" height="52" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1"/>')
    svg_lines.append('  <text x="976" y="422" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">divmod(a, b)</text>')
    svg_lines.append('')

    # Op 5: round() (2-lines, h=78, y=446..524)
    svg_lines.append('  <!-- Op 5 -->')
    svg_lines.append('  <rect x="956" y="446" width="588" height="78" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1"/>')
    svg_lines.append('  <text x="976" y="478" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="976" dy="0">round() rounds half to even:</tspan>')
    svg_lines.append('    <tspan x="976" dy="28">round(2.5) == 2</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Op 6: chained comparison (1-line, h=52, y=530..582)
    svg_lines.append('  <!-- Op 6 -->')
    svg_lines.append('  <rect x="956" y="530" width="588" height="52" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1"/>')
    svg_lines.append('  <text x="976" y="564" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">chained comparison 1 &lt;= x &lt; 10</text>')
    svg_lines.append('')

    # Op 7: bitwise (2-lines, h=78, y=588..666)
    svg_lines.append('  <!-- Op 7 -->')
    svg_lines.append('  <rect x="956" y="588" width="588" height="78" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1"/>')
    svg_lines.append('  <text x="976" y="620" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="976" dy="0">bitwise &amp; | ^ ~ &lt;&lt; &gt;&gt; for IP</tspan>')
    svg_lines.append('    <tspan x="976" dy="28">and mask: 0xFF &amp; addr</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Op 8: random (2-lines, h=78, y=672..750)
    svg_lines.append('  <!-- Op 8 -->')
    svg_lines.append('  <rect x="956" y="672" width="588" height="78" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1"/>')
    svg_lines.append('  <text x="976" y="704" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="976" dy="0">random is not for security,</tspan>')
    svg_lines.append('    <tspan x="976" dy="28">use secrets</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Bottom worked examples (y=820..1030, h=210)
    svg_lines.append('  <!-- ==================== WORKED EXAMPLES ==================== -->')
    # Row 1: Ex 1 and Ex 2 (y=820, h=94)
    # Ex 1: disk_bytes (x=40..780, w=740, h=94)
    svg_lines.append('  <!-- Example 1: disk_bytes -->')
    svg_lines.append('  <rect x="40" y="820" width="740" height="94" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg_lines.append('  <g transform="translate(56, 839)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <ellipse cx="28" cy="14" rx="20" ry="8"/>')
    svg_lines.append('    <path d="M8 14 V42 C8 46.4 17 50 28 50 C39 50 48 46.4 48 42 V14"/>')
    svg_lines.append('    <path d="M8 28 C8 32.4 17 36 28 36 C39 36 48 32.4 48 28"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="128" y="856" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="128" dy="0">disk_bytes / gib with gib = 1024 ** 3</tspan>')
    svg_lines.append('    <tspan x="128" dy="28">gives 3577.0 GiB for 3_840_755_982_336 bytes</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Ex 2: free_pct (x=820..1560, w=740, h=94)
    svg_lines.append('  <!-- Example 2: free_pct -->')
    svg_lines.append('  <rect x="820" y="820" width="740" height="94" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg_lines.append('  <g transform="translate(836, 839)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <path d="M28 8 L46 16 V30 C46 41 38 49 28 52 C18 49 10 41 10 30 V16 Z"/>')
    svg_lines.append('    <path d="M20 30 L26 36 L36 24"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="908" y="856" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="908" dy="0">free_pct = 100 * free / total</tspan>')
    svg_lines.append('    <tspan x="908" dy="28">if total else 0.0 guards divide by zero</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('')

    # Row 2: Ex 3 and Ex 4 (y=934, h=76)
    # Ex 3: timeout (x=40..780, w=740, h=76)
    svg_lines.append('  <!-- Example 3: timeout -->')
    svg_lines.append('  <rect x="40" y="934" width="740" height="76" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg_lines.append('  <g transform="translate(56, 944)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <circle cx="28" cy="28" r="21"/>')
    svg_lines.append('    <polyline points="28 16 28 28 36 34"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="128" y="980" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">timeout = base * 2 ** attempt</text>')
    svg_lines.append('')

    # Ex 4: pages, rem (x=820..1560, w=740, h=76)
    svg_lines.append('  <!-- Example 4: pages, rem -->')
    svg_lines.append('  <rect x="820" y="934" width="740" height="76" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8"/>')
    svg_lines.append('  <g transform="translate(836, 944)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <rect x="8" y="8" width="40" height="40" rx="6"/>')
    svg_lines.append('    <line x1="16" y1="20" x2="40" y2="20"/>')
    svg_lines.append('    <line x1="16" y1="28" x2="40" y2="28"/>')
    svg_lines.append('    <line x1="16" y1="36" x2="30" y2="36"/>')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="908" y="980" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">pages, rem = divmod(total_items, 100)</text>')
    svg_lines.append('')

    # Bottom takeaway bar (y=1050..1160, h=110)
    svg_lines.append('  <!-- ==================== TAKEAWAY BAR ==================== -->')
    svg_lines.append('  <rect x="40" y="1050" width="1520" height="110" rx="12" fill="#207448"/>')
    svg_lines.append('  <text x="800" y="1092" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">')
    svg_lines.append('    <tspan x="800" dy="0">Compare floats with tolerance, use // versus / on purpose,</tspan>')
    svg_lines.append('    <tspan x="800" dy="32">remember bool is an int, and use the ipaddress module instead of string IP arithmetic</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('</svg>')
    
    return "\n".join(svg_lines)

svg_str = generate_svg()
with open("test_candidate.svg", "w") as f:
    f.write(svg_str)

# Run strict audit on test_candidate.svg
tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == "title"
assert second_tag == "desc"

# 2. Dimensions
W = float(root.attrib.get("width"))
H = float(root.attrib.get("height"))
vb = [float(x) for x in root.attrib.get("viewBox").split()]
print(f"2. Canvas: W={W}, H={H}, viewBox={vb}")
assert W == 1600
assert 900 <= H <= 1200
assert vb == [0, 0, 1600, H]

# 3. Text font-size >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size', '0'))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if fs == 0 and tspans:
        fs = float(tspans[0].attrib.get('font-size', '0'))
    assert fs >= 24, f"Font size {fs} < 24 for '{full_text}'"
    for tsp in tspans:
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24"
    text_elements.append((full_text, fs))

print(f"3. Text elements count: {len(text_elements)} (all font-size >= 24px)")

# 4. Expected labels
expected_labels = [
    "Numeric types and the quiet traps they hide",
    "int: arbitrary precision, no overflow; 0x1f, 0o17, 0b101, 1_000_000",
    'float: IEEE 754 double, about 15 to 17 significant digits; 0.1 + 0.2 != 0.3, use math.isclose; float("inf"), nan never equals itself',
    "complex: 3 + 4j, rarely used in infra",
    "bool: subclass of int, True == 1, True + True == 2",
    "decimal.Decimal: exact decimal arithmetic for money and billing; construct from strings",
    "fractions.Fraction: exact rational numbers",
    "Operators",
    "/ is always true division (float)",
    "// floors toward negative infinity: -7 // 2 == -4",
    "% takes the sign of the divisor",
    "divmod(a, b)",
    "round() rounds half to even: round(2.5) == 2",
    "chained comparison 1 <= x < 10",
    "bitwise & | ^ ~ << >> for IP and mask: 0xFF & addr",
    "random is not for security, use secrets",
    "disk_bytes / gib with gib = 1024 ** 3 gives 3577.0 GiB for 3_840_755_982_336 bytes",
    "free_pct = 100 * free / total if total else 0.0 guards divide by zero",
    "timeout = base * 2 ** attempt",
    "pages, rem = divmod(total_items, 100)",
    "Compare floats with tolerance, use // versus / on purpose, remember bool is an int, and use the ipaddress module instead of string IP arithmetic"
]

found_texts = [t for t, fs in text_elements]
print(f"4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count==1, got {cnt}"

extras = [t for t in found_texts if t not in expected_labels]
print(f"   Extras: {extras}")
assert len(extras) == 0, f"Unexpected extra texts: {extras}"
print("   All expected labels matched 1-to-1! Exactly zero extra texts!")

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'"
print("5. Forbidden words: PASS!")

# 6. Orange check (#db8129)
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"6. Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 5, f"Unexpected orange count: {len(oranges)}"

# 7. No arrows
markers = re.findall(r'marker-end', svg_str)
print(f"7. Arrow markers count: {len(markers)}")
assert len(markers) == 0, f"Expected 0 arrows, got {len(markers)}"

print("\nALL AUDITS PASSED PERFECTLY!")
