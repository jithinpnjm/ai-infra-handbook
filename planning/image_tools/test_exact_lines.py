import re

# Left column candidate lines:
cli_lines = [
    "cli.py: Click group, output formatting and exit codes"
]
# If 1 line: len=53. mono_w = 53 * 14.88 = 788.6. sans_w = 53 * 14.4 = 763.2.

col_lines = [
    "collect.py: per-host executor over SSH, an agent or",
    "Redfish, with timeout and bounded concurrency"
]
# max len = 51. mono_w = 758.9. sans_w = 734.4.

pars_lines = [
    "parsers.py: pure functions turning nvidia-smi CSV and",
    "dcgmi output into frozen dataclasses (a pure function",
    "answers from its inputs alone: no network, no clock,",
    "no randomness)"
]
# max len = 53. mono_w = 788.6. sans_w = 763.2.

rules_lines = [
    "rules.py: evaluate(gpus, expected=8, max_temp=85)"
]
# len = 49. mono_w = 729.1. sans_w = 705.6.

print("Left column max widths (at 1 line for cli and rules):")
print(f"cli: {53*14.88:.1f} mono / {53*14.4:.1f} sans")
print(f"col: {51*14.88:.1f} mono / {51*14.4:.1f} sans")
print(f"pars: {53*14.88:.1f} mono / {53*14.4:.1f} sans")
print(f"rules: {49*14.88:.1f} mono / {49*14.4:.1f} sans")

# If Left Column width = 880 (x from 40 to 920):
# Usable width inside box (with icon?):
# WAIT! Where is the icon placed?
# "Every node gets one simple outline icon drawn in SVG shapes (about 56 px, green stroke 4), placed beside or above its title, never overlapping text."
# "placed beside or above its title, never overlapping text"
# If icon is placed ABOVE the title, or BESIDE the title!
