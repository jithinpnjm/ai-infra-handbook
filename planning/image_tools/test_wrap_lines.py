import re

def test_breaks():
    # Label 7: parser_detail
    pd = "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns"
    
    # Let's find natural line breaks for parser_detail:
    pd_lines = [
        "Gpu(index, name, temp_c, util_pct, mem_used_mib,",
        "mem_total_mib, ecc_uncorrected);",
        "_int maps empty, [N/A] and [Not Supported] to None;",
        "a line without exactly 7 columns raises",
        "ValueError unexpected nvidia-smi columns"
    ]
    # Check that joined text with spaces matches exactly:
    joined_pd = " ".join(pd_lines)
    assert joined_pd == pd, f"Mismatch:\n{joined_pd}\nvs\n{pd}"
    print("pd_lines matched exactly! Line lengths:")
    for l in pd_lines:
        print(f"  len={len(l):2d}: '{l}' (mono_w={len(l)*14.88:.1f}, sans_w={len(l)*14.4:.1f})")

    # Label 8: rules_detail
    rd = "problems for: expected 8 GPUs but found a different count; temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes"
    rd_lines = [
        "problems for: expected 8 GPUs but found a",
        "different count; temp above 85; uncorrected",
        "ECC non-zero; plus XID in a set of known codes"
    ]
    joined_rd = " ".join(rd_lines)
    assert joined_rd == rd, f"Mismatch:\n{joined_rd}\nvs\n{rd}"
    print("\nrd_lines matched exactly! Line lengths:")
    for l in rd_lines:
        print(f"  len={len(l):2d}: '{l}' (mono_w={len(l)*14.88:.1f}, sans_w={len(l)*14.4:.1f})")

    # Label 3: collect.py
    col = "collect.py: per-host executor over SSH, an agent or Redfish, with timeout and bounded concurrency"
    col_lines = [
        "collect.py: per-host executor over SSH, an agent",
        "or Redfish, with timeout and bounded concurrency"
    ]
    joined_col = " ".join(col_lines)
    assert joined_col == col, f"Mismatch:\n{joined_col}\nvs\n{col}"
    print("\ncol_lines matched exactly! Line lengths:")
    for l in col_lines:
        print(f"  len={len(l):2d}: '{l}' (sans_w={len(l)*14.4:.1f})")

    # Label 4: parsers.py
    pars = "parsers.py: pure functions turning nvidia-smi CSV and dcgmi output into frozen dataclasses (a pure function answers from its inputs alone: no network, no clock, no randomness)"
    pars_lines = [
        "parsers.py: pure functions turning nvidia-smi CSV and dcgmi output",
        "into frozen dataclasses (a pure function answers from its",
        "inputs alone: no network, no clock, no randomness)"
    ]
    joined_pars = " ".join(pars_lines)
    assert joined_pars == pars, f"Mismatch:\n{joined_pars}\nvs\n{pars}"
    print("\npars_lines matched exactly! Line lengths:")
    for l in pars_lines:
        print(f"  len={len(l):2d}: '{l}' (sans_w={len(l)*14.4:.1f})")

    # Label 13: test_strip
    ts = "canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, empty output, missing GPU; then CliRunner with a stubbed executor asserting exit codes and JSON shape"
    ts_lines = [
        "canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, empty output,",
        "missing GPU; then CliRunner with a stubbed executor asserting exit codes and JSON shape"
    ]
    joined_ts = " ".join(ts_lines)
    assert joined_ts == ts, f"Mismatch:\n{joined_ts}\nvs\n{ts}"
    print("\nts_lines matched exactly! Line lengths:")
    for l in ts_lines:
        print(f"  len={len(l):2d}: '{l}' (sans_w={len(l)*14.4:.1f})")

test_breaks()
