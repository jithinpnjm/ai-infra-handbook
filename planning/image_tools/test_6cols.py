# Canvas width = 1600.
# Let margins be left=30, right=30. Usable width = 1540px.
# We have 6 segments.
# Can we choose widths w1, w2, w3, w4, w5, w6 such that sum(wi) + 5*gap <= 1540?

# Let's see what each segment needs if wrapped onto multiple lines.
# Rule: sans factor = 0.6 * 24 = 14.4 px/char.
# Rule: padding >= 16px each side, so min box width = max_line_len * 14.4 + 32.

# Segment 1: "Created to Scheduled" (20 chars * 18 = 360? Wait, title fs >= 30, so 0.6 * 30 = 18 px/char)
# If title "Created to Scheduled" is wrapped:
# "Created to" (10 chars * 18 = 180px)
# "Scheduled" (9 chars * 18 = 162px)
# Source: "creationTimestamp versus PodScheduled lastTransitionTime, scheduler metrics"
# If wrapped:
# Line 1: "creationTimestamp" (17 chars * 14.4 = 244.8px) -> min box width = 245 + 32 = 277px!
# Line 2: "versus"
# Line 3: "PodScheduled" (12 chars * 14.4 = 172.8px)
# Line 4: "lastTransitionTime," (19 chars * 14.4 = 273.6px) -> min box width = 274 + 32 = 306px!
# Line 5: "scheduler metrics" (17 chars * 14.4 = 244.8px)
# So Segment 1 needs at least 306px!

# What about Segment 3: "Sandbox"
# Source: "kubelet_run_podsandbox_duration_seconds" (39 chars)
# If unbroken: 39 * 14.4 = 561.6px -> needs 594px!
# If broken into 3 lines without space in text:
# "kubelet_run_" (12 chars * 14.4 = 172.8px)
# "podsandbox_" (11 chars * 14.4 = 158.4px)
# "duration_seconds" (16 chars * 14.4 = 230.4px) -> min box width = 230.4 + 32 = 263px!

# What about Segment 4: "Pull"
# Source: "event Pulled in X, kubelet_image_pull_duration_seconds, containerd logs"
# If broken:
# "event Pulled in X," (18 chars * 14.4 = 259.2px) -> needs 292px!
# "kubelet_image_" (14 chars * 14.4 = 201.6px)
# "pull_duration_" (14 chars * 14.4 = 201.6px)
# "seconds, containerd" (19 chars * 14.4 = 273.6px) -> needs 306px!
# "logs"

print("If Segment 1 = 310px, Segment 4 = 310px, that's already 620px.")
print("Remaining width for 4 segments = 1540 - 620 - 50 = 870px -> 870 / 4 = 217px.")
print("In 217px, max line length = (217 - 32) / 14.4 = 12.8 chars.")
print("In Segment 2: 'init containers,' is 16 chars -> 16 * 14.4 = 230.4px.")
print("In Segment 5: 'ContainersReady' is 15 chars -> 15 * 14.4 = 216px.")
print("In Segment 6: 'readiness probe' is 15 chars -> 216px.")
print("So 6 columns CANNOT satisfy the 16px padding rule!")
