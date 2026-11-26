# Let's test the layout where DOWN is below IDLE:
#
# Nodes:
# IDLE:      (x=400,  y=300)
# ALLOCATED: (x=1200, y=300)
# DOWN:      (x=400,  y=650)
# DRAINING:  (x=1200, y=650)
# DRAINED:   where does DRAINED go?
#
# Connections:
# 1. [*] -> IDLE
# 2. IDLE <-> ALLOCATED (2 arrows: job starts, job ends)
# 3. IDLE <-> DOWN:
#    - IDLE -> DOWN: "slurmd not responding (SlurmdTimeout) / admin"
#    - DOWN -> IDLE: "resume or ReturnToService on valid registration"
#    Notice: IDLE and DOWN are directly adjacent vertically!
#    The 2 arrows between them are direct vertical arrows!
# 4. ALLOCATED -> DOWN: "node failure (jobs requeued or failed)"
#    From ALLOCATED (1200, 300) down/left to DOWN (400, 650)!
# 5. ALLOCATED -> DRAINING: "scontrol drain / health check"
#    ALLOCATED and DRAINING are directly adjacent vertically!
# 6. DRAINING -> DRAINED: "running jobs finish"
# 7. IDLE -> DRAINED: "scontrol drain / health check"
# 8. DRAINED -> IDLE: "scontrol resume"
#
# Wait! Where can DRAINED be placed?
# DRAINED needs to connect to:
# - DRAINING (from DRAINING)
# - IDLE (from IDLE, to IDLE)
# If DRAINED is at (x=800, y=480) [between the four nodes!]
# Then:
# - DRAINING (1200, 650) -> DRAINED (800, 480): goes up-left.
# - IDLE (400, 300) <-> DRAINED (800, 480): goes down-right and up-left.
# BUT wait: ALLOCATED -> DOWN goes from (1200, 300) to (400, 650)!
# That would cross DRAINED in the center!
#
# So DRAINED cannot be in the center if ALLOCATED -> DOWN crosses the center.
# What if ALLOCATED -> DOWN goes around the outside?
# Or what if DRAINED is at the bottom (x=800, y=920)?
# Let's check:
# If DRAINED is at (800, 920):
# - DRAINING (1200, 650) -> DRAINED (800, 920): down-left.
# - IDLE (400, 300) <-> DRAINED (800, 920):
#   Wait, DOWN is at (400, 650)!
#   So IDLE to DRAINED would have to go past DOWN!
print("Checked.")
