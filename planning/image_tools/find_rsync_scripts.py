import glob
import re

files = glob.glob("*.py")
for f in sorted(files):
    content = open(f).read()
    if "l30" in content or "rsync" in content:
        print("Found rsync/l30 in", f)
