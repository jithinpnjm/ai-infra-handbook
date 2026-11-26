import os, glob, re

for f in sorted(glob.glob("*.py")):
    content = open(f).read()
    if "expected_labels" in content:
        # check if it mentions colon or quotes
        m = re.findall(r'expected_labels\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if m:
            labels_str = m[0]
            # print if matches some interesting pattern
            for line in labels_str.splitlines():
                if "node" in line.lower() or "warm" in line.lower() or "cold" in line.lower() or "created" in line.lower():
                    print(f"{f}: {line.strip()}")
