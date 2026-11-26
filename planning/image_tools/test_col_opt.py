# Let's see: col width = 740.
# Card width = 700. Card x = 60 to 760.
# In Step 2:
# What if the card has:
# Circle 1 (cx=92, cy=card_top + 34, r=24)
# Icon 56px (x=128..184, y=card_top + 6)
# Title / Line 1 beside circle & icon:
# x=198: "./ansible.cfg in the current directory"
# Can "./ansible.cfg in the current directory" fit from x=198 to x=744 (546px)?
# Length of "./ansible.cfg in the current directory" = 38 chars.
# 38 * 24 * 0.6 = 547.2 px (with sans) or 38 * 24 * 0.62 = 565.4 (with mono).
# That is 565px > 546px.
# But what if:
# Line 1: "./ansible.cfg" (13 chars, mono: 13 * 24 * 0.62 = 193.4 px)
# Line 2: "in the current directory" (24 chars, sans: 24 * 24 * 0.6 = 345.6 px)
# Both fit beside the icon easily!
# And Line 3 & 4 (the parenthetical clause):
# "(honoured only if it is not world-writable:"
# "a folder any user can change cannot be trusted)"
# can span from x=80 across the full card width!
# From x=80 to x=744 is 664 px!
# Line 3: 44 chars * 24 * 0.6 = 633.6 px <= 664 px! (Fits with 30px padding!)
# Line 4: 47 chars * 24 * 0.6 = 676.8 px > 664 px!
# What if Line 4 is split?
# Line 3: "(honoured only if it is not world-writable: "
# Line 4: "a folder any user can change "
# Line 5: "cannot be trusted)"
# Let's check widths:
l3 = "(honoured only if it is not world-writable: " # len=44, w=633.6
l4 = "a folder any user can change " # len=29, w=417.6
l5 = "cannot be trusted)" # len=18, w=259.2
print(f"l3: {len(l3)*24*0.6:.1f} <= 664")
print(f"l4: {len(l4)*24*0.6:.1f} <= 664")
print(f"l5: {len(l5)*24*0.6:.1f} <= 664")
