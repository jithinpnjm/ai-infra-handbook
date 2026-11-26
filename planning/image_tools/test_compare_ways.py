# Let's inspect the layout of Way A vs Way B.

# In Way A:
# The number line has:
# - marker '0'
# - marker '1'
# - marker '2'
# - marker '126'
# - marker '127'
# - wide segment '128 + N' (in orange outline) split into 3 markers:
#     '130 Ctrl-C', '137 SIGKILL', '143 SIGTERM'
# - marker '255'

# And beneath the line:
# 6 boxes:
# Box 0: 'Success'
# Box 1: 'General error. For grep, diff and cmp: no match or files differ, not an error'
# Box 2: 'Misuse of a command, or a real error for grep and diff'
# Box 126: 'Found but not executable'
# Box 127: 'Command not found'
# Box 255: 'Status out of range, or ssh connection failure'

# But wait: in Way A, what is under the wide segment '128 + N'?
# On the number line, the wide segment '128 + N' is between 127 and 255.
# If the 6 boxes are directly under their markers, then under 128+N there is a big empty gap between Box 127 and Box 255!
# Or is there?
# What if in Way B:
# Under 128+N, there IS a box!
# The box under 128+N has an orange outline, and contains the three markers:
# '130 Ctrl-C'
# '137 SIGKILL'
# '143 SIGTERM'
# Then under EVERY marker on the line, there is a box!
# And the row beneath the line has 7 boxes, completely filling the space with no awkward hole!

# Wait! Can 7 boxes fit across 1520 px with at least 40 px gap?
# Let's check!
