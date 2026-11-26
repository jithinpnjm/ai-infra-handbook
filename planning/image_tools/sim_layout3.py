import re

# Margins: left=40, right=40, top=40, bottom=40
# Canvas: 1600 x 1200

# 1. Title:
# "Which ansible.cfg wins: the search order and the precedence of settings"
# 2 lines:
# Line 1: "Which ansible.cfg wins: " (font 48 bold)
# Line 2: "the search order and the precedence of settings" (font 48 bold)
title_y1 = 52
title_y2 = 104
title_bottom = 112

gap_title_ladders = 40 # >= 40px
ladders_top = title_bottom + gap_title_ladders # 152

# 2. Ladders (side-by-side):
# Col 1: x=40, width=740
# Col 2: x=820, width=740
# Gap = 820 - 780 = 40px
ladders_height = 490
ladders_bottom = ladders_top + ladders_height # 152 + 490 = 642

gap_ladders_surprise = 40 # >= 40px
surprise_top = ladders_bottom + gap_ladders_surprise # 642 + 40 = 682

# 3. Surprise story (orange):
# 2 lines of text + icon + 16px padding
surprise_height = 80
surprise_bottom = surprise_top + surprise_height # 682 + 80 = 762

gap_surprise_commands = 40 # >= 40px
commands_top = surprise_bottom + gap_surprise_commands # 762 + 40 = 802

# 4. Commands strip:
# 3 lines of text + icon + 16px padding
commands_height = 104
commands_bottom = commands_top + commands_height # 802 + 104 = 906

gap_commands_rules = 40 # >= 40px
rules_top = commands_bottom + gap_commands_rules # 906 + 40 = 946

# 5. Rules strip:
# 3 lines of text + icon + 16px padding
rules_height = 104
rules_bottom = rules_top + rules_height # 946 + 104 = 1050

gap_rules_bottombar = 40 # >= 40px
bottombar_top = rules_bottom + gap_rules_bottombar # 1050 + 40 = 1090

# 6. Bottom bar:
# 1 line of text + padding
bottombar_height = 54
bottombar_bottom = bottombar_top + bottombar_height # 1090 + 54 = 1144

bottom_margin = 1200 - bottombar_bottom # 1200 - 1144 = 56px >= 40px!

print(f"Title: y={title_y1}..{title_bottom}")
print(f"Gap: {gap_title_ladders}px")
print(f"Ladders: y={ladders_top}..{ladders_bottom} (h={ladders_height})")
print(f"Gap: {gap_ladders_surprise}px")
print(f"Surprise: y={surprise_top}..{surprise_bottom} (h={surprise_height})")
print(f"Gap: {gap_surprise_commands}px")
print(f"Commands: y={commands_top}..{commands_bottom} (h={commands_height})")
print(f"Gap: {gap_commands_rules}px")
print(f"Rules: y={rules_top}..{rules_bottom} (h={rules_height})")
print(f"Gap: {gap_rules_bottombar}px")
print(f"Bottom bar: y={bottombar_top}..{bottombar_bottom} (h={bottombar_height})")
print(f"Bottom margin: {bottom_margin}px")
