import re

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

# Let's inspect the cards:
# Height budget: 1200
# Title: 48px bold.
# y = 42, dy = 44 (or single line if wrapped or 2 lines:
# "Why web load balancing assumptions fail"
# "for LLM serving: five differences"
# Top of title: 42 - 48 * 0.8 = 3.6 (pad_t from 0 = 3.6). But title is not in a card, it's canvas title.

# Row 0: Scenario & Flow visual
# Row 1: Diff 1 & Resp 1
# Row 2: Diff 2 & Resp 2
# Row 3: Diff 3 & Resp 3
# Row 4: Diff 4 & Resp 4
# Row 5: Diff 5 & Resp 5
# Bottom bar: Takeaway bar

# Let's find vertical allocation so each card has pad_t >= 16 and pad_b >= 16:
