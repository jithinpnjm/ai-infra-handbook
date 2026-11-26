import re

rd = "problems for: expected 8 GPUs but found a different count; temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes"

rd_lines = [
    "problems for: expected 8 GPUs but",
    "found a different count; temp above 85;",
    "uncorrected ECC non-zero; plus XID in",
    "a set of known codes"
]

reconstructed = " ".join(rd_lines)
assert re.sub(r'\s+', ' ', reconstructed).strip() == rd
print(f"Reconstructed: {reconstructed == rd}")
for i, l in enumerate(rd_lines):
    mono_w = len(l) * 14.88
    sans_w = len(l) * 14.4
    print(f"  L{i+1} (len={len(l):2d}): '{l}' -> mono_w={mono_w:.1f}, sans_w={sans_w:.1f}")

