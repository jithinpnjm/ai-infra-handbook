# Check BACKUP lines:
lines = [
    ("backup", 140, 515, 30, "mono"),
    ("slurmctld", 140, 545, 30, "mono"),
    ("(optional)", 140, 575, 24, "sans"),
    ("shared StateSaveLocation", 140, 610, 24, "mono") # or split
]
# If shared StateSaveLocation is split:
# "shared" -> len 6 * 14.88 = 89.3
# "StateSaveLocation" -> len 17 * 14.88 = 253
# Box width 300: 300 - 20 - 253 = 27px padding!
print("Fits with >25px padding!")
