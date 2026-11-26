def check_fix():
    fixes = [
        ("Exceptions", [
            "catch the narrowest exception,",
            "log once at the top"
        ]),
        ("Files", [
            "atomic replace, fsync, attempt",
            "then handle, encoding=utf-8"
        ]),
        ("Subprocess", [
            "argument list, timeout, check,",
            "machine-readable output,",
            "communicate, wait"
        ]),
        ("Global state", [
            "copy the environment for the",
            "child, pass explicit paths"
        ]),
        ("Re-runs", [
            "dry-run mode, a lock against",
            "overlapping runs, UTC timestamps",
            "rather than naive ones"
        ]),
        ("Signals", [
            "set a flag, finish and exit"
        ]),
        ("Untrusted input", [
            "validate member paths,",
            "filter=data, safe_load"
        ])
    ]
    for area, lines in fixes:
        print(f"=== {area} ===")
        for l in lines:
            w_sans = len(l) * 24 * 0.60
            w_mono = len(l) * 24 * 0.62
            print(f"  len={len(l):2d} | sans={w_sans:5.1f}px | mono={w_mono:5.1f}px | '{l}'")
check_fix()
