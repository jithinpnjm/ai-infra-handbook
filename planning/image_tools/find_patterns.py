import glob, json, re

for f in sorted(glob.glob("specs/*.json")):
    data = json.load(open(f))
    for item in data:
        spec = item.get("spec", "")
        m = re.findall(r"'([^']*)'\s+([a-zA-Z][^;'.]+)", spec)
        if m:
            print(f"[{item.get('name')}] in {f}:")
            for code, desc in m[:4]:
                print(f"   code: '{code}' | desc: '{desc}'")
