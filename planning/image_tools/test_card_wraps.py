# Let's test the text wrapping and dimensions for both layouts

# In Layout A (side-by-side columns of width 740):
# Column width = 740
# Container padding = 20 on each side -> inner width = 700
# Inside each step card:
# Card width = 700
# Card has:
# Circle (cx=44, r=24) -> takes up x=0..68 + gap=16 -> 84px
# Icon (56px) -> takes up x=84..140 + gap=16 -> 156px
# Text area width = 700 - 156 - 20 (right pad) = 524 px!

# Let's test text wrapping in 524px:
# At font-size 24:
# sans char width = 24 * 0.6 = 14.4 px -> 524 / 14.4 = 36.3 chars per line.
# mono char width = 24 * 0.62 = 14.88 px -> 524 / 14.88 = 35.2 chars per line.

# Step 2 of Ladder 1:
# './ansible.cfg in the current directory (honoured only if it is not world-writable: a folder any user can change cannot be trusted)'
text_l1_2 = "./ansible.cfg in the current directory (honoured only if it is not world-writable: a folder any user can change cannot be trusted)"
print("Step 2 length:", len(text_l1_2))
