text = "(honoured only if it is not world-writable: a folder any user can change cannot be trusted)"
words = text.split()

# If card width = 708 (x: 56..764), available width = 708 - 32 = 676px.
# Conservative max chars = 676 / (24 * 0.6) = 46.94 -> 46 chars!
# If 2 lines:
# Total chars = 91 chars.
# Can we split 91 chars into 2 lines of <= 46 chars?
# Let's test all possible 2-line splits:
found_2lines = False
for i in range(1, len(words)):
    l1 = " ".join(words[:i])
    l2 = " ".join(words[i:])
    if len(l1) <= 46 and len(l2) <= 46:
        print(f"2-line split possible! '{l1}' ({len(l1)} chars) | '{l2}' ({len(l2)} chars)")
        found_2lines = True

if not found_2lines:
    print("Cannot split into 2 lines with <= 46 chars each.")

# What about 3 lines?
# In 3 lines:
for i in range(1, len(words)):
    for j in range(i+1, len(words)):
        l1 = " ".join(words[:i])
        l2 = " ".join(words[i:j])
        l3 = " ".join(words[j:])
        if max(len(l1), len(l2), len(l3)) <= 35:
            print(f"3 lines: '{l1}' ({len(l1)}) | '{l2}' ({len(l2)}) | '{l3}' ({len(l3)})")
            break
    if max(len(l1), len(l2), len(l3)) <= 35:
        break
