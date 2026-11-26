# If D2 and D3 are on the left, and D1 is on the right of Compute:
# Let's check:
# D2: x=100..250
# D3: x=280..430
# D1: x=480..780 (with STEPD and JOB below D1)
# CTLD: x=300..750, y=360..510
# DBD: x=850..1150, y=360..510
#
# CTLD connects to:
# - D2: from CTLD left-bottom (x=350) down to D2 (x=175)
# - D3: from CTLD center-bottom (x=450) down to D3 (x=355)
# - D1: from CTLD right-bottom (x=600) down to D1 (x=630)
# None of these 3 cross!
#
# CTLD connects to DBD:
# - from CTLD right (y=430) to DBD left (y=430).
#
# Now where is MUNGE?
# Between D1, DBD, and CTLD!
# Or MUNGE is at x=850..1300, y=720..880 (below DBD, to the right of D1).
# From MUNGE:
# - MUNGE -> DBD: straight UP to DBD! (no crossing)
# - MUNGE -> D1: straight LEFT to D1! (no crossing)
# - MUNGE -> CTLD: from MUNGE top-left, up to CTLD bottom-right (x=720, y=510)!
# Does MUNGE -> CTLD cross CTLD -> D1?
# CTLD -> D1 leaves CTLD at x=600, going down to D1 at x=630.
# MUNGE -> CTLD enters CTLD at x=720!
# x=720 is to the RIGHT of x=600!
# D1 is to the LEFT of MUNGE!
# So MUNGE -> CTLD stays entirely to the right of CTLD -> D1!
# THEY DO NOT CROSS!
print("NO CROSSING! Let's verify U1 -> D1!")
