# Let's check vertical budget:
# Total H = 1200
# Margin top: 40px
# Title: y = 56, height from y=30 to y=80 (~50px)
# y_start = 100
# y_end = 1160 (margin bottom 40px)
# Available height = 1160 - 100 = 1060px!

# What needs to go in this 1060px?
# 1. Row 1: Layer 1 (cli.py) + Exit code table
#    Wait! Exit code table has 4 items:
#    - 0 all GPUs healthy
#    - 1 usage or runtime failure
#    - 3 any GPU unhealthy
#    - 4 partial collection failure
#    If each item is 40px high, 4 items = 160px.
#    Wait, can Exit code table span Row 1 and Row 2?
#    Or how tall should Row 1 be?
