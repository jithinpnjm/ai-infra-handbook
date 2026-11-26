import json

with open("planning/image_tools/specs/p3_03_06.json") as f:
    specs = json.load(f)

for s in specs:
    if s["name"] == "p3-0306-lost-update":
        print("Spec for p3-0306-lost-update:")
        print(s["spec"])
