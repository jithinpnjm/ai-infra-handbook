import re

# We will design a complete, robust layout for candidate_gpu_cli_v3.svg.
# Canvas: 1600 x 1200
# Background: #f5f8f5
# Text: #303a36
# Green: #207448
# Light green panel: #e8f1ea
# Orange: #db8129 (only for the pure layers container)
# White: #ffffff

# Grid & Columns:
# Left column: x=40, w=1000 (ends at 1040)
# Right column: x=1080, w=480 (ends at 1560)
# Horizontal gap: 1080 - 1040 = 40px (>= 40px)
# Outer margins: left 40px, right 40px

# Let's calculate vertical coordinates:
# Title:
# y=50: "The GPU diagnostics CLI in four layers, " (48px bold)
# y=102: "with exit codes" (48px bold)
# Bottom of title text ~ 102 + 0.25*48 = 114.
# Gap to first row: ~36px -> row 1 starts at y=150.

# Left Row 1: cli.py
# bx=40, bw=1000. Icon at (56, 162, 56, 56).
# Label: "cli.py: Click group, output formatting and exit codes"
# Can it be 1 line or 2 lines?
# If 1 line at 28px bold:
# mono "cli.py: " (8 * 0.62 * 28 = 138.88)
# sans "Click group, output formatting and exit codes" (45 * 0.6 * 28 = 756)
# total tw = 894.88.
# tx = 132 (gap from icon: 132 - (56+56) = 20px).
# tx + tw = 1026.88. Box ends at 1040. Right pad = 13.12 < 16.
# So if we make it 2 lines or make font-size 26:
# If font-size 26: 8 * 0.62 * 26 + 45 * 0.6 * 26 = 128.96 + 702 = 830.96.
# 1040 - (132 + 830.96) = 77.04 px right pad!
# Or if 2 lines at 28px:
# Line 1: "cli.py: Click group, "
# Line 2: "output formatting and exit codes"
# But 1 line at 26px bold is very clean, OR 2 lines at 28px. Wait, rule:
# "Node and step titles at least 30 px bold. Secondary text and monospace at least 24 px. NO text smaller than 24 px anywhere."
# If node title must be at least 30 px bold:
# Let's test 2 lines at 30 px bold!
# Line 1: "cli.py: Click group, " (21 chars * 0.62 * 30 = 390.6 px)
# Line 2: "output formatting and exit codes" (32 chars * 0.6 * 30 = 576 px)
# Both lines < 580 px! Fit inside 1000px box with > 300px padding!
# Let's check!

print("Testing layout solver...")
