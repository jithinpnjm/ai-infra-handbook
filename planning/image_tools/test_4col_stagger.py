# Test the 4-column architecture geometry and clearances
import sys

# Canvas: 1600 x 1100 (or 1150)
WIDTH = 1600
HEIGHT = 1100

# Columns:
# Col 1: Hardware / BMC (Provisioned, Quarantined)
# Col 2: OS / Config (Configured)
# Col 3: Validation / Maintenance (Validating, Maintenance)
# Col 4: Cluster Operations (Ready, Cordoned, Draining, Decommissioned)

# Let's check X positions of columns:
# Col 1: X = 200  (width 240 -> [80, 320])
# Col 2: X = 560  (width 240 -> [440, 680])
# Col 3: X = 920  (width 240 -> [800, 1040])
# Col 4: X = 1320 (width 260 -> [1190, 1450])

# Horizontal gaps between columns:
# Col 1 to Col 2: 440 - 320 = 120 px.
# Col 2 to Col 3: 800 - 680 = 120 px.
# Col 3 to Col 4: 1190 - 1040 = 150 px.

# Now: where do the transition labels on Row 1 go?
# Row 1 transitions:
# 1. Provisioned -> Configured: "OS, kernel, drivers, runtime, kubelet (Ansible/image)"
# 2. Configured -> Validating: "join cluster tainted \"validating\""
# 3. Validating -> Ready: "health gates pass (GPU diag, NCCL, network, storage)"

# If the gap is 120 px, a 300 px badge horizontally between them would overlap!
# BUT what if Row 1 nodes are staggered, or what if the badge is placed ABOVE or BELOW Row 1?
# Let's check:
# Top margin: Title is at y = 60.
# If Row 1 nodes are at y = 300..400:
# The space ABOVE Row 1 (y = 110..260) is COMPLETELY EMPTY!
# 150 px of vertical height across the entire width of the canvas!
print("Space above Row 1 has 150px vertical clearance!")
