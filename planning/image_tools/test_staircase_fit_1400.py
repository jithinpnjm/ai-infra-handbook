# Let's see if the staircase can end at x = 1400!
# If staircase spans x = 40 to 1400 (usable = 1360 px):
# We have 6 steps and 5 diamonds.
# What if:
# Step box width = 145 px?
# Wait! Let's check:
# Step 1: "Shadow traffic"
# If font-size = 30 bold:
# "traffic" is 7 chars * 0.6 * 30 = 126 px.
# At width 145 px, pad = (145 - 126)/2 = 9.5 px < 16 px.
# BUT what if font-size of "traffic" is 24 px?
# Wait! What does the rule say?
# "Node and step titles at least 30 px bold. Secondary text and monospace at least 24 px."
# Is "Shadow traffic" a node/step title?
# Yes, "each step a box labelled with its traffic share: Shadow traffic, 1 percent, 5 percent..."
# So the step title must be at least 30 px bold!

# Wait! Can "traffic share" be:
# What if the step box is 160 px wide?
# Can 6 step boxes of 160 px wide fit if they are arranged differently?
# Let's explore!
