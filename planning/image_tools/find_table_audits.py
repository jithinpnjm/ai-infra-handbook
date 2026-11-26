import glob, re

for f in sorted(glob.glob("*.py")):
    try:
        content = open(f).read()
        if "expected_labels" in content:
            m = re.search(r'expected_labels\s*=\s*\[(.*?)\]', content, re.DOTALL)
            if m:
                # check if there are any table-related specs
                labels_str = m.group(1)
                labels = re.findall(r'"([^"]+)"', labels_str)
                if any("table" in l.lower() or "need" in l.lower() or "slurm" in l.lower() or "mig" in l.lower() for l in labels):
                    print(f"File: {f}")
                    for l in labels[:10]:
                        print(f"   {l}")
                    print("---")
    except Exception as e:
        pass
