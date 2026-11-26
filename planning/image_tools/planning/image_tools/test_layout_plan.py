# Test layout geometries for GPU CLI infographic

# Labels:
# 1. Title: The GPU diagnostics CLI in four layers, with exit codes
# 2. cli.py: Click group, output formatting and exit codes
# 3. collect.py: per-host executor over SSH, an agent or Redfish, with timeout and bounded concurrency
# 4. parsers.py: pure functions turning nvidia-smi CSV and dcgmi output into frozen dataclasses (a pure function answers from its inputs alone: no network, no clock, no randomness)
# 5. rules.py: evaluate(gpus, expected=8, max_temp=85)
# 6. models.py: dataclasses or pydantic models
# 7. Parser detail: Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns
# 8. Rules detail: problems for: expected 8 GPUs but found a different count; temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes
# 9. Exit code 0: 0 all GPUs healthy
# 10. Exit code 1: 1 usage or runtime failure
# 11. Exit code 3: 3 any GPU unhealthy
# 12. Exit code 4: 4 partial collection failure
# 13. Test strip: canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, empty output, missing GPU; then CliRunner with a stubbed executor asserting exit codes and JSON shape
# 14. Bottom bar: Parser, rules, executor and CLI stay separate

# Let's see: How are they grouped?
# "A layered pipeline. 'cli.py...' to 'collect.py...' to 'parsers.py...' to 'rules.py...' (orange for the pure layers). 'models.py: dataclasses or pydantic models' at the side."
# "Parser detail '...'"
# "Rules detail '...'"
# "Exit code table '0...', '1...', '3...', '4...'"
# "Test strip '...'"
# "Bottom bar: '...'"

print("Labels defined.")
