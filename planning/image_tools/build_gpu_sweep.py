import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

# Let's verify the text elements and exact strings:
title = "How many GPU nodes? Sweep the reservations and reuse a node when one ends"
node1_label = "Node 1"
node2_label = "Node 2"

bar_a = "(0, 4)"
bar_b = "(2, 6)"
bar_c = "(8, 10)"

overlap_label = "A and B overlap, they need separate nodes"

step_1 = "1 Sort by start: (0, 4), (2, 6), (8, 10)"
step_2 = "2 (0, 4): no node in use, open node, heap of end times = 4"
step_3 = "3 (2, 6): earliest end 4 is after start 2, open a second node, heap = 4, 6"
step_4 = "4 (8, 10): earliest end 4 is at or before start 8, reuse that node, heap = 6, 10"
step_5 = "5 Answer: the heap holds 2 end times, so 2 nodes"

side_note = "Half-open [start, end): a job ending at 10 frees its node for one starting at 10"
alt_method = "Event sweep: +1 at each start, -1 at each end, at equal times the end sorts before the start, the maximum running total is the answer"
takeaway = "First ask whether reservations are per node or pooled, because that changes the whole model."

ticks = [str(i) for i in range(11)]

print("All elements defined.")
