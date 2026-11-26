# Let us find y_steps such that:
# y1 >= 262
# y20 <= 1134 (so 1134 + 24 = 1158 <= 1160)
# for any same-sender pair, dy >= 48 (e.g. 5->6, 6->7, 7->8, 10->11, 17->18, 18->19, 19->20)
# for note, height 56px, so spacing around it is >= 46px
# for others, dy >= 40px

senders = ["U", "A", "S", "A", "K", "K", "K", "K", "R", "K", "K", "R", "K", "NOTE", "U", "A", "K", "K", "K", "K"]

y = 264
ys = [y]
for i in range(1, len(senders)):
    s_curr = senders[i]
    s_prev = senders[i-1]
    if s_curr == s_prev and s_curr != "NOTE":
        dy = 48
    elif s_curr == "NOTE" or s_prev == "NOTE":
        dy = 46
    elif i == 2: # Step 3 (2 lines)
        dy = 44
    elif i == 4: # Step 5 (2 lines)
        dy = 44
    elif i == 12: # Step 13 (2 lines)
        dy = 44
    else:
        dy = 41
    y += dy
    ys.append(y)

for i, (s, y_val) in enumerate(zip(senders, ys)):
    print(f"Step {i+1:2d} ({s:4s}): y = {y_val}")

print(f"\nFinal step at y = {ys[-1]}, circle bottom = {ys[-1] + 24}")
print(f"Margin to 1200 = {1200 - (ys[-1] + 24)}")
assert ys[-1] + 24 <= 1160, "Bottom margin < 40!"
print("BOTTOM MARGIN >= 40 (PASS)!")
