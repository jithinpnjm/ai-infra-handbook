#!/usr/bin/env python3

habits_text = "separate data from templates; keep templates light on logic; prefer declarative overlays such as Kustomize or typed config; avoid templating a templating language, such as Helm values rendered by Jinja then rendered again by Terraform; keep logic in code in modules, not 200-line Jinja files; validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"
# Note: exact text from prompt:
habits_text = "separate data from templates; keep templates light on logic; prefer declarative overlays such as Kustomize or typed config; avoid templating a templating language, such as Helm values rendered by Jinja then rendered again by Terraform; keep logic in code or modules, not 200-line Jinja files; validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server"

reviewer_text = "could a reviewer understand the change without running anything?"

bottom_bar_text = "The same double brace can mean three different things"

print("Habits length:", len(habits_text))
print("Reviewer length:", len(reviewer_text))
print("Bottom bar length:", len(bottom_bar_text))
