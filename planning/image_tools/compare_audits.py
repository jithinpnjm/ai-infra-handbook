import glob, json, re

# Find python files that have expected_labels and their spec
audits = [
    ("planning/image_tools/audit_candidate_engines.py", "p4-0404-template-engines-map"),
    ("planning/image_tools/audit_candidate_startup.py", "p3-2022-startup-remedies"),
    ("planning/image_tools/audit_eight_rules.py", "p3-0601-eight-invariants"),
    ("planning/image_tools/audit_final_verification.py", "p3-0301-numeric-traps"),
    ("planning/image_tools/audit_lost_update_script.py", "p3-0306-lost-update"),
    ("planning/image_tools/check_prefix_spec.py", "p3-2022-prefix-cache-keys"),
    ("planning/image_tools/test_audit_long_running_ux.py", "p3-0308-long-running-ux"),
    ("planning/image_tools/test_audit_p4_0404.py", "p4-0404-merge-walkthrough"),
]

# Map name to spec
name_to_spec = {}
for f in glob.glob("specs/*.json"):
    for item in json.load(open(f)):
        name_to_spec[item.get("name")] = item

for py_path, spec_name in audits:
    print(f"\n==================== {spec_name} ====================")
    spec_item = name_to_spec.get(spec_name, {})
    print("SPEC TITLE:", spec_item.get("title"))
    print("SPEC TEXT:", spec_item.get("spec")[:200] + "...")
    
    # Read py file
    txt = open(py_path).read()
    m = re.search(r"expected_labels\s*=\s*\[(.*?)\]", txt, re.DOTALL)
    if m:
        labels_code = m.group(0)
        # exec in sandbox
        loc = {}
        exec(labels_code, {}, loc)
        labels = loc["expected_labels"]
        print(f"EXPECTED LABELS ({len(labels)} items):")
        for i, l in enumerate(labels, 1):
            print(f"  {i:2d}. {l[:70]}")
