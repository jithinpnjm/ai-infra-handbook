import glob, json, re

# Find all audit scripts that load a spec from specs/*.json
for f in sorted(glob.glob("*.py")):
    try:
        txt = open(f).read()
        if "re.findall(r\"'([^']*)\'\"" in txt and "spec_item" in txt:
            print("Found re.findall in:", f)
            for line in txt.splitlines():
                if "spec_item =" in line or "data = json.load" in line:
                    print("  ", line)
    except:
        pass
