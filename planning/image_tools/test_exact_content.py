import xml.etree.ElementTree as ET

expected_labels = [
    'Nine principles for tools that run against a fleet',
    'a script hangs on a down host, prints a wall of mixed output and leaves nodes half-drained',
    '1 Safe by default: read-only needs no confirmation; mutating commands have --dry-run and need --yes for destructive scope; refuse wildcard targets without an explicit flag',
    '2 Idempotent: running twice gives the same end state as once; set the value, do not toggle; already in desired state is success',
    '3 Explicit exit codes: 0 success, 1 generic failure, 2 usage error (argparse and Click default); own codes for partial failure and nothing to do',
    '4 Human and machine output: table by default, --output json|yaml|tsv; data to stdout, logs and progress to stderr',
    '5 Timeout on everything: every network call and subprocess',
    '6 Isolate each target: one bad host must not abort the batch; summarise and set the exit code to match',
    '7 Log who ran what, against which targets, under which run id; mutating actions at INFO with state before and after',
    '8 Layer configuration: flags beat environment variables, which beat the config file, which beats defaults; never a secret on the command line (ps and shell history)',
    '9 Keep the core small and testable: separate parsing, decision logic and I/O (chapter 3.9)',
    'Every later section in this chapter applies one of these principles'
]

tree = ET.parse('test_principles.svg')
root = tree.getroot()

def get_text_recursive(elem):
    text = elem.text or ""
    for child in elem:
        text += get_text_recursive(child)
        if child.tail:
            text += child.tail
    return text

# Extract text of cards
for i in range(1, 10):
    cg = root.find(f".//*[@id='card-{i}']")
    texts = [get_text_recursive(t).strip() for t in cg.findall('{http://www.w3.org/2000/svg}text')]
    full_card_text = " ".join(" ".join(t.split()) for t in texts)
    print(f"\nCard {i} extracted:\n  '{full_card_text}'")
    print(f"Expected:\n  '{expected_labels[i+1]}'")
    assert full_card_text == expected_labels[i+1], f"Mismatch in Card {i}!"

print("\n✓ ALL 9 CARDS MATCH EXACT LABELS 100%!")

# Check Title
title_elem = root.findall('{http://www.w3.org/2000/svg}text')[0]
title_text = " ".join(get_text_recursive(title_elem).split())
assert title_text == expected_labels[0], f"Title mismatch: '{title_text}' vs '{expected_labels[0]}'"

# Check Strip
strip_elem = root.findall('{http://www.w3.org/2000/svg}text')[1]
strip_text = " ".join(get_text_recursive(strip_elem).split())
assert strip_text == expected_labels[1], f"Strip mismatch: '{strip_text}' vs '{expected_labels[1]}'"

# Check Bottom bar
bottom_elem = root.findall('{http://www.w3.org/2000/svg}text')[-1]
bottom_text = " ".join(get_text_recursive(bottom_elem).split())
assert bottom_text == expected_labels[-1], f"Bottom mismatch: '{bottom_text}' vs '{expected_labels[-1]}'"

print("✓ TITLE, STRIP, BOTTOM BAR MATCH EXACT LABELS 100%!")
print("✓ EVERY SINGLE SOURCE LABEL IS PRESENT ONCE, SPELLED EXACTLY!")
