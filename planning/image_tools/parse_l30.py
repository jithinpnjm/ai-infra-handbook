import json
import re

spec_file = "specs/v1_30.json"
data = json.load(open(spec_file))
item = [x for x in data if x.get("name") == "l30-rsync-decide"][0]

print("Title:", item.get("title"))
print("Spec:", item.get("spec"))
print("Alt:", item.get("alt"))
print("Cap:", item.get("cap"))
