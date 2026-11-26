import json

with open("specs/p3_20_19.json") as f:
    data = json.load(f)

item = [x for x in data if x.get("name") == "p3-2019-stream-good-event"][0]
print("Title from JSON:", item["title"])
print("Spec from JSON:", item["spec"])
