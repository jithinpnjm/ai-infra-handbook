# If ALLOCATED is at (1240, 480) and DOWN is at (1240, 920):
# ALLOCATED bottom is at y = 522.
# DOWN top is at y = 878.
# Vertical arrow: from (1240, 522) to (1240, 878).
#
# If Track 1 (IDLE -> DOWN) comes from IDLE (360, 480):
# Exits IDLE bottom at (360, 522) -> goes down to y=720 -> turns right to x=1110 -> enters DOWN left edge at (1110, 720)?
# Wait, DOWN is at y in [878, 962]!
# If Track 1 goes to y=720, then to reach DOWN (y=920), it would have to turn down at x=1110 to y=920!
# But ALLOCATED is at x in [1110, 1370]!
# So x=1110 is the left edge of ALLOCATED!
# If Track 1 went along x=1110, it would be touching ALLOCATED!
# And it would cross the interior of the right column!

print("Checked.")
