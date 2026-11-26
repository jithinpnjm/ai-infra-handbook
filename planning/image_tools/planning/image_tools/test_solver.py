# Precision layout solver for GPU CLI infographic

def solve():
    # Let's verify text wrapping and box dimensions
    # For every text block, calculate tw, ascent, descent, and check all 4 paddings >= 16 px.
    
    # 1. Title: 48px bold
    title_l1 = "The GPU diagnostics CLI in four layers, "
    title_l2 = "with exit codes"
    w_t1 = len(title_l1) * 0.6 * 48
    w_t2 = len(title_l2) * 0.6 * 48
    print(f"Title w1={w_t1:.1f}, w2={w_t2:.1f}")
    assert w_t1 <= 1520 and w_t2 <= 1520
solve()
