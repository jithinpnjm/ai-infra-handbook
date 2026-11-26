# Let us check how shifting Y coordinates by ~12px affects everything:
step_y = [
    270, # 1: U -> A
    312, # 2: A -> S
    356, # 3: S -> A
    400, # 4: A -> K
    448, # 5: K -> K
    496, # 6: K -> D
    544, # 7: K -> V
    592, # 8: K -> R
    636, # 9: R -> C
    680, # 10: K -> R
    728, # 11: K -> R
    772, # 12: R -> X
    818, # 13: K -> A
    868, # 14: Note over K,X
    920, # 15: U -> A
    964, # 16: A -> K
    1008,# 17: K -> X
    1056,# 18: K -> R
    1104,# 19: K -> V
    1146 # 20: K -> A
]

print("Step 20 is at y =", step_y[-1])
print("Step 20 circle bottom is at y =", step_y[-1] + 24)
print("Margin to 1200 is:", 1200 - (step_y[-1] + 24))
