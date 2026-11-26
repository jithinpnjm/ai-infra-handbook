def wrap_to_limit(words, max_chars):
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

c2_text = "different weights produce different KV values; reusing a block from old weights would feed the new model numbers it never computed, wrong answers with no error; key the prefix cache and cache-aware routing by model version so no hit crosses a version boundary"
c2_lines = wrap_to_limit(c2_text.split(), 42)
print("C2 lines (max 42 chars):", len(c2_lines))
for l in c2_lines:
    w = len(l) * 24 * 0.6
    print(f"  [{len(l)} chars, {w:.1f}px] '{l}'")

c3_text = "a checkpoint with the wrong tokenizer fails quietly, garbage output and green infrastructure; the registry record makes weights, tokenizer and config one object with one version"
c3_lines = wrap_to_limit(c3_text.split(), 42)
print("\nC3 lines (max 42 chars):", len(c3_lines))
for l in c3_lines:
    w = len(l) * 24 * 0.6
    print(f"  [{len(l)} chars, {w:.1f}px] '{l}'")

c4_text = "a user who sees both versions in one conversation may see style change midway; sticky routing by tenant or session during the canary sends one user back to the same version every time; this is the difference between a canary and an A/B test"
c4_lines = wrap_to_limit(c4_text.split(), 42)
print("\nC4 lines (max 42 chars):", len(c4_lines))
for l in c4_lines:
    w = len(l) * 24 * 0.6
    print(f"  [{len(l)} chars, {w:.1f}px] '{l}'")

c1_text = "Request accepted by the old version and rejected by the new in the same minute: two versions run at once during a rollout"
c1_lines = wrap_to_limit(c1_text.split(), 42)
print("\nC1 lines (max 42 chars):", len(c1_lines))
for l in c1_lines:
    w = len(l) * 24 * 0.6
    print(f"  [{len(l)} chars, {w:.1f}px] '{l}'")
