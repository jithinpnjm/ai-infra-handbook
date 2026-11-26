# Test the 5 lines wrap for Parser detail and 3 lines for Rules detail starting at x=144

p_lines = [
    "Gpu(index, name, temp_c, util_pct, ",
    "mem_used_mib, mem_total_mib, ecc_uncorrected); ",
    "_int maps empty, [N/A] and [Not Supported] to None; ",
    "a line without exactly 7 columns raises ",
    "ValueError unexpected nvidia-smi columns"
]

print("Joined text matches exact label?")
expected_p = "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns"
joined_p = "".join(p_lines).strip()
print(f"Match: {joined_p == expected_p}")
assert joined_p == expected_p

r_lines = [
    "problems for: expected 8 GPUs but found a different count; ",
    "temp above 85; uncorrected ECC non-zero; ",
    "plus XID in a set of known codes"
]
expected_r = "problems for: expected 8 GPUs but found a different count; temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes"
joined_r = "".join(r_lines).strip()
print(f"Match: {joined_r == expected_r}")
assert joined_r == expected_r

print("Both exact matches confirmed!")
