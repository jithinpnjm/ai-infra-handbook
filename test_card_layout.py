# Middle Box x=340, width=920.
# Sub-row 2 (task flow): x=365, width=870.
# Inside task flow:
# Card A (import_role): x=385, width=830, y=470, height=135
# Card B (include_role): x=385, width=830, y=640, height=225

# Let's check Card A:
# Icon at x=405, y=485 (48x48)
# Title at x=475, y=515: ansible.builtin.import_role (mono 24 bold)
#   w = 27 * 0.62 * 24 = 401.8 px -> from 475 to 876.8 < 385+830=1215! (Padding right = 338.2 px)
# Subtitle at x=475, y=560: static, fixed at parse time (sans 24)
#   w = 27 * 0.6 * 24 = 388.8 px -> from 475 to 863.8 < 1215! (Padding right = 351.2 px)

# Downward arrow between Card A and Card B:
# Line from (x=800, y=605) to (x=800, y=640) - orthogonal vertical arrow with arrowhead!

# Let's check Card B:
# Orange border: stroke="#db8129" stroke-width="3.5" fill="#fffaf5"
# Icon (loop icon, orange) at x=405, y=660 (48x48)
# Title at x=475, y=685: ansible.builtin.include_role (mono 24 bold)
#   w = 28 * 0.62 * 24 = 416.6 px -> from 475 to 891.6 < 1215! (Padding right = 323.4 px)
# Row 2 at x=475, y=725: dynamic, decided at runtime (sans 24)
#   w = 27 * 0.6 * 24 = 388.8 px
# Row 3 at x=475, y=765: supports loop and tasks_from (sans 24)
#   w = 28 * 0.6 * 24 = 403.2 px
# Row 4 (note chip inside Card B):
#   Box at x=475, y=785, width=720, height=55, rx=8, fill="#fff2e5", stroke="#db8129", stroke-width="1.5"
#   Text inside at x=495, y=820: the one that can run a role after a reboot or a drain step
#   Wait, let's check width: 58 chars * 0.6 * 24 = 835.2 px.
#   Inside 720 px, 835.2 px is too wide!
#   If width=830, total available width is 830 - 30 = 800 px.
#   Still 835.2 > 800!
#   So wrapping is needed for this line!

print("Wrapping for Card B note:")
l1 = "the one that can run a role"
l2 = "after a reboot or a drain step"
print(f"Line 1: {l1} w={len(l1)*0.6*24:.1f} px")
print(f"Line 2: {l2} w={len(l2)*0.6*24:.1f} px")
