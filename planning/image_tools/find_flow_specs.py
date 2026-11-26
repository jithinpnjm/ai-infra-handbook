import glob
import re

for f in sorted(glob.glob("**/*.py", recursive=True)):
    txt = open(f, errors='ignore').read()
    if "Flow:" in txt:
        print("Found 'Flow:' in", f)
        for line in txt.splitlines():
            if "Flow:" in line or "expected_labels" in line:
                print("  ", line[:120])
