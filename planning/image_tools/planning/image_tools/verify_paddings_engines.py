#!/usr/bin/env python3

# Let's inspect clearances:
# Col 1: rect x = 40, width = 360 -> x_min = 40, x_max = 400.
# Center x = 220.
# For each line in Col 1, max width must be <= 360 - 32 = 328 px.
# At font-size 24 sans: 328 / 14.4 = 22.7 chars.
col1_lines = [
    "Tool", # 4 chars
    "Ansible, Salt,", # 14 chars -> 201.6 px
    "Cookiecutter, dbt", # 17 chars -> 244.8 px
    "Helm", # 4 chars
    "Terraform or OpenTofu", # 21 chars -> 302.4 px
    "Kustomize", # 9 chars
    "GitHub Actions", # 14 chars
    "Docker Compose", # 14 chars
    "cloud-init", # 10 chars
    "Packer", # 6 chars
    "Prometheus and", # 14 chars
    "Alertmanager" # 12 chars
]
print("Checking Col 1 lines:")
for l in col1_lines:
    w = len(l) * 24 * 0.6
    pad = (360 - w) / 2
    print(f"  '{l}': w={w:.1f}px, pad={pad:.1f}px (>=16: {pad >= 16})")
    assert pad >= 16

# Col 2: rect x = 400, width = 400 -> x_min = 400, x_max = 800.
# Center x = 600.
# Max width must be <= 400 - 32 = 368 px.
col2_lines = [
    "Language", # 8 chars
    "Jinja2", # 6 chars
    "Go text/template", # 16 chars -> 230.4 px
    "plus Sprig functions", # 20 chars -> 288 px
    "HCL expressions and", # 19 chars -> 273.6 px
    "templatefile()", # 14 chars -> mono 208.3 px
    "no templating", # 13 chars
    "${{ expression }}", # 17 chars -> mono 252.96 px
    "${VAR:-default}", # 15 chars -> mono 223.2 px
    "Jinja2 optional header", # 22 chars -> 316.8 px
    "## template: jinja", # 18 chars -> mono 267.8 px
    "HCL2", # 4 chars
    "Go templates" # 12 chars
]
print("\nChecking Col 2 lines:")
for l in col2_lines:
    is_mono = any(c in l for c in ["$", "{", "(", "#"])
    factor = 0.62 if is_mono else 0.6
    w = len(l) * 24 * factor
    pad = (400 - w) / 2
    print(f"  '{l}': w={w:.1f}px, pad={pad:.1f}px (>=16: {pad >= 16})")
    assert pad >= 16

# Col 3: rect x = 800, width = 760 -> x_min = 800, x_max = 1560.
# Center x = 1180.
# Max width must be <= 760 - 32 = 728 px.
col3_lines = [
    "Notes", # 5 chars
    "{{ }}, {% %}, filters", # 21 chars -> mono 312.5 px
    '{{ .Values.image.tag | quote }},', # 32 chars -> mono 476.2 px
    '{{- if .Values.gpu }},', # 22 chars -> mono 327.4 px
    '{{ include "chart.fullname" . }},', # 33 chars -> mono 491.0 px
    'toYaml | nindent 4; trim with {{- and -}}', # 41 chars -> mono 610.1 px
    '"${var.name}", for expressions,', # 31 chars -> mono 461.3 px
    '%{ if } directives', # 18 chars -> mono 267.8 px
    "overlays and patches", # 20 chars -> 288 px
    "(JSON6902, strategic merge)", # 27 chars -> 388.8 px
    "different syntax and contexts", # 29 chars -> 417.6 px
    "shell-like", # 10 chars
    "{{ v1.local_hostname }}", # 23 chars -> mono 342.2 px
    "templatefile, locals", # 20 chars -> mono 297.6 px
    "{{ $labels.instance }};", # 23 chars -> mono 342.2 px
    "conflicts with Jinja in Ansible-templated", # 41 chars -> 590.4 px
    "rule files: use raw" # 19 chars -> 273.6 px
]
print("\nChecking Col 3 lines:")
for l in col3_lines:
    is_mono = any(c in l for c in ["{", "$", "%", "|", '"'])
    factor = 0.62 if is_mono else 0.6
    w = len(l) * 24 * factor
    pad = (760 - w) / 2
    print(f"  '{l}': w={w:.1f}px, pad={pad:.1f}px (>=16: {pad >= 16})")
    assert pad >= 16

# Habits strip:
# rect x = 40, y = 774, width = 1520, height = 200.
# Icon at x = 68, y = 846, width = 56 -> right edge of icon = 124.
# Text starts at x = 146 -> clearance from icon = 146 - 124 = 22 px (>= 16).
habits_lines = [
    "separate data from templates; keep templates light on logic;",
    "prefer declarative overlays such as Kustomize or typed config;",
    "avoid templating a templating language, such as Helm values",
    "rendered by Jinja then rendered again by Terraform;",
    "keep logic in code or modules, not 200-line Jinja files;",
    "validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"
]
print("\nChecking Habits lines:")
for l in habits_lines:
    w = len(l) * 24 * 0.6
    right_edge = 146 + w
    pad_right = 1560 - right_edge
    print(f"  '{l[:30]}...': w={w:.1f}px, right_edge={right_edge:.1f}px, pad_right={pad_right:.1f}px (>=16: {pad_right >= 16})")
    assert pad_right >= 16

# Reviewer test:
# rect x = 40, y = 994, width = 1520, height = 76.
# Icon at x = 68, y = 1004, width = 56 -> right edge = 124.
# Text starts at x = 146 -> clearance from icon = 146 - 124 = 22 px (>= 16).
rev_text = "could a reviewer understand the change without running anything?"
w_rev = len(rev_text) * 26 * 0.6
right_rev = 146 + w_rev
pad_right_rev = 1560 - right_rev
print(f"\nReviewer test: w={w_rev:.1f}px, right_edge={right_rev:.1f}px, pad_right={pad_right_rev:.1f}px (>=16: {pad_right_rev >= 16})")
assert pad_right_rev >= 16

# Bottom bar:
# rect x = 40, y = 1090, width = 1520, height = 60.
# Center x = 800.
bot_text = "The same double brace can mean three different things"
w_bot = len(bot_text) * 26 * 0.6
pad_bot = (1520 - w_bot) / 2
print(f"Bottom bar: w={w_bot:.1f}px, pad={pad_bot:.1f}px (>=16: {pad_bot >= 16})")
assert pad_bot >= 16

print("\nALL HORIZONTAL PADDINGS >= 16px CONFIRMED!")
