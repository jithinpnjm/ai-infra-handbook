def sans_w(text, fs=24):
    return len(text) * 0.6 * fs

questions = [
    "Is demand rising or falling? Compare the 1, 5 and 15 minute numbers.",
    "Did the kernel log errors, including OOM kills?",
    "Run queue, swapping and overall CPU split, one second at a time.",
    "Is one CPU busy while the others idle?",
    "Which processes use the CPU, and user or kernel time?",
    "Disk IOPS, throughput, wait time and percent busy.",
    "Memory in use, including the page cache.",
    "Network interface throughput and packets.",
    "TCP connection rates and retransmits.",
    "A sanity overview of everything above."
]

for i, q in enumerate(questions, 1):
    print(f"Row {i:2d} ({len(q):2d} chars, w={sans_w(q):.1f} px): {q}")

