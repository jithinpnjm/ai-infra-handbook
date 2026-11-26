#!/usr/bin/env python3

habits_text = "separate data from templates; keep templates light on logic; prefer declarative overlays such as Kustomize or typed config; avoid templating a templating language, such as Helm values rendered by Jinja then rendered again by Terraform; keep logic in code or modules, not 200-line Jinja files; validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"

# If Habits strip is width 1520 px (or e.g. 1420 px text area if with icon):
# Let's see natural breaks by semicolon:
clauses = [c.strip() for c in habits_text.split(";")]
print("Clauses count:", len(clauses))
for i, c in enumerate(clauses, 1):
    print(f"  {i}: {c} (len={len(c)})")
