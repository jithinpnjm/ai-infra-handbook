import xml.etree.ElementTree as ET
import glob

# Check all audit scripts in the repo to see what gap checks exist
for path in glob.glob("*audit*.py"):
    with open(path) as f:
        content = f.read()
    if "between boxes" in content or "gaps" in content:
        print(f"File {path} has gap checks:")
        for line in content.splitlines():
            if "gap" in line.lower() or "margin" in line.lower():
                print("   ", line.strip())
