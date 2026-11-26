messages = [
    (1, "U", "A"),
    (2, "A", "S"),
    (3, "S", "A"),
    (4, "A", "K"),
    (5, "K", "K"),
    (6, "K", "D"),
    (7, "K", "V"),
    (8, "K", "R"),
    (9, "R", "C"),
    (10, "K", "R"),
    (11, "K", "R"),
    (12, "R", "X"),
    (13, "K", "A"),
    # note over K,X (no circle)
    (14, "U", "A"),
    (15, "A", "K"),
    (16, "K", "X"),
    (17, "K", "R"),
    (18, "K", "V"),
    (19, "K", "A")
]

for i in range(len(messages)):
    step, src, dst = messages[i]
    print(f"Step {step:2}: sender = {src}")
