def test_lines(lines, box_w, fs=24):
    max_w = box_w - 32
    print(f"box_w={box_w}, max_w={max_w}")
    for l in lines:
        w = len(l) * 0.6 * fs
        pad = (box_w - w) / 2
        print(f"  [{'OK' if w <= max_w else 'FAIL'}] w={w:.1f}, pad={pad:.1f}: '{l}'")

print("--- Stage 5 Note wrapped (box_w=350) ---")
test_lines([
    "rank by count,",
    "address breaks ties;",
    "awk instead of head so",
    "pipefail never",
    "reports exit 141"
], 350)

print("\n--- Stage 4 Note wrapped (box_w=280) ---")
test_lines([
    "put address first,", # wait, prompt has no comma: "put address first, count second" -> wait, prompt says 'put address first, count second'
    # Actually prompt says: 'put address first, count second'
], 280)
