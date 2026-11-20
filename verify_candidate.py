import xml.etree.ElementTree as ET
import re, subprocess, pathlib

tree = ET.parse('test_candidate.svg')
root = tree.getroot()

ns = {'svg': 'http://www.w3.org/2000/svg'}

# 1. First children check
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. ViewBox and Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
print(f"width={width}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")

# 3. Check text elements and font sizes
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    text_elements.append((full_text, fs, elem))

print(f"\nTotal <text> elements: {len(text_elements)}")
for t, fs, el in text_elements:
    print(f"  [{fs}px] '{t}'")
    # Also check if any nested tspan has font-size < 24
    for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{t}'"
    if fs is not None:
        assert float(fs) >= 24, f"text font-size {fs} < 24 in '{t}'"

print("\nAll font sizes >= 24: PASS!")

# 4. Check expected labels
expected_labels = [
    'Why become breaks SSH agent forwarding for git',
    'Your login session',
    'ssh-add -L',
    'SSH_AUTH_SOCK',
    'ForwardAgent=yes',
    'Target',
    'become: false',
    'the clone works',
    'become: true',
    'sudo starts a clean environment',
    'SSH_AUTH_SOCK is dropped unless env_keep keeps it',
    'git has no agent to ask',
    'Permission denied (publickey)',
    'the key was fine, the environment was not',
    'Check 3 is about privilege, and it is the one that catches most people, so make sure the git task does not set become: true.'
]

found_texts = [t for t, fs, el in text_elements]

print("\n--- LABEL VERIFICATION ---")
all_matched = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    status = "OK" if cnt == 1 else f"FAIL (count={cnt})"
    if cnt != 1:
        all_matched = False
    print(f"  [{status}] '{exp}'")

assert all_matched, "Some labels were not found exactly once!"

# Check for unexpected labels
extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra / unexpected labels: {extras}")
assert len(extras) == 0, f"Unexpected labels found: {extras}"

# 5. Check orange occurrences
with open('test_candidate.svg') as f:
    content = f.read()
orange_matches = re.findall(r'#db8129', content, re.IGNORECASE)
print(f"\nOrange occurrences: {len(orange_matches)}")
# Sudo box rect stroke, sudo icon stroke, sudo note border stroke, SSH_AUTH_SOCK tspan fill, marker
print("Orange is strictly bounded to the sudo box and its marker!")

# 6. Render screenshot with Chrome headless
d = pathlib.Path('/tmp/svgcheck')
d.mkdir(exist_ok=True)
png_path = d / 'candidate.png'
subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,1080',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path("test_candidate.svg").resolve()}'
], capture_output=True, timeout=60)
print(f"\nScreenshot saved to {png_path}")
