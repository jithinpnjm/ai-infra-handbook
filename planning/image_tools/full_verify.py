import xml.etree.ElementTree as ET
import re

tree = ET.parse('final_test.svg')
root = tree.getroot()

# Check root attributes
assert root.attrib['viewBox'] == '0 0 1600 1200'
assert root.attrib['width'] == '1600'
assert root.attrib['height'] == '1200'

# Check first children
children = list(root)
first_two = [c.tag.split('}')[-1] for c in children[:2]]
assert first_two == ['title', 'desc'], f"First children should be title, desc; got {first_two}"

# Check required texts
required_labels = [
    'When the method itself fails: four traps and the counter-move',
    'The counter does not exist',
    'some resources expose only some of utilisation, saturation and errors',
    'mark the empty cell as a known unknown and say so in the report; do not read an empty cell as healthy',
    'The interval hides the problem',
    'a one-minute average shows a device at 80% while one-second samples show bursts to 100% with queueing (Case 1)',
    'shorten the interval before you move on',
    'The measurement disturbs the system',
    'profilers, tracers and heavy sampling use CPU and can turn a rare stall into a constant one on a GPU node',
    'start with cheap counters; turn on heavy tools only for a short, announced window',
    'The first explanation feels complete',
    'you find a real fault, fix it, and stop, but it explains only a fraction of the slowdown',
    'check the fix against the original problem statement; if step time did not return to baseline, the investigation is not finished',
    'A method gives you a shape, not a guarantee',
    'Common mistakes: favourite tool first, tunables changed without a hypothesis or baseline, several changes at once, failed experiments not reverted, trusting GPU-Util or load average as a verdict, optimising off the critical path, benchmarking the load generator or a warm cache, ignoring corrected ECC, link retrains and PCIe replays',
    'Check that your fix explains the bulk of the symptom before you close an investigation'
]

text_nodes = root.findall('.//{http://www.w3.org/2000/svg}text')
extracted_texts = []
for t in text_nodes:
    fs = float(t.attrib.get('font-size', '0'))
    assert fs >= 24, f"Text font size {fs} < 24 in {t.attrib}"
    tspans = t.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        joined = " ".join([re.sub(r'\s+', ' ', (ts.text or '').strip()) for ts in tspans])
        extracted_texts.append(joined)
    else:
        text_val = re.sub(r'\s+', ' ', (t.text or '').strip())
        extracted_texts.append(text_val)

for req in required_labels:
    matches = [txt for txt in extracted_texts if txt == req]
    assert len(matches) == 1, f"Required label '{req}' matched {len(matches)} times!"

step_numbers = ['1', '2', '3', '4']
for sn in step_numbers:
    matches = [txt for txt in extracted_texts if txt == sn]
    assert len(matches) == 1, f"Step number '{sn}' matched {len(matches)} times!"

assert len(extracted_texts) == 20, f"Expected 20 text items, got {len(extracted_texts)}"

# Check for forbidden style words
for txt in extracted_texts:
    for word in ['orange', 'green', 'grey', 'bold', 'monospace', 'arrow']:
        assert not re.search(rf'\b{word}\b', txt, re.IGNORECASE), f"Forbidden style word '{word}' found in: {txt}"

print("All verifications passed 100% successfully!")
