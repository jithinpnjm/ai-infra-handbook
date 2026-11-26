import re

# Left panel cards:
# y start: 225
# Left panel: x=40, y=140, w=740, h=690
# Usable inside: x=65, w=690

# Card 1: cpu.stat fields
# Icon at x=85, y=240 (44x44 or 48x48)
# Text below icon or beside?
# Line 1: usage_usec, user_usec, system_usec, (520.8 px)
# Line 2: nr_periods, nr_throttled, (372.0 px)
# Line 3: throttled_usec, nr_bursts, burst_usec (550.6 px)
# If centered or left-aligned at x=85:
# Card width 690. Left margin 65. Right edge = 755.
# If text x=85, max x = 85 + 550.6 = 635.6. 755 - 635.6 = 119.4 px padding!
# Height: y=230 to 365 (h=135)

# Card 2: compare nr_throttled with nr_periods and check throttled_usec
# Icon at x=85, y=390
# Line 1: compare nr_throttled with nr_periods (540 px)
# Line 2: and check throttled_usec (360 px)
# Height: y=380 to 495 (h=115)

# Card 3: cAdvisor metrics
# Icon at x=85, y=520
# Line 1: container_cpu_cfs_throttled_periods_total (610.1 px)
# Line 2: and container_cpu_cfs_periods_total (520.8 px)
# If text at x=80, 80 + 610.1 = 690.1. Card right edge = 755. 755 - 690.1 = 64.9 px padding!
# Height: y=510 to 650 (h=140)

# Card 4: cpu.pressure (PSI)
# Icon at x=85, y=675
# Text: cpu.pressure (PSI) (312.5 px at 28px)
# Beside icon: icon x=85, text x=160. 160 + 312.5 = 472.5. Card right edge = 755. Padding = 282.5 px!
# Height: y=665 to 790 (h=125)

print("Left panel fits comfortably in height 140 to 830 (h=690).")

# Right panel:
# x=820, y=140, w=740, h=690
# Right Panel Header: The oversubscription trap
# Top Host box: 64 CPUs
# Host box: x=845, y=225, w=690, h=220
# Inside Host Box:
# Container Box: cpu.max = 200000 100000 (2 CPUs)
# Container box: x=870, y=275, w=640, h=70
# Under Container box or beside: nproc = 64 (orange)
# Runtime reads nproc = 64 (orange): x=870, y=360, w=300, h=65
# (and starts a 64 thread pool visualization / threads)

# Arrow from Host / nproc box to Result Card!
# Result Card:
# x=845, y=475, w=690, h=135
# Line 1: the quota is burned early in each period, (590.4 px)
# Line 2: then every thread pauses even though (518.4 px)
# Line 3: other CPUs are idle (273.6 px)

# Fix Table:
# Under it a fix table:
# x=845, y=630, w=690, h=175
# 4 items in Fix Table:
# Let's see: 2 columns of 2 rows!
# Col 1: x=855, w=330.
# Col 2: x=1200, w=325.
# Wait, can "Python: os.cpu_count() reports the host, pass the limit in" fit in 325px?
# No, that was 58 chars!
# But if fix table has 4 rows across the full 670px:
# Row 1 (y=640): Go: automaxprocs (GOMAXPROCS) (431px)
# Row 2 (y=680): Java: -XX:ActiveProcessorCount (446px)
# Row 3 (y=720): OpenMP: OMP_NUM_THREADS (342px)
# Row 4 (y=760): Python: os.cpu_count() reports the host, pass the limit in (863px -> 2 lines in 670px!)
# Wait, if Row 4 is 2 lines, height needs ~40px per single-line row, ~65px for python row!
# 40 + 40 + 40 + 65 = 185px!
# Let's check vertical budget!
