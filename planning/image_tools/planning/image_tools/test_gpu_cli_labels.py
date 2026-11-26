import re

labels = [
    "The GPU diagnostics CLI in four layers, with exit codes",
    "cli.py: Click group, output formatting and exit codes",
    "collect.py: per-host executor over SSH, an agent or Redfish, with timeout and bounded concurrency",
    "parsers.py: pure functions turning nvidia-smi CSV and dcgmi output into frozen dataclasses (a pure function answers from its inputs alone: no network, no clock, no randomness)",
    "rules.py: evaluate(gpus, expected=8, max_temp=85)",
    "models.py: dataclasses or pydantic models",
    "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns",
    "problems for: expected 8 GPUs but found a different count; temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes",
    "0 all GPUs healthy",
    "1 usage or runtime failure",
    "3 any GPU unhealthy",
    "4 partial collection failure",
    "canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, empty output, missing GPU; then CliRunner with a stubbed executor asserting exit codes and JSON shape",
    "Parser, rules, executor and CLI stay separate"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. ({len(l)} chars): {l}")
