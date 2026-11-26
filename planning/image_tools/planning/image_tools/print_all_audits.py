import glob, re

for f in sorted(glob.glob("planning/image_tools/audit_*.py") + glob.glob("planning/image_tools/test_audit_*.py") + glob.glob("planning/image_tools/verify_*.py")):
    content = open(f).read()
    m = re.search(r"expected_labels\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if m:
        labels = [l.strip("\"'") for l in re.findall(r"[\"'](.*?)[\"']", m.group(1))]
        if labels:
            print(f"=== {f} ({len(labels)} labels) ===")
            for l in labels:
                print("   ", l[:80])
