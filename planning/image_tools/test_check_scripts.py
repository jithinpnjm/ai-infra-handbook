import glob, re

for f in sorted(glob.glob("test_*padding*.py")):
    print("=== " + f + " ===")
    content = open(f).read()
    for line in content.splitlines()[:20]:
        print(" ", line)
