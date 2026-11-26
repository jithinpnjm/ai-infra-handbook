import json

data = json.load(open("specs/v1_all.json"))
print(f"Total items in v1_all: {len(data)}")
for i, item in enumerate(data):
    spec = item.get("spec", "")
    if "Flow:" in spec:
        print(f"[{i}] {item.get('name')}: {item.get('title')}")
        print("   Spec:", spec)
