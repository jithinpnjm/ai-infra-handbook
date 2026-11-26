# Let's test the 4 vertical layers in Left Column (w = 1000 px, x = 40 to 1040)

# In width 1000 px:
# Icon at x = 56 (ends at 112). Text starts at x = 132.
# Usable width for text = 1040 - 132 - 20 = 888 px!
# At 24 px font: 888 / 14.4 = 61.6 chars per line!

cli_text = "cli.py: Click group, output formatting and exit codes" # 53 chars -> 1 line!
collect_text = "collect.py: per-host executor over SSH, an agent or Redfish, with timeout and bounded concurrency" # 97 chars -> 2 lines!
parsers_text = "parsers.py: pure functions turning nvidia-smi CSV and dcgmi output into frozen dataclasses (a pure function answers from its inputs alone: no network, no clock, no randomness)" # 175 chars -> 3 lines!
rules_text = "rules.py: evaluate(gpus, expected=8, max_temp=85)" # 49 chars -> 1 line!

p_detail = "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns" # 214 chars -> 4 lines!
r_detail = "problems for: expected 8 GPUs but found a different count; temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes" # 132 chars -> 2 lines!

print("Number of lines:")
print("cli:", 1)
print("collect:", 2)
print("parsers:", 3)
print("p_detail:", 4)
print("rules:", 1)
print("r_detail:", 2)
