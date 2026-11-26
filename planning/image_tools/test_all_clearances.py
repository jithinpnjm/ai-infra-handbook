from test_clearances import check_box

print("=== CHECKING ALL 11 TEXT ELEMENTS FOR CLEARANCES ===")

# Top event
assert check_box("Top event", 40, 88, 1520, 92, 68, 106, 56, 56, [
    ("kubelet sends SIGTERM to PID 1 (after preStop)", 145, 146)
], 30)

# Lane A Header
assert check_box("Lane A Header", 40, 206, 740, 122, 68, 226, 56, 56, [
    ("PID 1 is /bin/sh or a process", 145, 252),
    ("with no SIGTERM handler", 145, 288)
], 28)

# Lane A Step 1
assert check_box("Lane A Step 1", 65, 328, 690, 124, 85, 362, 56, 56, [
    ("the kernel ignores signals to PID 1", 165, 370),
    ("in a PID namespace unless a", 165, 398),
    ("handler is registered", 165, 426)
], 24)

# Lane A Step 2
assert check_box("Lane A Step 2", 65, 482, 690, 114, 85, 511, 56, 56, [
    ("nothing happens for the whole", 165, 530),
    ("terminationGracePeriodSeconds", 165, 564)
], 24, is_mono=True)

# Lane A Step 3
assert check_box("Lane A Step 3", 65, 626, 690, 104, 85, 650, 56, 56, [
    ("SIGKILL, which the kernel", 165, 670),
    ("never ignores", 165, 704)
], 26)

# Lane A Step 4
assert check_box("Lane A Step 4", 65, 760, 690, 100, 85, 782, 56, 56, [
    ("pod takes 30 s to die", 165, 822)
], 30)

# Lane B Header
assert check_box("Lane B Header", 820, 206, 740, 122, 848, 226, 56, 56, [
    ("PID 1 registers a SIGTERM handler", 925, 264)
], 30)

# Lane B Step 1
assert check_box("Lane B Step 1", 845, 328, 690, 124, 865, 362, 56, 56, [
    ("saves checkpoint or drains,", 945, 380),
    ("exits 0", 945, 416)
], 28)

# Lane B Step 2
assert check_box("Lane B Step 2", 845, 500, 690, 114, 865, 529, 56, 56, [
    ("pod ends early", 945, 568)
], 32)

# Side note
assert check_box("Side note", 40, 906, 1520, 130, 68, 943, 56, 56, [
    ("shell-form entrypoint can swallow SIGTERM; for training treat SIGTERM as checkpoint now", 145, 960),
    ("and set the grace period from a measured checkpoint time plus margin", 145, 994)
], 24)

print("ALL CLEARANCE CHECKS PASSED PERFECTLY!")
