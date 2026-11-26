import glob, re

for f in sorted(glob.glob("*.py")):
    try:
        content = open(f).read()
        if "decision table" in content.lower():
            print(f"File: {f}")
            for line in content.splitlines():
                if "decision table" in line.lower():
                    print(f"  {line}")
    except Exception as e:
        pass
