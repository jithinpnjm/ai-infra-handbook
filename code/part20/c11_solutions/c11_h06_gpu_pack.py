"""H6: choose models to load on one GPU to maximise value within a memory budget (0/1 knapsack)."""


def gpu_pack(mem, value, capacity):
    """Return (best_value, chosen_indices). O(n * capacity) time and space."""
    n = len(mem)
    table = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        m, v = mem[i - 1], value[i - 1]
        for c in range(capacity + 1):
            table[i][c] = table[i - 1][c]
            if m <= c and table[i - 1][c - m] + v > table[i][c]:
                table[i][c] = table[i - 1][c - m] + v
    chosen, c = [], capacity
    for i in range(n, 0, -1):
        if table[i][c] != table[i - 1][c]:
            chosen.append(i - 1)
            c -= mem[i - 1]
    return table[n][capacity], sorted(chosen)
