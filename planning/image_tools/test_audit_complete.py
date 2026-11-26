import re
import xml.etree.ElementTree as ET

def test_full_svg():
    svg_code = open("candidate_experiment.svg").read()
    root = ET.fromstring(svg_code)

    # Verify all text elements
    expected = [
        "The ten-minute experiment: the same job run three ways",
        "Three lanes for 8 jobs of burn(seed), each chaining 1,000,000 SHA-256 hashes.",
        "sequential",
        "one interpreter runs jobs 0 to 7 one after another",
        "4 threads: ThreadPoolExecutor(max_workers=4)",
        "four threads share one GIL and take turns, so 'about as long as sequential, or a little longer'",
        "4 processes: ProcessPoolExecutor(max_workers=4)",
        "four interpreters, each with its own GIL, 'clearly faster' on a machine with at least four free cores",
        "change burn to time.sleep(1) and rerun: now threads win because the GIL is released while a thread sleeps",
        "timed() prints label and seconds with perf_counter; your timings depend on your hardware, so record your own",
        "a thread that computes for a long time is paused every 5 ms (sys.getswitchinterval()), an asyncio task is never paused that way and runs until an await",
        "The GIL gives threads turns, processes get their own lock"
    ]

    texts = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
        texts.append(full)
        fs = float(elem.attrib.get('font-size'))
        assert fs >= 24, f"Text font size {fs} < 24 in '{full}'"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font size {tfs} < 24 in '{full}'"

    print("Found texts count:", len(texts))
    assert len(texts) == len(expected), f"{len(texts)} != {len(expected)}"
    for exp in expected:
        cnt = texts.count(exp)
        assert cnt == 1, f"Expected '{exp}' count 1, got {cnt}"

    for t in texts:
        assert t in expected, f"Unexpected '{t}'"

    print("All label verifications passed perfectly!")

test_full_svg()
