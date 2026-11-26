def test_wrap(name, lines, box_w, fs=24, is_mono=False):
    max_w = box_w - 32
    print(f"\n--- {name} (box_w={box_w}, max_w={max_w}) ---")
    all_ok = True
    for l in lines:
        w = len(l) * (0.62 if is_mono else 0.6) * fs
        pad = (box_w - w) / 2
        ok = w <= max_w
        if not ok: all_ok = False
        print(f"  [{'OK' if ok else 'OVERFLOW'}] w={w:.1f} (pad={pad:.1f}): '{l}'")
    return all_ok

# Let's test widths:
# Box 1: 250 px
test_wrap("Stage 1 cmd", ["awk print $1"], 250, fs=24, is_mono=True)
test_wrap("Stage 1 note", ["keep the", "client address", "field"], 250, fs=24)

# Box 2: 240 px
test_wrap("Stage 2 cmd", ["sort"], 240, fs=26, is_mono=True)
test_wrap("Stage 2 note", ["equal addresses", "become", "neighbours"], 240, fs=24) # wait, "equal addresses" is 15 chars = 216 px. 240-32=208!
test_wrap("Stage 2 note alt", ["equal", "addresses", "become", "neighbours"], 240, fs=24)

# Box 3: 240 px
test_wrap("Stage 3 cmd", ["uniq -c"], 240, fs=26, is_mono=True)
test_wrap("Stage 3 note", ["count each run", "of equal lines"], 240, fs=24)

# Box 4: 280 px
test_wrap("Stage 4 cmd", ["awk print $2, $1"], 280, fs=24, is_mono=True)
test_wrap("Stage 4 note", ["put address first,", "count second"], 280, fs=24)

# Box 5: 350 px
test_wrap("Stage 5 cmd 1", ["sort -k2,2nr -k1,1"], 350, fs=24, is_mono=True)
test_wrap("Stage 5 cmd 2", ["awk NR<=5"], 350, fs=24, is_mono=True)
test_wrap("Stage 5 note", [
    "rank by count, address breaks ties;",
    "awk instead of head so",
    "pipefail never reports exit 141"
], 350, fs=24)
