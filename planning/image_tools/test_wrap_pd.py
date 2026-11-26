import re

pd = "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns"

# Try wrapping with max_len <= 38:
pd_lines = [
    "Gpu(index, name, temp_c, util_pct,",
    "mem_used_mib, mem_total_mib,",
    "ecc_uncorrected); _int maps empty,",
    "[N/A] and [Not Supported] to None;",
    "a line without exactly 7 columns",
    "raises ValueError unexpected",
    "nvidia-smi columns"
]

reconstructed = " ".join(pd_lines)
assert re.sub(r'\s+', ' ', reconstructed).strip() == pd
print(f"Reconstructed: {reconstructed == pd}")
for i, l in enumerate(pd_lines):
    mono_w = len(l) * 14.88
    sans_w = len(l) * 14.4
    print(f"  L{i+1} (len={len(l):2d}): '{l}' -> mono_w={mono_w:.1f}, sans_w={sans_w:.1f}")

