footer_lines = [
    "how the gateway observes a mid-stream break depends on its design, so name the assumption you make;",
    "also count the outcome the customer sees, not each attempt, and track retries separately"
]

print("--- Footer in 1460px ---")
for l in footer_lines:
    w = len(l) * 0.6 * 24
    print(f"  '{l}': len={len(l)}, w={w:.1f}, pad_in_1460={(1460-w)/2:.1f}")

