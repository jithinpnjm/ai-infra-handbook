#!/usr/bin/env python3

# Let's verify line wraps for Habits text in Option A:
habits_text = "separate data from templates; keep templates light on logic; prefer declarative overlays such as Kustomize or typed config; avoid templating a templating language, such as Helm values rendered by Jinja then rendered again by Terraform; keep logic in code or modules, not 200-line Jinja files; validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"

# Option A: 5 lines inside ~1400px text area
# Let's break naturally at clause boundaries:
lines_habits = [
    "separate data from templates; keep templates light on logic; prefer declarative overlays such as Kustomize or typed config;",
    "avoid templating a templating language, such as Helm values rendered by Jinja then rendered again by Terraform;",
    "keep logic in code or modules, not 200-line Jinja files;",
    "validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"
]
# Wait, line 1 has length:
for i, l in enumerate(lines_habits, 1):
    print(f"Habits Line {i}: len={len(l)}, sans_w={len(l)*14.4:.1f}px")

print("Habits match?:", " ".join(lines_habits) == habits_text)
