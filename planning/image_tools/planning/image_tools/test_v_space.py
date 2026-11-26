#!/usr/bin/env python3

# Let's inspect heights:
# Total canvas height H = 1200.
# Margins: Top = 40, Bottom = 40.
# Available height = 1200 - 80 = 1120.

# Title: y = 50, font-size = 48.
# Table starts at y = 90.
# Table header: y = 90 to 135 (height = 45).
# Rows:
# Row 1: Ansible (2 lines) -> h = 60
# Row 2: Helm (4 lines) -> h = 115
# Row 3: Terraform (2 lines) -> h = 60
# Row 4: Kustomize (2 lines) -> h = 60
# Row 5: GitHub Actions (1-2 lines) -> h = 55
# Row 6: Docker Compose (1 line) -> h = 50
# Row 7: cloud-init (2 lines) -> h = 60
# Row 8: Packer (1 line) -> h = 50
# Row 9: Prometheus (3 lines, orange!) -> h = 90

# Total table rows height = 45 + 60 + 115 + 60 + 60 + 55 + 50 + 60 + 50 + 90 = 645 px!
# Table ends at 90 + 645 = 735 px.
# Gap: 25 px -> y = 760.
# Next section:
# Habits strip + Reviewer test
# If Habits strip and Reviewer test are stacked or side-by-side:
# Let's see:
# y = 760 to 1100: 340 px available!
# Bottom bar: y = 1120 to 1165 (height = 45).
# Available between 760 and 1100 is 340 px!
print("Available space for Habits + Reviewer test: 340 px!")
