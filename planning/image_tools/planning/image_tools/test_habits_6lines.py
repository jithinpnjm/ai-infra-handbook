#!/usr/bin/env python3

habits_text = "separate data from templates; keep templates light on logic; prefer declarative overlays such as Kustomize or typed config; avoid templating a templating language, such as Helm values rendered by Jinja then rendered again by Terraform; keep logic in code or modules, not 200-line Jinja files; validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"

lines_habits = [
    "separate data from templates; keep templates light on logic;",
    "prefer declarative overlays such as Kustomize or typed config;",
    "avoid templating a templating language, such as Helm values",
    "rendered by Jinja then rendered again by Terraform;",
    "keep logic in code or modules, not 200-line Jinja files;",
    "validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"
]

print("Option with 6 lines:")
for i, l in enumerate(lines_habits, 1):
    w = len(l) * 14.4
    print(f"  Line {i}: len={len(l)}, sans_w={w:.1f}px")

print("Reconstructed match?:", " ".join(lines_habits) == habits_text)
