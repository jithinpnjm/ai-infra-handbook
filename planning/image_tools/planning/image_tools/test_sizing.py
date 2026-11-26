# Test text layout and box sizing for parsers and rules details

def test_text_sizing():
    p_text = "parsers.py: pure functions turning nvidia-smi CSV and dcgmi output into frozen dataclasses (a pure function answers from its inputs alone: no network, no clock, no randomness)"
    p_detail = "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns"
    
    r_text = "rules.py: evaluate(gpus, expected=8, max_temp=85)"
    r_detail = "problems for: expected 8 GPUs but found a different count; temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes"

    print("=== Parsers text ===")
    print("p_text len:", len(p_text))
    print("p_detail len:", len(p_detail))
    print("=== Rules text ===")
    print("r_text len:", len(r_text))
    print("r_detail len:", len(r_detail))

test_text_sizing()
