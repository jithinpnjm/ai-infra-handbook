import re

labels_and_lines = {
    "title": (
        "The GPU diagnostics CLI in four layers, with exit codes",
        ["The GPU diagnostics CLI in four layers, with exit codes"]
    ),
    "cli": (
        "cli.py: Click group, output formatting and exit codes",
        [
            "cli.py: Click group, output formatting",
            "and exit codes"
        ]
    ),
    "collect": (
        "collect.py: per-host executor over SSH, an agent or Redfish, with timeout and bounded concurrency",
        [
            "collect.py: per-host executor over SSH,",
            "an agent or Redfish, with timeout",
            "and bounded concurrency"
        ]
    ),
    "parsers": (
        "parsers.py: pure functions turning nvidia-smi CSV and dcgmi output into frozen dataclasses (a pure function answers from its inputs alone: no network, no clock, no randomness)",
        [
            "parsers.py: pure functions turning nvidia-smi",
            "CSV and dcgmi output into frozen dataclasses",
            "(a pure function answers from its inputs alone:",
            "no network, no clock, no randomness)"
        ]
    ),
    "rules": (
        "rules.py: evaluate(gpus, expected=8, max_temp=85)",
        [
            "rules.py: evaluate(gpus, expected=8,",
            "max_temp=85)"
        ]
    ),
    "models": (
        "models.py: dataclasses or pydantic models",
        [
            "models.py: dataclasses or pydantic models"
        ]
    ),
    "parser_detail": (
        "Gpu(index, name, temp_c, util_pct, mem_used_mib, mem_total_mib, ecc_uncorrected); _int maps empty, [N/A] and [Not Supported] to None; a line without exactly 7 columns raises ValueError unexpected nvidia-smi columns",
        [
            "Gpu(index, name, temp_c, util_pct, mem_used_mib,",
            "mem_total_mib, ecc_uncorrected); _int maps empty,",
            "[N/A] and [Not Supported] to None; a line without",
            "exactly 7 columns raises ValueError unexpected",
            "nvidia-smi columns"
        ]
    ),
    "rules_detail": (
        "problems for: expected 8 GPUs but found a different count; temp above 85; uncorrected ECC non-zero; plus XID in a set of known codes",
        [
            "problems for: expected 8 GPUs but found a different",
            "count; temp above 85; uncorrected ECC non-zero; plus",
            "XID in a set of known codes"
        ]
    ),
    "ec0": (
        "0 all GPUs healthy",
        ["0 all GPUs healthy"]
    ),
    "ec1": (
        "1 usage or runtime failure",
        ["1 usage or runtime failure"]
    ),
    "ec3": (
        "3 any GPU unhealthy",
        ["3 any GPU unhealthy"]
    ),
    "ec4": (
        "4 partial collection failure",
        ["4 partial collection failure"]
    ),
    "test_strip": (
        "canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, empty output, missing GPU; then CliRunner with a stubbed executor asserting exit codes and JSON shape",
        [
            "canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, empty output,",
            "missing GPU; then CliRunner with a stubbed executor asserting exit codes and JSON shape"
        ]
    ),
    "bottom_bar": (
        "Parser, rules, executor and CLI stay separate",
        ["Parser, rules, executor and CLI stay separate"]
    )
}

print(f"Checking {len(labels_and_lines)} labels for exact text reconstruction:")
for k, (expected, lines) in labels_and_lines.items():
    reconstructed = " ".join(lines)
    reconstructed_collapsed = re.sub(r'\s+', ' ', reconstructed).strip()
    assert reconstructed_collapsed == expected, f"FAIL for {k}!\nGot: '{reconstructed_collapsed}'\nExp: '{expected}'"
    print(f"  [OK] {k:15s}: max line len={max(len(l) for l in lines):2d}")

