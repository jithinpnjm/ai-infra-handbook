def test_wrap(label, lines, font_size, box_w, pad=20):
    full_text = " ".join(lines)
    full_text = " ".join(full_text.split())
    # check that text matches label exactly
    clean_label = " ".join(label.split())
    matches = (full_text == clean_label)
    max_len = max(len(l) for l in lines)
    w = max_len * 0.6 * font_size
    usable = box_w - 2 * pad
    fits = w <= usable
    status = "PASS" if (fits and matches) else "FAIL"
    print(f"[{status}] max_len={max_len}, w={w:.1f}px, usable={usable}px, matches={matches}")
    if not matches:
        print(f"   MISMATCH!\n   Expected: '{clean_label}'\n   Got:      '{full_text}'")
    for l in lines:
        print(f"      '{l}' ({len(l)} chars, {len(l)*0.6*font_size:.1f}px)")
    return fits and matches

print("=== MAGLEV HASHING in width 500 ===")
maglev_label = "Maglev hashing: a lookup table built from backend preference permutations; near-uniform load with minimal disruption; used by L4 LBs behind ECMP (Google Maglev, Meta Katran); table rebuild cost, small disruption on change"
maglev_lines = [
    "Maglev hashing: a lookup table",
    "built from backend preference",
    "permutations; near-uniform load",
    "with minimal disruption; used",
    "by L4 LBs behind ECMP (Google",
    "Maglev, Meta Katran); table",
    "rebuild cost, small disruption",
    "on change"
]
test_wrap(maglev_label, maglev_lines, 24, 500, 20)

print("\n=== L4 TIER behind ECMP in width 500 ===")
l4_label = "L4 tier behind ECMP: any node computes the same backend for the same 5-tuple without synchronised state"
l4_lines = [
    "L4 tier behind ECMP: any",
    "node computes the same",
    "backend for the same 5-tuple",
    "without synchronised state"
]
test_wrap(l4_label, l4_lines, 24, 500, 20)

print("\n=== LLM PREFIX CACHE in width 500 ===")
llm_label = "LLM prefix cache: consistent hashing on a session ID or prompt-prefix hash, with bounded loads that spill to the next replica when one exceeds its share"
llm_lines = [
    "LLM prefix cache: consistent",
    "hashing on a session ID or",
    "prompt-prefix hash, with bounded",
    "loads that spill to the next",
    "replica when one exceeds",
    "its share"
]
test_wrap(llm_label, llm_lines, 24, 500, 20)

print("\n=== CONSISTENT HASHING TITLE in width 500 (with icon 60px) ===")
ch_title_label = "Consistent hashing (ring, rendezvous, jump hash)"
ch_title_lines = [
    "Consistent hashing",
    "(ring, rendezvous,",
    "jump hash)"
]
test_wrap(ch_title_label, ch_title_lines, 30, 500 - 60, 20)
