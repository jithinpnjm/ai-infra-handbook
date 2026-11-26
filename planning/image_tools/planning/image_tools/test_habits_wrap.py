#!/usr/bin/env python3

habits_text = "separate data from templates; keep templates light on logic; prefer declarative overlays such as Kustomize or typed config; avoid templating a templating language, such as Helm values rendered by Jinja then rendered again by Terraform; keep logic in code or modules, not 200-line Jinja files; validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"

# Let's test a wrap that fits in width ~1000 (if side-by-side) or ~1400 (if full width):
# Full width ~1400 px available for text (1400 / 14.4 ≈ 97 chars per line max):
lines_full = [
    "separate data from templates; keep templates light on logic; prefer declarative overlays",
    "such as Kustomize or typed config; avoid templating a templating language, such as Helm",
    "values rendered by Jinja then rendered again by Terraform; keep logic in code or modules,",
    "not 200-line Jinja files; validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"
]

print("Full width option (4 lines):")
for i, l in enumerate(lines_full, 1):
    w = len(l) * 14.4
    print(f"  Line {i}: len={len(l)}, w={w:.1f}px")

print("Reconstructed matches?:", " ".join(lines_full) == habits_text)
