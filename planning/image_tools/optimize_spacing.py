# Let's write an optimizer to find the exact Y coordinates:

steps_data = [
    # 1: U -> A
    {"num": 1, "src": "U", "dst": "A", "type": "msg_r", "bh": 28},
    # 2: A -->> S
    {"num": 2, "src": "A", "dst": "S", "type": "dash_r", "bh": 28},
    # 3: S -> A (leftward)
    {"num": 3, "src": "S", "dst": "A", "type": "msg_l", "bh": 44},
    # 4: A -->> K
    {"num": 4, "src": "A", "dst": "K", "type": "dash_r", "bh": 28},
    # 5: K -> K (self-loop)
    {"num": 5, "src": "K", "dst": "K", "type": "self_r", "bh": 44},
    # 6: K -> D
    {"num": 6, "src": "K", "dst": "D", "type": "msg_r", "bh": 28},
    # 7: K -> V
    {"num": 7, "src": "K", "dst": "V", "type": "msg_r", "bh": 28},
    # 8: K -> R
    {"num": 8, "src": "K", "dst": "R", "type": "msg_r", "bh": 28},
    # 9: R -> C
    {"num": 9, "src": "R", "dst": "C", "type": "msg_r", "bh": 28},
    # 10: K -> R
    {"num": 10, "src": "K", "dst": "R", "type": "msg_r", "bh": 28},
    # 11: K -> R
    {"num": 11, "src": "K", "dst": "R", "type": "msg_r", "bh": 28},
    # 12: R -> X
    {"num": 12, "src": "R", "dst": "X", "type": "msg_r", "bh": 28},
    # 13: K -> A (leftward)
    {"num": 13, "src": "K", "dst": "A", "type": "msg_l", "bh": 64},
    # Note over K,X
    {"num": "note", "src": "K", "dst": "X", "type": "note", "bh": 34},
    # 14: U -> A
    {"num": 14, "src": "U", "dst": "A", "type": "msg_r", "bh": 28},
    # 15: A -->> K
    {"num": 15, "src": "A", "dst": "K", "type": "dash_r", "bh": 28},
    # 16: K -> X
    {"num": 16, "src": "K", "dst": "X", "type": "msg_r", "bh": 28},
    # 17: K -> R
    {"num": 17, "src": "K", "dst": "R", "type": "msg_r", "bh": 28},
    # 18: K -> V
    {"num": 18, "src": "K", "dst": "V", "type": "msg_r", "bh": 28},
    # 19: K -> A (leftward)
    {"num": 19, "src": "K", "dst": "A", "type": "msg_l", "bh": 28}
]

# Total steps = 20 (19 steps + 1 note)
# Row 2 headers: y = 140 to 216 (h = 76)
# Step 1: ay = 252 (card at 252 - 28 - 4 = 220, gap from row 2 is 4px)

# Let's test intervals:
# For consecutive K steps (where src == K and prev_src == K):
# interval = 48.5 px
# For other steps:
# interval = max(bh + 8, 36)

start_ay = 252.0
cur_ay = start_ay
prev_src = None
prev_k_ay = None

for s in steps_data:
    src = s["src"]
    num = s["num"]
    bh = s["bh"]
    
    if prev_src == "K" and src == "K" and num != "note":
        cur_ay += 48.5
    else:
        if prev_src is not None:
            # gap to previous arrow
            cur_ay += max(36.0, bh + 8.0)
            
    s["ay"] = cur_ay
    s["by"] = cur_ay - bh - 4.0
    
    if src == "K" and num != "note":
        if prev_k_ay is not None:
            dist = cur_ay - prev_k_ay
            print(f"Step {str(num):>4} K-dist: {dist:4.1f}px")
            assert dist >= 48.0
        prev_k_ay = cur_ay
    prev_src = src

print(f"\nFinal Step 19 ay: {cur_ay:.1f}px")
max_y = cur_ay + 24.0 # circle 19 bottom
print(f"Max Y: {max_y:.1f}px")
print(f"Bottom margin (1200 - max_y): {1200.0 - max_y:.1f}px")
assert 1200.0 - max_y >= 40.0, f"Bottom margin {1200 - max_y} < 40!"
print("SUCCESS: ALL CONSTRAINTS MET PERFECTLY!")
