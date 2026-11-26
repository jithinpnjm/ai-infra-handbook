import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_and_or_trap.svg")
root = tree.getroot()

all_full_texts = []
for t in root.iter("{http://www.w3.org/2000/svg}text"):
    full = " ".join("".join(t.itertext()).split())
    all_full_texts.append(full)

print(f"Total extracted <text> elements: {len(all_full_texts)}")
for i, ft in enumerate(all_full_texts, 1):
    print(f"{i:2d}. '{ft}'")

expected = [
    "a && b || c is not an if/else",
    "if a; then b; else c; fi",
    "yes",
    "no",
    "start",
    "a succeeds?",
    "b",
    "c",
    "end",
    "a && b || c",
    "yes",
    "yes",
    "a failed",
    "b failed",
    "start",
    "a succeeds?",
    "b",
    "b succeeded?",
    "end",
    "c",
    "c runs even though a succeeded",
    '[ -d "$d" ] || mkdir -p "$d"',
    "command -v nvidia-smi >/dev/null || exit 0",
    'cd "$dir" || exit 1',
    '[ -z "$x" ] && { echo "empty" >&2; exit 1; }',
    "&& runs the next command only if the last one succeeded; || only if it failed"
]

print("\n--- Verifying Exact Matches ---")
assert len(all_full_texts) == len(expected), f"Count mismatch: {len(all_full_texts)} != {len(expected)}"

for exp in expected:
    assert exp in all_full_texts, f"Missing: '{exp}'"

for ft in all_full_texts:
    assert ft in expected, f"Extra/unexpected: '{ft}'"

print("SUCCESS: 100% exact match of all text elements!")
