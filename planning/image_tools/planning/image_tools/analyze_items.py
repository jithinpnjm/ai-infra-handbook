import re

# Let's analyze text lengths and wrapping for all items:
items = {
    "cli": "cli.py: Click group, output formatting and exit codes",
    "collect": "collect.py: per-host executor over SSH, an agent or Redfish, with timeout and bounded concurrency",
    "parsers": "parsers.py: pure functions turning nvidia-smi CSV and dcgmi output into frozen dataclasses (a pure function answers from its inputs alone: no network, no clock, no randomness)",
    "rules": "rules.py: evaluate(gpus, expected=8, max_temp=85)",
    "models": "models.py: dataclasses or pydantic models",
    "p_detail": "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns",
    "r_detail": "problems for: expected 8 GPUs but found a different count; temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes",
    "exit_0": "0 all GPUs healthy",
    "exit_1": "1 usage or runtime failure",
    "exit_3": "3 any GPU unhealthy",
    "exit_4": "4 partial collection failure",
    "test_strip": "canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, empty output, missing GPU; then CliRunner with a stubbed executor asserting exit codes and JSON shape",
    "bottom_bar": "Parser, rules, executor and CLI stay separate"
}

for k, v in items.items():
    print(f"{k:12s} ({len(v):3d} chars): {v}")
