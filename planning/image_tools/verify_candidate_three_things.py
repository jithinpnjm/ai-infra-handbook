import xml.etree.ElementTree as ET
import re

def verify(svg_path):
    print(f"=== Auditing {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure
    children = list(root)
    t0 = children[0].tag.split('}')[-1]
    t1 = children[1].tag.split('}')[-1]
    print(f"1. Children: <{t0}>, <{t1}>")
    assert t0 == 'title', f"Child 0 must be <title>, got <{t0}>"
    assert t1 == 'desc', f"Child 1 must be <desc>, got <{t1}>"

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600"
    assert viewBox == f"0 0 1600 {height}"
    H_val = float(height)
    assert 900 <= H_val <= 1200

    # 3. All text elements >= 24px
    text_elements = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', '0'))
        combined = " ".join("".join(el.itertext()).split())
        assert fs >= 24, f"Text '{combined}' font-size {fs} < 24!"
        for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
            tfs = float(ts.attrib.get('font-size', fs))
            assert tfs >= 24, f"tspan in '{combined}' font-size {tfs} < 24!"
        text_elements.append((combined, fs))

    print(f"3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")

    # 4. Expected labels
    expected_labels = [
        "Three things a runtime must do to give a container a GPU",
        "Namespaces and cgroups know nothing about GPUs, so the GPU layer supplies the pieces",
        "Make the device nodes exist in the container's mount namespace",
        "by bind mount or mknod",
        "/dev/nvidia0..N, /dev/nvidiactl, /dev/nvidia-uvm, /dev/nvidia-uvm-tools, /dev/nvidia-modeset",
        "/dev/nvidia-caps/*",
        "ls -l /dev/nvidia* inside the container",
        "Allow those devices in the devices cgroup",
        "runtime class, CDI spec, cgroup driver match",
        "Mount the driver user-space libraries and binaries from the host",
        "libcuda.so, NVML, nvidia-smi must match the host kernel driver version",
        "the CUDA toolkit libraries can live in the image, but the driver library cannot",
        "Automation: NVIDIA Container Toolkit (nvidia-container-runtime, nvidia-ctk, libnvidia-container); historically an OCI prestart hook, now prefers CDI, a declarative spec file listing device nodes, mounts and environment variables, created with nvidia-ctk cdi generate",
        "nvidia-smi fails with driver/library version mismatch: the container has its own libcuda not matching the host driver, or the toolkit hook is missing",
        "GPU visible on the host but not in the container: nodes missing, devices cgroup denies, or runtime not configured",
        "Do not bake driver libraries into images; let the toolkit inject them from the host"
    ]
    step_numbers = ["1", "2", "3"]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels:")
    for lbl in expected_labels:
        norm_lbl = re.sub(r'\s+', ' ', lbl)
        cnt = found_texts.count(norm_lbl)
        assert cnt == 1, f"Expected label '{lbl}' count {cnt} != 1!"
        print(f"   [PASS] count=1: '{lbl[:55]}...'")

    print("\n   Checking step numbers:")
    for num in step_numbers:
        cnt = found_texts.count(num)
        assert cnt == 1, f"Step number '{num}' count {cnt} != 1!"
        print(f"   [PASS] count=1: '{num}'")

    # 5. Extras check
    all_allowed = set(expected_labels + step_numbers)
    extras = [t for t in found_texts if t not in all_allowed]
    assert len(extras) == 0, f"Unexpected extra text: {extras}"
    assert len(found_texts) == len(expected_labels) + len(step_numbers), f"Text count {len(found_texts)} mismatch!"
    print("\n5. Zero extra text elements: PASS")

    # 6. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("6. No forbidden words found: PASS")

    # 7. Orange usage
    svg_str = open(svg_path).read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 count: {len(orange_matches)}")
    assert len(orange_matches) == 1, f"Orange used {len(orange_matches)} times, expected exactly 1!"
    print("   PASS: Orange used exactly once for the driver version match card.")

    # 8. Check arrows
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    total_arrows = len(lines_with_marker) + len(paths_with_marker)
    print(f"\n8. Total arrows: {total_arrows} (expected 0)")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

    # 9. Outside margins (>= 40px)
    print(f"\n9. Checking outside margins on rects (>= 40px):")
    for r in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(r.attrib.get('x', '0'))
        ry = float(r.attrib.get('y', '0'))
        rw = float(r.attrib.get('width', '0'))
        rh = float(r.attrib.get('height', '0'))
        if rw < 1600 and rw > 100: # major content boxes, not tiny icon parts or background
            lm = rx
            rm = 1600 - (rx + rw)
            tm = ry
            bm = H_val - (ry + rh)
            assert lm >= 39.9, f"Left margin {lm} < 40 for rect w={rw}"
            assert rm >= 39.9, f"Right margin {rm} < 40 for rect w={rw}"
            assert tm >= 39.9, f"Top margin {tm} < 40 for rect w={rw}"
            assert bm >= 39.9, f"Bottom margin {bm} < 40 for rect w={rw}"
            print(f"   [PASS] Rect x={rx}, y={ry}, w={rw}, h={rh}: lm={lm}, rm={rm}, tm={tm}, bm={bm}")

    print("   PASS: Outside margins >= 40px for all rects.")

    # 10. Check horizontal padding on all text lines inside boxes (>= 16px)
    print("\n10. Checking text padding inside boxes (>= 16px)...")
    lines_to_check = [
        # (desc, text, ftype, fsize, box_w)
        ("Top strip", "Namespaces and cgroups know nothing about GPUs, so the GPU layer supplies the pieces", "sans", 24, 1520),
        ("Col 1 title 1", "Make the device ", "sans", 30, 480),
        ("Col 1 title 2", "nodes exist in the ", "sans", 30, 480),
        ("Col 1 title 3", "container's mount ", "sans", 30, 480),
        ("Col 1 title 4", "namespace", "sans", 30, 480),
        ("Col 1 Item 1", "by bind mount or mknod", "sans", 24, 440),
        ("Col 1 Item 2 line 1", "/dev/nvidia0..N, ", "mono", 24, 440),
        ("Col 1 Item 2 line 2", "/dev/nvidiactl, ", "mono", 24, 440),
        ("Col 1 Item 2 line 3", "/dev/nvidia-uvm, ", "mono", 24, 440),
        ("Col 1 Item 2 line 4", "/dev/nvidia-uvm-tools, ", "mono", 24, 440),
        ("Col 1 Item 2 line 5", "/dev/nvidia-modeset", "mono", 24, 440),
        ("Col 1 Item 3", "/dev/nvidia-caps/*", "mono", 24, 440),
        ("Col 1 Item 4 line 1", "ls -l /dev/nvidia* ", "mono", 24, 440),
        ("Col 1 Item 4 line 2", "inside the container", "sans", 24, 440),
        ("Col 2 title 1", "Allow those devices in ", "sans", 30, 480),
        ("Col 2 title 2", "the devices cgroup", "sans", 30, 480),
        ("Col 2 check line 1", "runtime class, CDI spec, ", "sans", 24, 440),
        ("Col 2 check line 2", "cgroup driver match", "sans", 24, 440),
        ("Col 3 title 1", "Mount the driver ", "sans", 30, 480),
        ("Col 3 title 2", "user-space libraries ", "sans", 30, 480),
        ("Col 3 title 3", "and binaries from ", "sans", 30, 480),
        ("Col 3 title 4", "the host", "sans", 30, 480),
        ("Col 3 card 1 line 1", "libcuda.so, NVML, ", "sans", 24, 440),
        ("Col 3 card 1 line 2", "nvidia-smi must match ", "sans", 24, 440),
        ("Col 3 card 1 line 3", "the host kernel driver ", "sans", 24, 440),
        ("Col 3 card 1 line 4", "version", "sans", 24, 440),
        ("Col 3 card 2 line 1", "the CUDA toolkit libraries ", "sans", 24, 440),
        ("Col 3 card 2 line 2", "can live in the image, ", "sans", 24, 440),
        ("Col 3 card 2 line 3", "but the driver library ", "sans", 24, 440),
        ("Col 3 card 2 line 4", "cannot", "sans", 24, 440),
        ("Automation line 1", "Automation: NVIDIA Container Toolkit (nvidia-container-runtime, nvidia-ctk, libnvidia-container); ", "sans", 24, 1520),
        ("Automation line 2", "historically an OCI prestart hook, now prefers CDI, a declarative spec file listing device nodes, ", "sans", 24, 1520),
        ("Automation line 3", "mounts and environment variables, created with nvidia-ctk cdi generate", "sans", 24, 1520),
        ("Symptom 1 line 1", "nvidia-smi fails with driver/library version ", "sans", 24, 740),
        ("Symptom 1 line 2", "mismatch: the container has its own libcuda ", "sans", 24, 740),
        ("Symptom 1 line 3", "not matching the host driver, or the toolkit ", "sans", 24, 740),
        ("Symptom 1 line 4", "hook is missing", "sans", 24, 740),
        ("Symptom 2 line 1", "GPU visible on the host but not in the ", "sans", 24, 740),
        ("Symptom 2 line 2", "container: nodes missing, devices cgroup ", "sans", 24, 740),
        ("Symptom 2 line 3", "denies, or runtime not configured", "sans", 24, 740),
        ("Bottom bar", "Do not bake driver libraries into images; let the toolkit inject them from the host", "sans", 24, 1520),
    ]

    for desc, text, ftype, fsize, box_w in lines_to_check:
        mult = 0.62 if ftype == "mono" else 0.60
        est_w = len(text) * fsize * mult
        pad = (box_w - est_w) / 2
        assert pad >= 16.0, f"[{desc}] '{text}': pad {pad:.1f} < 16.0px (box_w={box_w})"
        print(f"   [PASS] {desc:22s}: pad={pad:5.1f}px (box={box_w}, est_w={est_w:5.1f}px) | '{text}'")

    print("\nALL VERIFICATIONS PASSED!")

if __name__ == "__main__":
    verify("candidate_three_things.svg")
