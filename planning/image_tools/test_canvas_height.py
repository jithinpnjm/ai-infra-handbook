#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Let's design the layout and check every detail:
# Total width: 1600
# Height: 900 to 1200. Let's aim for ~1080 or 1100 or 1120.

# Let's plan vertical dimensions:
# Margin top: 40
# Title: baseline y = 58 (height ~48)
# Gap between Title and Story strip: 40px -> Story strip starts at y = 105
# Story strip height:
# Inside story strip: 2 lines of text (24px sans, line-height 32px), with padding 18px top/bottom
# Text height = 24 + 32 = 56px. Card height = 18 + 56 + 18 = 92px.
# Story strip: y = 105 to y = 197. (h = 92)
# Gap from Story strip to Pipeline Gates: 43px -> Gates start at y = 240.

# What is the height needed for the gates?
# Let's check Gate 1, Gate 2, Gate 3:
#
# Inside Gate 1 (w = 480):
# Gate Header:
# Icon at (x=65, y=265), size 56x56
# Title: "render offline with realistic data" (30px bold)
# Wrapped on 2 lines:
# "render offline with" (y = 295)
# "realistic data" (y = 332)
# Header bottom ~ y = 345.
#
# Sub-cards inside Gate 1 (card width = 440, x = 60):
# Card 1 (Item 1): "jinja2 Python API with a fixtures file"
# 2 lines:
# "jinja2 Python API with"
# "a fixtures file"
# height = 16 + 24 + 30 + 16 = 86px.
#
# Card 2 (Item 2): 'ansible localhost -m ansible.builtin.template -a "src=nccl.conf.j2 dest=/tmp/out" -e @vars.yml --diff'
# 5 lines monospace 24px (line height 30px):
# height = 16 + 24 + 4*30 + 16 = 176px.
#
# Card 3 (Item 3): "one-task playbook"
# 1 line sans 24px:
# height = 16 + 24 + 16 = 56px.
#
# Card 4 (Item 4): 'ansible -m debug -a "msg={{ ... }}"'
# 2 lines monospace 24px (line height 30px):
# height = 16 + 24 + 30 + 16 = 86px.
#
# Total heights of 4 cards in Gate 1:
# 86 + 16 (gap) + 176 + 16 (gap) + 56 + 16 (gap) + 86 = 452px.
# Plus header height (~105px) + top padding (20) + bottom padding (20) = ~597px.
#
# Now let's check Gate 2 (w = 480):
# Header:
# Icon at (x=585, y=265), size 56x56
# Title: "compare with the golden file" (30px bold)
# Wrapped on 2 lines:
# "compare with"
# "the golden file"
# Header bottom ~ y = 345.
#
# Body in Gate 2:
# 11 lines sans 24px (line height 32px):
# 11 lines * 32px = 352px text block!
# Card height = 24 + 352 + 24 = 400px (or single large card ~452px to match Gate 1!).
#
# Now let's check Gate 3 (w = 480):
# Header:
# Icon at (x=1105, y=265), size 56x56
# Title: "validate with the target's own parser" (30px bold)
# Wrapped on 2 lines:
# "validate with the"
# "target's own parser"
# Header bottom ~ y = 345.
#
# Body in Gate 3:
# 7 lines mono 24px (line height 34px):
# 7 lines * 34px = 238px text block.
# Card height = 24 + 238 + 24 = 286px (or padded out to match Gate 1!).
#
# If all 3 gates have the SAME height, say h = 670px:
# Gates y: 240 to 910. (h = 670)
#
# Gap after Gates: 45px -> Bottom bar starts at y = 955.
# Bottom bar height: 75px -> y: 955 to 1030.
# Margin bottom: 1080 - 1030 = 50px >= 40px!
# Total SVG height: 1080!
print("Layout plan fits nicely in 1600 x 1080!")
