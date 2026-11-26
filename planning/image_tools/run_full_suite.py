import re
import xml.etree.ElementTree as ET

tree = ET.parse("final_slurm_daemons.svg")
root = tree.getroot()

# 1. XML check
print("1. XML well-formed: PASS")

# 2. Dimensions check
w = root.get('width')
h = root.get('height')
vb = root.get('viewBox')
assert w == "1600" and h == "1200" and vb == "0 0 1600 1200"
print(f"2. Canvas: {w}x{h}, viewBox='{vb}': PASS")

# 3. First children check: <title> and <desc>
first_two = list(root)[:2]
assert first_two[0].tag.endswith('title')
assert first_two[1].tag.endswith('desc')
print("3. <title> and <desc> are first children: PASS")

# 4. Check all fonts >= 24px
small_fonts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = elem.get('font-size')
    if fs and float(fs) < 24:
        small_fonts.append((elem.text, fs))
for elem in root.iter('{http://www.w3.org/2000/svg}tspan'):
    fs = elem.get('font-size')
    if fs and float(fs) < 24:
        small_fonts.append((elem.text, fs))
assert len(small_fonts) == 0, f"Found small fonts: {small_fonts}"
print("4. All font sizes >= 24px: PASS")

# 5. Check banned style words
banned = ["orange", "green", "grey", "bold", "monospace", "arrow"]
with open("final_slurm_daemons.svg") as f:
    raw_svg = f.read()

# Extract text node contents only
text_contents = []
for elem in root.iter():
    if elem.text and elem.text.strip():
        text_contents.append(elem.text.strip())

found_banned = []
for txt in text_contents:
    for b in banned:
        if re.search(r'\b' + b + r'\b', txt, re.IGNORECASE):
            found_banned.append((b, txt))
assert len(found_banned) == 0, f"Found banned style words printed as text: {found_banned}"
print("5. Zero banned style words printed as text: PASS")

# 6. Check exact labels
cleaned_text = ' '.join(re.sub(r'<[^>]+>', ' ', raw_svg).split())
required_labels = [
    'The daemons',
    'Login / submit nodes',
    'Control plane',
    'Compute nodes (data plane)',
    'sbatch, srun, salloc, squeue, sinfo, scancel',
    'sacct, sacctmgr, sreport (accounting queries)',
    'slurmctld',
    'controller, port 6817',
    'queue, scheduler, node and job state',
    'backup slurmctld (optional)',
    'shared StateSaveLocation',
    'slurmdbd, port 6819',
    'accounting daemon',
    'MariaDB / MySQL',
    'accounting database',
    'slurmrestd (optional)',
    'REST API',
    'slurmd, port 6818',
    'slurmd',
    'slurmstepd',
    'one per job step per node',
    'application processes',
    'munge on every node',
    '(shared key, authenticates every request)',
    'RPC + munge credential',
    'RPC',
    'job and usage records',
    'launch and control RPCs',
    'runs your program',
    'srun talks to slurmd and slurmstepd directly'
]
for req in required_labels:
    norm_req = ' '.join(req.split())
    assert norm_req in cleaned_text, f"Missing required label: {req}"
print("6. All 29 content labels present and spelled exactly: PASS")

# 7. Check arrow count
arrows_g = root.find('.//{http://www.w3.org/2000/svg}g[@id="arrows"]')
paths = arrows_g.findall('{http://www.w3.org/2000/svg}path')
assert len(paths) == 15, f"Expected 15 arrows, got {len(paths)}"
print("7. Arrow count is exactly 15: PASS")

# 8. Check arrow crossings
def ccw(A, B, C):
    return (C[1]-A[1]) * (B[0]-A[0]) > (B[1]-A[1]) * (C[0]-A[0])

def intersect(p1, p2, p3, p4):
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False
    return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)

parsed_paths = []
for p in paths:
    d = p.get('d')
    tokens = d.replace('M', ' ').replace('L', ' ').split()
    pts = [(float(tokens[i]), float(tokens[i+1])) for i in range(0, len(tokens), 2)]
    parsed_paths.append(pts)

intersections = 0
for i in range(len(parsed_paths)):
    for j in range(i + 1, len(parsed_paths)):
        p1, p2 = parsed_paths[i], parsed_paths[j]
        for s1 in range(len(p1) - 1):
            a, b = p1[s1], p1[s1+1]
            for s2 in range(len(p2) - 1):
                c, d = p2[s2], p2[s2+1]
                if intersect(a, b, c, d):
                    intersections += 1
assert intersections == 0, f"Found {intersections} arrow intersections!"
print("8. Arrow intersections count is exactly 0: PASS")

print("\nALL SUITE TESTS PASSED 100%!")
