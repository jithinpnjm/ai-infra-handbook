fix_lines = [
    "count a stream good only if it ends normally;",
    "add a gateway counter for streams that ended with a server-side abort;",
    "cross-check against vllm:request_success_total by finished_reason;",
    "do not alert on abort alone because client disconnects count as abort"
]

print("--- Fix list in 1380px ---")
for l in fix_lines:
    w = len(l) * 0.6 * 24
    print(f"  '{l}': len={len(l)}, w={w:.1f}, pad_in_1380={(1380-w)/2:.1f}")

