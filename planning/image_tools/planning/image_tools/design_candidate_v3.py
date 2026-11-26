import sys

# Let's define the exact layout and check all paddings with a script before writing SVG.

boxes = {}

# 1. Title
# <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
# <tspan x="800" dy="0">The GPU diagnostics CLI in four layers, </tspan>
# <tspan x="800" dy="52">with exit codes</tspan>

# --- LEFT COLUMN (x=40, w=1000) ---
# Total height from 140 to 880 = 740px.

# Box 1: cli.py
# by = 140, bh = 92
# icon: (56, 158, 56, 56)
# lines at tx = 132:
# line 1: ty = 176, fs = 28. ascent = 22.4 -> top_pad = 176 - 22.4 - 140 = 13.6 -> ty=178 -> top_pad = 15.6
# line 2: ty = 212, fs = 28. descent = 7 -> bot_pad = (140+92) - (212+7) = 232 - 219 = 13 -> make bh = 96, by=140
# with bh=96: bot_pad = 236 - 219 = 17. top_pad = 15.6.
# Arrow 1: y from 236 to 276 (length 40px, marker-end)

# Box 2: collect.py
# by = 276, bh = 96
# icon: (56, 296, 56, 56)
# lines at tx = 132, fs = 26:
# line 1: ty = 314. ascent = 20.8 -> top_pad = 314 - 20.8 - 276 = 17.2
# line 2: ty = 348. descent = 6.5 -> bot_pad = (276+96) - (348+6.5) = 372 - 354.5 = 17.5
# Arrow 2: y from 372 to 412 (length 40px, marker-end)

# Pure Layers Container:
# by = 412, bh = 480 (from 412 to 892)
# Orange border: stroke="#db8129" stroke-width="3" fill="#ffffff"

# Inside Pure Layers:
# Box 3: parsers.py card
# bx = 56, by = 428, bw = 968, bh = 246 (from 428 to 674)
# icon: (72, 442, 56, 56)
# parsers.py text:
# tx = 144, fs = 24 (ascent = 19.2, descent = 6)
# line 1: ty = 458 -> top_pad = 458 - 19.2 - 428 = 10.8 -> ty = 464 -> top_pad = 16.8
# line 2: ty = 492
# line 3: ty = 520 -> bot_pad in parsers header area: gap before parser detail panel!
# Wait! What lines for parsers.py?
# Line 1: "parsers.py: pure functions turning nvidia-smi CSV and dcgmi " (58 chars * 0.6 * 24 = 835.2 px. tx=144 -> 144+835.2 = 979.2. Box ends at 56+968 = 1024. Right pad = 44.8)
# Line 2: "output into frozen dataclasses (a pure function answers from " (61 chars: 61*0.6*24 = 878.4 px. 144+878.4 = 1022.4 -> tight! Let's wrap into 3 shorter lines:)
# Line 1: "parsers.py: pure functions turning nvidia-smi CSV " (50 chars * 0.6 * 24 = 720 px)
# Line 2: "and dcgmi output into frozen dataclasses " (41 chars * 0.6 * 24 = 590.4 px)
# Line 3: "(a pure function answers from its inputs alone: " (48 chars * 0.6 * 24 = 691.2 px)
# Line 4: "no network, no clock, no randomness)" (36 chars * 0.6 * 24 = 518.4 px)
# Let's check 4 lines:
# ty = 460, 486, 512, 538.
# Then Parser detail panel:
# by = 552, bh = 110 (ends at 662. Box ends at 674 -> bot_pad = 12 -> make bh of parsers card = 254 (ends at 682, gap before panel = 14, bot_pad = 20)
# Inside Parser detail panel:
# bx = 72, by = 554, bw = 936, bh = 116 (ends at 670)
# tx = 92, fs = 24 mono (factor 0.62 * 24 = 14.88 px)
# line 1: ty = 578 (top_pad = 578 - 19.2 - 554 = 4.8 -> ty = 588 -> top_pad = 14.8)
# line 2: ty = 612
# line 3: ty = 636
# line 4: ty = 660 (wait, 4 lines: 580, 606, 632, 658 -> if bh=130: 554 to 684. Then parsers card bh = 270: 428 to 698.)

# Let's check Arrow 3: parsers.py -> rules.py
# gap: between parsers card and rules card!
# If parsers card ends at 686. Arrow 3: y from 686 to 726 (length 40px).
# Rules card: by = 726, bh = 154 (ends at 880). Pure layers container ends at 894!
print("Calculating exact coordinates...")
