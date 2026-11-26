#!/usr/bin/env python3
import sys

# Labels to include:
labels = [
    "Which engine is reading the braces in front of you",
    "Tool",
    "Language",
    "Notes",
    "Ansible, Salt, Cookiecutter, dbt",
    "Jinja2",
    "{{ }}, {% %}, filters",
    "Helm",
    "Go text/template plus Sprig functions",
    '{{ .Values.image.tag | quote }}, {{- if .Values.gpu }}, {{ include "chart.fullname" . }}, toYaml | nindent 4; trim with {{- and -}}',
    "Terraform or OpenTofu",
    "HCL expressions and templatefile()",
    '"${var.name}", for expressions, %{ if } directives',
    "Kustomize",
    "no templating",
    "overlays and patches (JSON6902, strategic merge)",
    "GitHub Actions",
    "${{ expression }}",
    "different syntax and contexts",
    "Docker Compose",
    "${VAR:-default}",
    "shell-like",
    "cloud-init",
    "Jinja2 optional header ## template: jinja",
    "{{ v1.local_hostname }}",
    "Packer",
    "HCL2",
    "templatefile, locals",
    "Prometheus and Alertmanager",
    "Go templates",
    "{{ $labels.instance }}; conflicts with Jinja in Ansible-templated rule files: use raw",
    "separate data from templates; keep templates light on logic; prefer declarative overlays such as Kustomize or typed config; avoid templating a templating language, such as Helm values rendered by Jinja then rendered again by Terraform; keep logic in code or modules, not 200-line Jinja files; validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server",
    "could a reviewer understand the change without running anything?",
    "The same double brace can mean three different things"
]

print("Total labels:", len(labels))
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. {l}")
