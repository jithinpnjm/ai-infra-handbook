# Let's explore how 6 stage boxes can fit horizontally across 1600 px.

# If canvas width = 1600.
# What if:
# Let's check font sizes:
# Rule:
# "Title 48 px bold. Node and step titles at least 30 px bold. Secondary text and monospace at least 24 px. NO text smaller than 24 px anywhere."
# "Never shrink text to make it fit. Make the box bigger, wrap the text onto more lines (separate <tspan x= dy=> lines), or use fewer items per row."
# "Estimate widths conservatively: sans 0.6 x font-size per character, monospace 0.62 x font-size per character. Every text line must fit inside its box with at least 16 px padding. Never let text touch or cross a box edge, an icon or an arrow."

# Let's examine if 6 stage boxes can fit with:
# Outside margins: 40px left, 40px right. (x goes from 40 to 1560 -> total width = 1520px).
# What if gap between boxes = 20px? 5 gaps * 20 = 100px.
# Total width for 6 boxes = 1420px.
# Box 1: 170px
# Box 2: 240px
# Box 3: 240px
# Box 4: 250px
# Box 5: 250px
# Box 6: 270px
# Sum = 170 + 240 + 240 + 250 + 250 + 270 = 1420px!
# Wait! In Box 6: 270px width.
# In Box 6, text is "_start, __libc_start_main, main".
# What if font size is 24px?
# "__libc_start_main," has 18 chars.
# If sans: 18 * 0.6 * 24 = 259.2 px.
# 270 - 259.2 = 10.8 px padding total -> 5.4 px each side. But padding must be >= 16px!
# To have 16px padding on each side, Box 6 width must be >= 259.2 + 32 = 291.2 px!

# What if Box 6 is 300px?
# Then total width of boxes = 170 + 230 + 230 + 250 + 240 + 300 = 1420px!
# Let's check Box 1: 170px. Max text: "and execve" (10 chars * 14.4 = 144px -> pad = (170-144)/2 = 13px! Needs 144+32 = 176px).
# Box 2: "picks a format" (14 chars * 14.4 = 201.6px -> needs 201.6 + 32 = 233.6px -> 234px).
# Box 3: "builds the stack" (16 chars * 14.4 = 230.4px -> needs 230.4 + 32 = 262.4px -> 263px).
# Box 4: "PT_INTERP: kernel" (17 chars * 14.4 = 244.8px -> needs 244.8 + 32 = 276.8px -> 277px).
# Box 5: "relocates, runs" (15 chars * 14.4 = 216px -> needs 216 + 32 = 248px).
# Box 6: "__libc_start_main," (18 chars * 14.4 = 259.2px -> needs 259.2 + 32 = 291.2px -> 292px).

# Total box widths = 176 + 234 + 263 + 277 + 248 + 292 = 1490 px!
# Available width = 1520 px.
# Remaining for 5 gaps = 1520 - 1490 = 30 px!
# 30 / 5 = 6 px per gap!
# But arrows need to fit between the boxes! An arrow with an 18px marker needs at least 20-30px!

print("Analysis of box widths:")
