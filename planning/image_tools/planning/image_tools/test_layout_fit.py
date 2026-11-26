#!/usr/bin/env python3

# Let's test wrapping Tile 5, 6, 7 with max 30 chars per line, and vertical height

# Tile 5:
# Title: 2 lines at 30px (line-height ~34px)
# Body: 5 lines at 24px (line-height ~28px)
# Icon: where is icon?
# Prompt: "Every node gets one simple outline icon drawn in SVG shapes (about 56 px, green stroke 4), placed beside or above its title, never overlapping text."
# If icon is BESIDE the title:
# Wait! Can icon be beside the title?
# If icon is 56px wide, can "5 Centralized scheduling" fit beside a 56px icon?
# "5 Centralized scheduling" is 24 chars * 18 = 432px!
# 432 + 56 = 488px! It would NOT fit beside the title if the title line is 432px!
# BUT what if the title is wrapped to:
# "5 Centralized" (13 chars * 18 = 234px) -> 234 + 56 + 15 = 305px < 448px!
# "scheduling and" (14 chars)
# "accounting:" (11 chars)
# OR what if the icon is at the TOP (ABOVE the title)?
# Let's calculate total vertical height if icon is ABOVE the title:
# Icon height = 56px.
# Gap between icon and title = 12px.
# Title = 2 lines * 34px = 68px.
# Gap between title and body = 12px.
# Body = 5 lines * 28px = 140px.
# Total height = 16 (top pad) + 56 + 12 + 68 + 12 + 140 + 16 (bottom pad) = 320px!
# But our box height was 265px! 320px > 265px!

print("Testing different layouts...")
