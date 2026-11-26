import re
import xml.etree.ElementTree as ET

# 1. Parse XML
try:
    tree = ET.parse("output.svg")
    root = tree.getroot()
    print("XML Parsing: SUCCESS (valid XML)")
except Exception as e:
    print(f"XML Parsing: FAILED ({e})")
    exit(1)

# 2. Check title and desc
title_el = root.find('{http://www.w3.org/2000/svg}title')
desc_el = root.find('{http://www.w3.org/2000/svg}desc')
print(f"Title present: {title_el is not None} -> '{title_el.text if title_el is not None else ''}'")
print(f"Desc present : {desc_el is not None} -> '{desc_el.text if desc_el is not None else ''}'")

# 3. Check expected labels from prompt
expected_labels = [
    "Choosing command, shell, raw, script or a real module",
    "Is there a purpose-built module (package, service, user, file, lineinfile, template, sysctl, systemd, mount, cron)?",
    "use it: idempotent, supports check mode, returns structured results",
    "Does the target have Python?",
    "raw: plain SSH command with no module and no Python; bootstraps Python on minimal systems and devices",
    "Need pipes or redirects?",
    "shell: passes through /bin/sh; vulnerable to quoting and injection mistakes when variables are untrusted",
    "command: no shell, safest; no pipes, redirects or expansion",
    "Need to run a local script on the target?",
    "script: copies a local script to the target and runs it",
    "command and shell are not idempotent: add creates: or removes:, a guard task (a small check that decides whether the risky step should run), or changed_when and failed_when; a shell one-liner always reports changed, cannot be dry-run and hides intent",
    "a hostname from a ticket sneaks in a second command after a semicolon",
    "Prefer modules, and guard what you cannot avoid"
]

with open("output.svg") as f:
    svg_text = f.read()

# Extract all text inside <text> elements
texts_found = []
for t in root.iter('{http://www.w3.org/2000/svg}text'):
    full_t = "".join(t.itertext()).strip()
    full_t = re.sub(r'\s+', ' ', full_t)
    texts_found.append(full_t)

print("\n--- Texts extracted from SVG ---")
for idx, tf in enumerate(texts_found, 1):
    print(f"{idx:2d}. {tf}")

print("\n--- Checking Expected Content Labels ---")
all_labels_ok = True
for idx, exp in enumerate(expected_labels, 1):
    found = False
    for tf in texts_found:
        if exp == tf:
            found = True
            break
    if found:
        print(f"Label {idx:2d}: OK -> '{exp[:50]}...'")
    else:
        print(f"Label {idx:2d}: MISSING -> '{exp}'")
        all_labels_ok = False

if all_labels_ok:
    print("ALL 13 CONTENT LABELS FOUND EXACTLY ONCE!")

# 4. Check forbidden style words printed as text
forbidden_words = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']

forbidden_found = False
for tf in texts_found:
    words = re.findall(r'\b[a-zA-Z]+\b', tf.lower())
    for fw in forbidden_words:
        if fw in words:
            print(f"FORBIDDEN WORD '{fw}' FOUND IN TEXT: '{tf}'")
            forbidden_found = True

if not forbidden_found:
    print("NO FORBIDDEN WORDS FOUND IN ANY TEXT!")

# 5. Check font sizes
print("\n--- Checking font sizes in SVG ---")
font_sizes = []
for el in root.iter():
    fs = el.get('font-size')
    if fs:
        font_sizes.append(float(fs))

print(f"Found {len(font_sizes)} font-size declarations: min={min(font_sizes)}, max={max(font_sizes)}")
if min(font_sizes) < 24.0:
    print(f"FAILED: Font size smaller than 24px found: {min(font_sizes)}")
else:
    print(f"PASSED: No font size smaller than 24px (min is {min(font_sizes)}px)!")

# 6. Check arrows count
lines = root.findall('.//{http://www.w3.org/2000/svg}line')
arrow_lines = [l for l in lines if l.get('marker-end')]
print(f"\nArrow lines with marker-end: {len(arrow_lines)}")
for idx, a in enumerate(arrow_lines, 1):
    print(f"  Arrow {idx}: ({a.get('x1')}, {a.get('y1')}) -> ({a.get('x2')}, {a.get('y2')}) marker={a.get('marker-end')}")
