import re

ts = "canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, empty output, missing GPU; then CliRunner with a stubbed executor asserting exit codes and JSON shape"

ts_lines = [
    "canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, empty output,",
    "missing GPU; then CliRunner with a stubbed executor asserting exit codes and JSON shape"
]
assert re.sub(r'\s+', ' ', " ".join(ts_lines)).strip() == ts

ts_lines3 = [
    "canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count,",
    "empty output, missing GPU; then CliRunner with a stubbed executor asserting",
    "exit codes and JSON shape"
]
assert re.sub(r'\s+', ' ', " ".join(ts_lines3)).strip() == ts

print("2 lines:")
for l in ts_lines:
    print(f"  len={len(l):2d}: mono_w={len(l)*14.88:.1f}, sans_w={len(l)*14.4:.1f}")

print("\n3 lines:")
for l in ts_lines3:
    print(f"  len={len(l):2d}: mono_w={len(l)*14.88:.1f}, sans_w={len(l)*14.4:.1f}")

