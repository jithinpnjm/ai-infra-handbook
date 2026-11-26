from test_clearances import check_box

# If box y=328, h=124 (bottom 452).
# lines at 370, 398, 426
check_box("Lane A Step 1", 65, 328, 690, 124, 85, 362, 56, 56, [
    ("the kernel ignores signals to PID 1", 165, 370),
    ("in a PID namespace unless a", 165, 398),
    ("handler is registered", 165, 426)
], 24)
