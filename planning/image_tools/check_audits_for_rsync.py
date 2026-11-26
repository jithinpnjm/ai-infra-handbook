import glob
import re

for f in sorted(glob.glob("*.py")):
    txt = open(f).read()
    m = re.search(r"expected_labels\s*=\s*\[(.*?)\]", txt, re.DOTALL)
    if m:
        block = m.group(1)
        # check if any label mentions 'skip' or 'rsync' or 'quick check'
        if any(w in block for w in ["rsync", "quick check", "skip", "safeguard", "checksum"]):
            print("Found in", f)
            print(block[:300])
