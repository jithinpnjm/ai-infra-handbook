import re

# We will test wrapping options for each text block.

def get_text_width(text, fs, is_mono=False):
    factor = 0.62 if is_mono else 0.6
    return len(text) * factor * fs

def wrap_text(full_text, max_w, fs, is_mono=False):
    words = full_text.split()
    lines = []
    curr = []
    for w in words:
        cand = " ".join(curr + [w])
        if get_text_width(cand, fs, is_mono) <= max_w:
            curr.append(w)
        else:
            if curr:
                lines.append(" ".join(curr))
                curr = [w]
            else:
                lines.append(w)
                curr = []
    if curr:
        lines.append(" ".join(curr))
    return lines

print("Testing wrapping...")
