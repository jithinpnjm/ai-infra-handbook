#!/usr/bin/env python3

# Let's test full height budget:
H = 1200
y = 0

# 1. Top margin to title:
# Title at y = 52. Font-size 48.
# Title baseline: y = 52.
# Table top: y = 88.
y_table_top = 88

# Table columns:
# Total table width = 1520.
# Col 1 (Tool): width = 360
# Col 2 (Language): width = 420
# Col 3 (Notes): width = 740
# 360 + 420 + 740 = 1520!

# Table header height: 42 px (y = 88 to 130)

# Table rows:
# Row 1: Ansible, Salt, Cookiecutter, dbt | Jinja2 | {{ }}, {% %}, filters
# Col 1: 2 lines ("Ansible, Salt,", "Cookiecutter, dbt")
# Col 2: 1 line ("Jinja2")
# Col 3: 1 line ("{{ }}, {% %}, filters")
# Row 1 height: 58 px (y = 130 to 188)

# Row 2: Helm | Go text/template plus Sprig functions | {{ .Values... }}
# Col 1: 1 line ("Helm")
# Col 2: 2 lines ("Go text/template", "plus Sprig functions")
# Col 3: 4 lines:
#   Line 1: {{ .Values.image.tag | quote }},
#   Line 2: {{- if .Values.gpu }},
#   Line 3: {{ include "chart.fullname" . }},
#   Line 4: toYaml | nindent 4; trim with {{- and -}}
# Row 2 height: 116 px (y = 188 to 304)

# Row 3: Terraform or OpenTofu | HCL expressions and templatefile() | "${var.name}"...
# Col 1: 1 line ("Terraform or OpenTofu")
# Col 2: 2 lines ("HCL expressions and", "templatefile()")
# Col 3: 2 lines ('"${var.name}", for expressions,', '%{ if } directives')
# Row 3 height: 60 px (y = 304 to 364)

# Row 4: Kustomize | no templating | overlays and patches (JSON6902, strategic merge)
# Col 1: 1 line ("Kustomize")
# Col 2: 1 line ("no templating")
# Col 3: 2 lines ("overlays and patches", "(JSON6902, strategic merge)")
# Row 4 height: 60 px (y = 364 to 424)

# Row 5: GitHub Actions | ${{ expression }} | different syntax and contexts
# Col 1: 1 line ("GitHub Actions")
# Col 2: 1 line ("${{ expression }}")
# Col 3: 1 line ("different syntax and contexts")
# Row 5 height: 50 px (y = 424 to 474)

# Row 6: Docker Compose | ${VAR:-default} | shell-like
# Col 1: 1 line ("Docker Compose")
# Col 2: 1 line ("${VAR:-default}")
# Col 3: 1 line ("shell-like")
# Row 6 height: 50 px (y = 474 to 524)

# Row 7: cloud-init | Jinja2 optional header ## template: jinja | {{ v1.local_hostname }}
# Col 1: 1 line ("cloud-init")
# Col 2: 2 lines ("Jinja2 optional header", "## template: jinja")
# Col 3: 1 line ("{{ v1.local_hostname }}")
# Row 7 height: 60 px (y = 524 to 584)

# Row 8: Packer | HCL2 | templatefile, locals
# Col 1: 1 line ("Packer")
# Col 2: 1 line ("HCL2")
# Col 3: 1 line ("templatefile, locals")
# Row 8 height: 50 px (y = 584 to 634)

# Row 9: Prometheus and Alertmanager (orange) | Go templates | {{ $labels.instance }}...
# Col 1: 2 lines ("Prometheus and", "Alertmanager")
# Col 2: 1 line ("Go templates")
# Col 3: 3 lines:
#   Line 1: {{ $labels.instance }};
#   Line 2: conflicts with Jinja in Ansible-templated
#   Line 3: rule files: use raw
# Row 9 height: 90 px (y = 634 to 724)

# Total table ends at y = 724.
print(f"Table ends at y = {724}")
# Gap after table: 30 px -> y = 754.

# Habits strip:
# If y = 754, height = 210 -> ends at y = 964.
# Gap: 24 px -> y = 988.
# Reviewer test:
# y = 988, height = 80 -> ends at y = 1068.
# Gap: 24 px -> y = 1092.
# Bottom bar:
# y = 1092, height = 60 -> ends at y = 1152.
# Bottom margin: 1200 - 1152 = 48 px!

print("Total layout fits perfectly inside 1200 px!")
