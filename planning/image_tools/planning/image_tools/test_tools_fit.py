def test_tools():
    # Card 1: width 560
    c1_lines = [
        "python -m build makes",
        "dist/myops-0.3.1.tar.gz (sdist) and",
        "dist/myops-0.3.1-py3-none-any.whl (wheel)"
    ]
    print("Card 1 (w=560, usable=528):")
    for l in c1_lines:
        w = len(l) * 24 * 0.62
        print(f"  {w:5.1f}px | '{l}'")

    # Card 2: width 440
    c2_lines = [
        "python -m pip debug --verbose",
        "lists the supported tags"
    ]
    print("\nCard 2 (w=440, usable=408):")
    for l in c2_lines:
        w = len(l) * 24 * 0.62
        print(f"  {w:5.1f}px | '{l}'")

    # Card 3: width 480
    c3_lines = [
        "pip download --only-binary=:all:",
        "--platform manylinux2014_aarch64 ..."
    ]
    print("\nCard 3 (w=480, usable=448):")
    for l in c3_lines:
        w = len(l) * 24 * 0.62
        print(f"  {w:5.1f}px | '{l}'")

test_tools()
