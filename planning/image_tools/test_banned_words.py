import re

labels = [
    "Top five clients: what each pipeline stage does to the data",
    "awk print $1",
    "keep the client address field",
    "sort",
    "equal addresses become neighbours",
    "uniq -c",
    "count each run of equal lines",
    "awk print $2, $1",
    "put address first, count second",
    "sort -k2,2nr -k1,1",
    "awk NR<=5",
    "rank by count, address breaks ties; awk instead of head so pipefail never reports exit 141",
    "203.0.113.77 362",
    "203.0.113.18 68",
    "203.0.113.17 62",
    "203.0.113.24 62",
    "198.51.100.22 60",
    "Common wrong approach",
    "cut -d space -f1 access.log | uniq -c | sort -rn | head -3 skips the first sort, so uniq counted only neighbouring lines and printed 3 203.0.113.77 twice",
    "Cross-check: count the same thing with an awk array and compare",
    "Never report a number you have produced only one way."
]

step_numbers = ["1", "2", "3", "4", "5", "6"]

all_texts = labels + step_numbers

banned = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']

print(f"Total texts: {len(all_texts)}")
for t in all_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for b in banned:
        if b in words:
            print(f"FAILED: '{b}' found in '{t}'")
print("Banned words check complete: PASS if no FAILED above.")
