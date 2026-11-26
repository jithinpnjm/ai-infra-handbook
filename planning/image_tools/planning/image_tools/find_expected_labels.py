import glob
import re

for f in sorted(glob.glob("planning/image_tools/*.py")):
    try:
        content = open(f).read()
        if "expected_labels =" in content:
            # find the block
            idx = content.find("expected_labels =")
            snippet = content[idx:idx+800]
            print("=== File:", f)
            print(snippet[:400])
    except Exception as e:
        pass
