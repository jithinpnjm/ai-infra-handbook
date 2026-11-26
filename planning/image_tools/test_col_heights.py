# Check if cards can have tailored heights or if equal height works

# If Col 1 has 5 cards and Col 2 has 4 cards:
# Let's see what happens if Col 1 has 5 cards and Col 2 has 4 cards:
# Can we have:
# Col 1:
# Card 1: What does the runtime think exists (H=190)
# Card 2: What do the kubelet and runtime say (H=150)
# Card 3: Which namespaces does this process live in (H=175)
# Card 4: What is the pod network doing (H=150)
# Card 5: What does the pod filesystem look like (H=150)
# Sum = 190 + 150 + 175 + 150 + 150 = 815px.
# 4 gaps * 45px = 180px.
# Total = 995px.
# y_start = 130 -> y_end = 1125 <= 1160.
# Perfectly fits!

print("Total Col 1 height:", 815 + 180)
