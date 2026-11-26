# Test vertical spacing for 5 cards in Col 1
# Canvas H = 1200
# Top title at y=65, title height ~50px.
# Content starts at y=130.
# Content ends at y=1160 (bottom margin 40px).
# Total height available = 1160 - 130 = 1030px.

# In Column 1, we have 5 cards.
# Between 5 cards, there are 4 gaps.
# Each gap >= 40px.
# If gap = 40px, 4 * 40 = 160px.
# Remaining height for 5 cards = 1030 - 160 = 870px.
# Average card height = 870 / 5 = 174px.

# Let's check each card's content in Col 1:

# Card 1:
# Title: "What does the runtime think exists:"
# Commands:
# line 1: crictl pods, crictl ps -a, crictl inspectp,
# line 2: crictl inspect (pid, exit code, mounts,
# line 3: resources), crictl logs, crictl stats;
# line 4: ctr -n k8s.io tasks ls
# That is 1 title line + 4 command lines = 5 lines total.
# Or if title wraps: 2 title lines + 3 command lines = 5 lines total.
# Height of 5 lines:
# Title: 1 line of 30px (dy=0, height ~32px)
# Gap between title and commands: 10px
# Commands: 4 lines of 24px (line height 28px): 4 * 28 = 112px
# Padding top: 16px, padding bottom: 16px
# Total = 16 + 32 + 10 + 112 + 16 = 186px!
# Wait! 186px is 12px more than 174px!
# But what about the other cards in Col 1?
# Card 2:
# Title: "What do the kubelet and runtime say:" (1 line)
# Commands: "journalctl -u kubelet -u containerd --since -30 min" (1 line!)
# Total lines = 2 lines!
# Height = 16 + 32 + 10 + 28 + 16 = 102px!
# Card 3:
# Title: "Which namespaces does this process live in:" (1 or 2 lines)
# Commands: 2 lines
# Total lines = 3 or 4 lines.
# Height = ~135px.
# Card 4:
# Title: "What is the pod network doing:" (1 line)
# Commands: 2 lines
# Height = 16 + 32 + 10 + 56 + 16 = 130px.
# Card 5:
# Title: "What does the pod filesystem look like:" (1 line)
# Commands: 2 lines
# Height = 130px.

# Total height of the 5 cards:
# 186 + 102 + 135 + 130 + 130 = 683px!
# 683px is WAY LESS than 870px!
# 870 - 683 = 187px of EXTRA vertical room!
print("Total card height needed in Col 1:", 186 + 102 + 135 + 130 + 130, "px out of 870 px available!")
