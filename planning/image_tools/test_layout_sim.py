# Let's inspect the labels and their dimensions
labels = [
    # root
    ("root_title", "Run vmstat 2 and start at line 2", 30, True),
    ("root_note", "Line 1 is the average since boot", 24, False),
    
    # Branch 1
    ("c1", "All idle: id about 99, si and so at 0", 24, False),
    ("o1", "Healthy", 30, True),
    
    # Branch 2
    ("c2", "High us, low wa", 24, False),
    ("o2", "CPU-bound compute", 30, True),
    
    # Branch 3
    ("c3", "High wa and b", 24, False),
    ("o3", "I/O-bound work: look at iostat", 30, True),
    
    # Branch 4
    ("c4", "Growing so, falling free or cache", 24, False),
    ("o4", "Memory exhausted: kernel is paging out", 30, True),
    
    # Branch 5
    ("c5", "High r with high us plus sy", 24, False),
    ("o5", "CPU contention", 30, True),
    
    # Branch 6
    ("c6", "High sy and cs", 24, False),
    ("o6", "Many system calls or lock contention", 30, True),
    
    # Branch 7
    ("c7", "High st", 24, False),
    ("o7", "Noisy neighbours on a shared VM", 30, True),
    
    # Caption
    ("caption", "Read the trend across several lines, not one number.", 26, True),
]

for name, text, size, bold in labels:
    w = len(text) * 0.6 * size
    print(f"{name:12s}: len={len(text):2d}, size={size:2d}, est_width={w:6.1f}px | '{text}'")

