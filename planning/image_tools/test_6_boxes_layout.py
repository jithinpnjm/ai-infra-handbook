# If the wide segment '128 + N' is on the line, and split into three small markers '130 Ctrl-C', '137 SIGKILL', '143 SIGTERM':
# Where does it sit on the number line?
# From say x=920 to x=1360 (width 440 px).
# In 440 px, the three markers:
# '130 Ctrl-C' (width ~144 px)
# '137 SIGKILL' (width ~158 px)
# '143 SIGTERM' (width ~158 px)
# fit side-by-side or stacked!
# Wait, side-by-side: 144 + 158 + 158 = 460 px -> slightly wider than 440, say x=880 to x=1380 (width 500 px)!
# Then '130 Ctrl-C', '137 SIGKILL', '143 SIGTERM' fit side-by-side inside the wide segment!
# But wait: what is beneath the number line between x=880 and x=1380?
# If there is no box beneath it, there is a giant 500 px empty space in the row beneath the line!
print("Empty space check...")
