import glob, json, re

for f in sorted(glob.glob("specs/*.json")):
    data = json.load(open(f))
    for item in data:
        spec = item.get("spec", "")
        if "table" in spec.lower():
            m = re.findall(r"([a-zA-Z\s]+table[a-zA-Z\s]*'[^']*')", spec, re.IGNORECASE)
            if m:
                print(f"[{item.get('name')}]:")
                for x in m:
                    print("  ", x.strip())
