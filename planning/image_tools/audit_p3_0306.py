import xml.etree.ElementTree as ET
import re

svg_file = "p3-0306-symptom-ladder.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# Title text check
title_text = "".join(children[0].itertext()).strip()
print(f"   Title text: '{title_text}'")
assert title_text == "From symptom to likely cause, with the first tool to use", f"Unexpected title text: {title_text}"

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"Expected width 1600, got {width}"
assert viewBox == "0 0 1600 1200", f"Expected viewBox '0 0 1600 1200', got {viewBox}"
assert height == "1200", f"Expected height 1200, got {height}"

# 3. Check font-size >= 24 on all text and tspans
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")

# 4. Expected labels
expected_labels = [
    "From symptom to likely cause, with the first tool to use",
    "Tasks stall, timeouts everywhere, slow callback warnings",
    "blocking the event loop",
    "async APIs or to_thread",
    "Work never happens; was never awaited warning",
    "un-awaited coroutine",
    "await or create_task",
    "Task exception was never retrieved",
    "dropped task reference",
    "keep references, await or add done callbacks",
    "Cannot cancel or shut down",
    "swallowed CancelledError",
    "re-raise it, no bare except",
    "Hangs after network blips",
    "missing timeouts",
    "wait_for or timeout on every await; client timeout=",
    "OOM, too many open files, target overload",
    "unbounded fan-out",
    "semaphores, bounded queues, islice feeding",
    "Rare wrong results",
    "thread-unsafe shared state",
    "locks, queues, thread-local, immutable data",
    "Everything idle forever",
    "deadlock",
    "lock ordering, timeouts; faulthandler.dump_traceback_later(60); py-spy dump",
    "Hangs in children, CUDA errors",
    "fork with threads, CUDA or locks",
    "spawn or forkserver",
    "Can't pickle local object",
    "pickle errors",
    "top-level functions",
    "Memory growth in pools",
    "worker leaks",
    "maxtasksperchild, tracemalloc",
    "Defunct processes, leftover workers",
    "zombies or orphans",
    "wait(), context managers, process groups, supervisors",
    "CPU throttling, slow runs",
    "oversubscription",
    "match cgroup limits, OMP_NUM_THREADS=1",
    "Target collapse",
    "thundering herd or retry storm",
    "jittered backoff, limits, circuit breakers",
    "Silent partial results",
    "lost exceptions in threads",
    "futures, threading.excepthook",
    "ValueError: signal only works in main thread",
    "signal in a non-main thread",
    "install handlers in the main thread or loop.add_signal_handler",
    "RuntimeError",
    "asyncio.run() inside a running loop (Jupyter)",
    "await instead; nest_asyncio only for notebooks",
    "a timeout on every wait, a bound on every queue and pool",
    "Start from the symptom you see"
]

found_texts = [t for t, fs in text_elements]

print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
        print(f"   [FAIL] count={cnt}: '{exp}'")
    else:
        print(f"   [OK] '{exp[:55]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        if f in words:
            raise ValueError(f"Forbidden word '{f}' found in text: '{t}'")

print("\n6. No forbidden style words in any text!")

# 6. Colors present
with open(svg_file) as f:
    svg_str = f.read()

assert "#f5f8f5" in svg_str, "Background color #f5f8f5 missing!"
assert "#303a36" in svg_str, "Text color #303a36 missing!"
assert "#207448" in svg_str, "Main green #207448 missing!"
assert "#e8f1ea" in svg_str, "Light green panel #e8f1ea missing!"
assert "#db8129" in svg_str, "Orange #db8129 missing!"

print("\n7. All required colors present!")

# 7. Horizontal paddings check
print("\n8. Checking horizontal paddings on all text lines:")
rects = []
for el in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(el.attrib.get('x', 0))
    y = float(el.attrib.get('y', 0))
    w = float(el.attrib.get('width', 0))
    h = float(el.attrib.get('height', 0))
    if w > 0 and h > 0 and w < 1600:
        rects.append((x, y, w, h))

for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    anchor = elem.attrib.get('text-anchor', 'start')
    fs = float(elem.attrib.get('font-size', 24))
    ff = elem.attrib.get('font-family', '')
    is_mono = 'monospace' in ff
    factor = 0.62 if is_mono else 0.60
    
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        for tsp in tspans:
            txt = (tsp.text or '').strip()
            if not txt:
                continue
            tx = float(tsp.attrib.get('x', elem.attrib.get('x', 0)))
            lw = len(txt) * factor * fs
            if anchor == 'middle':
                left = tx - lw / 2
                right = tx + lw / 2
            else:
                left = tx
                right = tx + lw
            # find matching rect
            # Table columns: col 1 [40..500], col 2 [500..920], col 3 [920..1560]
            if left >= 40 and right <= 500:
                pad_l = left - 40
                pad_r = 500 - right
                assert pad_l >= 16 and pad_r >= 16, f"Pad fail in col 1: '{txt}' L={pad_l:.1f}, R={pad_r:.1f}"
            elif left >= 500 and right <= 920:
                pad_l = left - 500
                pad_r = 920 - right
                assert pad_l >= 16 and pad_r >= 16, f"Pad fail in col 2: '{txt}' L={pad_l:.1f}, R={pad_r:.1f}"
            elif left >= 920 and right <= 1560:
                pad_l = left - 920
                pad_r = 1560 - right
                assert pad_l >= 16 and pad_r >= 16, f"Pad fail in col 3: '{txt}' L={pad_l:.1f}, R={pad_r:.1f}"
            else:
                # Banner or bottom bar
                pad_l = left - 40
                pad_r = 1560 - right
                assert pad_l >= 16 and pad_r >= 16, f"Pad fail in banner: '{txt}' L={pad_l:.1f}, R={pad_r:.1f}"
    else:
        txt = (elem.text or '').strip()
        tx = float(elem.attrib.get('x', 0))
        lw = len(txt) * factor * fs
        if anchor == 'middle':
            left = tx - lw / 2
            right = tx + lw / 2
        else:
            left = tx
            right = tx + lw
        if left >= 40 and right <= 500:
            pad_l = left - 40
            pad_r = 500 - right
            assert pad_l >= 16 and pad_r >= 16, f"Pad fail in col 1: '{txt}' L={pad_l:.1f}, R={pad_r:.1f}"
        elif left >= 500 and right <= 920:
            pad_l = left - 500
            pad_r = 920 - right
            assert pad_l >= 16 and pad_r >= 16, f"Pad fail in col 2: '{txt}' L={pad_l:.1f}, R={pad_r:.1f}"
        elif left >= 920 and right <= 1560:
            pad_l = left - 920
            pad_r = 1560 - right
            assert pad_l >= 16 and pad_r >= 16, f"Pad fail in col 3: '{txt}' L={pad_l:.1f}, R={pad_r:.1f}"
        else:
            pad_l = left - 40
            pad_r = 1560 - right
            assert pad_l >= 16 and pad_r >= 16, f"Pad fail in banner: '{txt}' L={pad_l:.1f}, R={pad_r:.1f}"

print("   All text lines satisfy horizontal padding >= 16px!")
print("\n>>> ALL CHECKS PASSED PERFECTLY! <<<")
