import re

# Canvas: width = 1600. Margins: left = 40, right = 40. Available width = 1520.
# We have 7 columns:
# Col 0: Exit 0 ('Success')
# Col 1: Exit 1 ('General error. For grep, diff and cmp: no match or files differ, not an error')
# Col 2: Exit 2 ('Misuse of a command, or a real error for grep and diff')
# Col 3: Exit 126 ('Found but not executable')
# Col 4: Exit 127 ('Command not found')
# Col 5: Exit 128+N ('130 Ctrl-C', '137 SIGKILL', '143 SIGTERM')
# Col 6: Exit 255 ('Status out of range, or ssh connection failure')

# Gap rule from prompt:
# "Leave at least 40 px between boxes and 40 px outside margin."
# Wait! If 7 columns, there are 6 gaps of 40 px = 240 px.
# Total width of 7 boxes = 1520 - 240 = 1280 px.
# But can we arrange them in 2 rows, or must they be in 1 row?
# Prompt says: "Each marker has a short leader line down to its text box in a row beneath the line."
# "in a row beneath the line"

# Let's test if 1280 px can be partitioned among 7 columns:
# Let's see:
# Can Col 1 ("General error...") fit in, say, 260 px?
# Earlier we found:
# At w=260 (inner w = 228 px):
# Line 1: 'General error.' (14 chars = 201.6 px)
# Line 2: 'For grep, diff' (14 chars = 201.6 px)
# Line 3: 'and cmp: no' (11 chars = 158.4 px)
# Line 4: 'match or files' (14 chars = 201.6 px)
# Line 5: 'differ, not an' (14 chars = 201.6 px)
# Line 6: 'error' (5 chars = 72.0 px)
# That's 6 lines. With line-height 32 px: 6 * 32 = 192 px.

# Col 2 ("Misuse of a command..."):
# At w=210 (inner w = 178 px):
# Line 1: 'Misuse of a' (11 chars = 158.4 px)
# Line 2: 'command, or' (11 chars = 158.4 px)
# Line 3: 'a real error' (12 chars = 172.8 px)
# Line 4: 'for grep and' (12 chars = 172.8 px)
# Line 5: 'diff' (4 chars = 57.6 px)
# That's 5 lines.

# Col 3 ("Found but not executable"):
# 'executable' is 10 chars = 144 px. With 32 px padding, min width is 176 px.
# At w=180 (inner w = 148 px):
# Line 1: 'Found but' (9 chars = 129.6 px)
# Line 2: 'not' (3 chars)
# Line 3: 'executable' (10 chars = 144 px <= 148 px!)
# Wait, or:
# Line 1: 'Found but not' (13 chars = 187.2 px > 148 px)
# So at w=180 it wraps onto 3 lines.

# Col 4 ("Command not found"):
# At w=160 (inner w = 128 px):
# Line 1: 'Command' (7 chars = 100.8 px)
# Line 2: 'not found' (9 chars = 129.6 px > 128 px)
# So at w=165 (inner w = 133 px):
# Line 2: 'not found' (9 chars = 129.6 px <= 133 px!)

# Col 5 (128+N: 3 markers '130 Ctrl-C', '137 SIGKILL', '143 SIGTERM'):
# Each marker: '137 SIGKILL' is 11 chars = 158.4 px.
# Min width = 158.4 + 32 = 190.4 px -> say 200 px.

# Col 6 ("Status out of range, or ssh connection failure"):
# 'connection' is 10 chars = 144 px.
# At w=200 (inner w = 168 px):
# Line 1: 'Status out' (10 chars = 144 px)
# Line 2: 'of range,' (9 chars = 129.6 px)
# Line 3: 'or ssh' (6 chars = 86.4 px)
# Line 4: 'connection' (10 chars = 144 px)
# Line 5: 'failure' (7 chars = 100.8 px)

# Col 0 ('Success'):
# w = 140 px (inner w = 108 px):
# 'Success' is 7 chars = 100.8 px <= 108 px!

# Sum of widths:
# w0 = 140
# w1 = 260
# w2 = 210
# w3 = 180
# w4 = 165
# w5 = 200
# w6 = 200
# Sum = 140 + 260 + 210 + 180 + 165 + 200 + 200 = 1355 px!
# But available width for boxes is 1280 px! (1355 > 1280 by 75 px)
print("Let's see how to fit them!")
