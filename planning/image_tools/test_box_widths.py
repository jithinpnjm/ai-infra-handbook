#!/usr/bin/env python3

# Let's see what is the MINIMUM box width for each box:

# Box 1:
# 'Root directory /': 16 chars * 24 * 0.6 = 230.4 px -> min box = 230.4 + 32 = 262.4 px.
# Wait! Can 'Root directory /' be wrapped onto 2 lines?
# Line 1: 'Root directory ' (15 chars * 24 * 0.6 = 216 px)
# Line 2: '/' (1 char * 24 * 0.62 = 14.88 px)
# OR:
# Line 1: 'Root ' (5 chars)
# Line 2: 'directory /' (11 chars * 24 * 0.6 = 158.4 px)
# If wrapped to 'Root directory ' and '/', max line = 216 px -> min box = 216 + 32 = 248 px!
# But at 265 px, 'Root directory /' fits on 1 line if box is 265 px (265 - 230.4 = 34.6 px pad = 17.3 px each side >= 16 px!).

# Box 2:
# 'Directory /home (inode A)':
# If wrapped:
# Line 1: 'Directory /home ' (16 chars sans = 230.4 px)
# Line 2: '(inode A)' (9 chars sans = 129.6 px)
# And row: 'alice -> inode B' (16 chars mono = 238.08 px)
# For 'alice -> inode B' to have 16 px padding on each side:
# Min box width = 238.08 + 32 = 270.08 px!
# So Box 2 needs to be at least 271 px.

# Box 3:
# 'Directory /home/alice (inode B)':
# Line 1: 'Directory ' (10 chars = 144 px)
# Line 2: '/home/alice ' (12 chars mono = 178.6 px)
# Line 3: '(inode B)' (9 chars = 129.6 px)
# Row: 'train.py -> inode C' (19 chars mono = 282.72 px)
# For 'train.py -> inode C' to have 16 px padding on each side:
# Min box width = 282.72 + 32 = 314.72 px!
# So Box 3 needs to be at least 315 px.

# Box 4 (Inode C):
# 'Inode C: type, permissions, owner, size, times, link count, pointers to data blocks'
# Can be wrapped into 4 or 5 lines:
# Line 1: 'Inode C: type, ' (15 chars sans = 216 px)
# Line 2: 'permissions, owner, ' (20 chars sans = 288 px)
# Line 3: 'size, times, link count, ' (25 chars sans = 360 px -> too wide for 300 px)
# What if:
# Line 1: 'Inode C: ' (9 chars = 129.6 px)
# Line 2: 'type, permissions, ' (19 chars = 273.6 px)
# Line 3: 'owner, size, times, ' (20 chars = 288 px)
# Line 4: 'link count, ' (12 chars = 172.8 px)
# Line 5: 'pointers to data blocks' (23 chars = 331.2 px -> too wide for 300 px)
# Let's find optimal wrap for Box 4:
