# Simulate Grid 7 and check all 12 transitions
# Row 0: Quar(0,0), Prov(0,1), Conf(0,2)
# Row 1: Drai(1,0), Main(1,1), Vali(1,2)
# Row 2: Cord(2,0), Read(2,1), Deco(2,2)

edges = [
    ("Start", "Prov"),
    ("Prov", "Conf"),
    ("Conf", "Vali"),
    ("Vali", "Read"),
    ("Read", "Cord"),
    ("Cord", "Drai"),
    ("Drai", "Main"),
    ("Main", "Vali"),
    ("Drai", "Quar"),
    ("Quar", "Prov"),
    ("Read", "Deco"),
    ("Deco", "End"),
]

# Let's check each edge:
# 1. Start -> Prov: enters (0,1) from top! (y=60 to y=top of Prov)
# 2. Prov(0,1) -> Conf(0,2): straight RIGHT along Row 0
# 3. Conf(0,2) -> Vali(1,2): straight DOWN along Col 2
# 4. Vali(1,2) -> Read(2,1):
#    From bottom of Vali(1,2), goes DOWN into the gap between Row 1 and Row 2,
#    then turns LEFT and enters top of Read(2,1)!
#    Wait! Does that cross anything?
#    What else is in the gap between Row 1 and Row 2, Col 1 and Col 2?
#    Nothing!
# 5. Read(2,1) -> Deco(2,2): straight RIGHT along Row 2!
# 6. Deco(2,2) -> End: straight RIGHT to End [*]!
# 7. Read(2,1) -> Cord(2,0): straight LEFT along Row 2!
# 8. Cord(2,0) -> Drai(1,0): straight UP along Col 0!
# 9. Drai(1,0) -> Main(1,1): straight RIGHT along Row 1!
# 10. Main(1,1) -> Vali(1,2): straight RIGHT along Row 1!
# 11. Drai(1,0) -> Quar(0,0): straight UP along Col 0!
# 12. Quar(0,0) -> Prov(0,1): straight RIGHT along Row 0!

print("Testing Grid 7...")
