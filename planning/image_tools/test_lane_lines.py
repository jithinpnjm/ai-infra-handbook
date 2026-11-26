def test_wrap_lines():
    lane1 = [
        "one interpreter runs jobs",
        "0 to 7 one after another"
    ]
    lane2 = [
        "four threads share one",
        "GIL and take turns, so",
        "'about as long as",
        "sequential, or a little",
        "longer'"
    ]
    lane3 = [
        "four interpreters, each",
        "with its own GIL,",
        "'clearly faster' on a",
        "machine with at least",
        "four free cores"
    ]
    
    print("--- Lane 1 ---")
    for l in lane1:
        w = len(l) * 24 * 0.6
        pad = 480 - 24 - w
        print(f"  w={w:5.1f} pad_r={pad:5.1f} | '{l}'")
        assert pad >= 16

    print("\n--- Lane 2 ---")
    for l in lane2:
        w = len(l) * 24 * 0.6
        pad = 480 - 24 - w
        print(f"  w={w:5.1f} pad_r={pad:5.1f} | '{l}'")
        assert pad >= 16

    print("\n--- Lane 3 ---")
    for l in lane3:
        w = len(l) * 24 * 0.6
        pad = 480 - 24 - w
        print(f"  w={w:5.1f} pad_r={pad:5.1f} | '{l}'")
        assert pad >= 16

test_wrap_lines()
