import glob, json, os, re

scripts = glob.glob("*.py")
for s in sorted(scripts):
    content = open(s).read()
    m = re.search(r"(?:source_labels|expected_source_labels|expected_labels)\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if m:
        labels_block = m.group(1)
        title_m = re.search(r'"([^"]+)"', labels_block)
        if title_m:
            title = title_m.group(1)
            for spec_file in glob.glob("specs/*.json"):
                try:
                    data = json.load(open(spec_file))
                    for item in data:
                        if item.get("title") == title:
                            print(f"File {s} matches spec {item.get('name')} in {spec_file}")
                            labels = re.findall(r'"([^"]+)"', labels_block)
                            print(f"  Spec: {item.get('spec')}")
                            print(f"  Labels ({len(labels)}):")
                            for l in labels:
                                print(f"    - {l}")
                            print("="*60)
                except Exception as e:
                    pass
