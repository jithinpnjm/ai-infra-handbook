t = "Message from systemctl or the journal"
print("Length:", len(t))
print("At 30px sans (0.6):", len(t) * 30 * 0.6)
# If wrapped onto 2 lines:
# Line 1: "Message from systemctl" (22 chars * 18 = 396px)
# Line 2: "or the journal" (14 chars * 18 = 252px)
