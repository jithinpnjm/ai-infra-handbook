#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys
import pathlib

def audit_svg(svg_path):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

    # 2. Dimensions
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"Expected width 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

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
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    expected_labels = [
        "CI hardening: least privilege, reproducibility, packaging and nightly runs",
        "Least privilege",
        "permissions: set to the minimum; pin third-party actions by SHA; never echo secrets; pull requests from forks are untrusted and get no secrets; pull_request_target only with great care",
        "Reproducible",
        "lock files, pinned base images, --require-hashes, hermetic builds, record tool versions in logs; cache dependencies and test data keyed on lock file hashes; minimum-dependency run: uv pip install --resolution lowest-direct validates lower bounds",
        "Packaging and release",
        "install the built wheel into a clean venv and run a smoke test: catches missing package data and wrong entry points; tag, changelog from conventional commits; version from the git tag with hatch-vcs or setuptools-scm; sign artefacts, provenance attestations, SBOM; protect the environment so publishing needs approval",
        "GPU and nightly",
        "GPU tests on self-hosted runners labelled gpu, ephemeral or containerised jobs, limit who can trigger, clean state between jobs; NVIDIA publishes GPU-enabled container images and the container toolkit",
        "nightly: full suite with random seeds, dependency audit, slow and integration tiers; notify on failure; track flakiness over time",
        "artefacts: coverage files, JUnit XML, failure logs; GitLab CI uses stages, needs, cache, artifacts:reports:junit, rules: and runner tags",
        "Order the jobs cheap to expensive, and make the required checks branch-protected"
    ]

    found_texts = [t for t, fs in text_elements]

    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:60]}...'")

    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n5. No forbidden words found! (PASS)")

    # 6. Check orange count
    svg_str = pathlib.Path(svg_path).read_text(encoding='utf-8')
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n8. All required colors present! (PASS)")

    # 9. Check external resources: no <image>, no <script>, no external fonts
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    print("\n9. No external images or scripts! (PASS)")

    # 10. Check text padding and bounds
    print("\n10. Checking text bounds & paddings...")
    boxes = {
        "panel-1": (40, 140, 740, 370),
        "panel-2": (820, 140, 740, 370),
        "panel-3": (40, 550, 740, 365),
        "panel-4": (820, 550, 740, 365),
        "footer": (40, 955, 1520, 94),
        "bottom-bar": (40, 1089, 1520, 70)
    }

    for gid, (bx, by, bw, bh) in boxes.items():
        g = root.find(f".//*[@id='{gid}']")
        assert g is not None, f"Group {gid} not found"
        for text in g.findall('{http://www.w3.org/2000/svg}text'):
            base_fs = float(text.attrib.get('font-size', 24))
            anchor = text.attrib.get('text-anchor', 'start')
            base_tx = float(text.attrib.get('x', 0))
            base_ty = float(text.attrib.get('y', 0))

            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            if not tspans:
                # single line
                t = (text.text or "").strip()
                if not t: continue
                fs = base_fs
                is_mono = "ui-monospace" in text.attrib.get('font-family', '') or "monospace" in text.attrib.get('font-family', '')
                w = len(t) * (0.62 if is_mono else 0.60) * fs
                if anchor == 'middle':
                    x_start = base_tx - w / 2
                    x_end = base_tx + w / 2
                elif anchor == 'end':
                    x_start = base_tx - w
                    x_end = base_tx
                else:
                    x_start = base_tx
                    x_end = base_tx + w

                top_y = base_ty - fs
                bot_y = base_ty + 0.25 * fs
                assert x_start >= bx + 16, f"Text '{t}' left padding {x_start - bx:.1f} < 16 in {gid}"
                assert x_end <= bx + bw - 16, f"Text '{t}' right padding {bx + bw - x_end:.1f} < 16 in {gid}"
                assert top_y >= by + 16, f"Text '{t}' top padding {top_y - by:.1f} < 16 in {gid}"
                assert bot_y <= by + bh - 16, f"Text '{t}' bot padding {by + bh - bot_y:.1f} < 16 in {gid}"
            else:
                curr_y = base_ty
                for tsp in tspans:
                    # check if tsp has nested tspans or text
                    t = "".join(tsp.itertext()).strip()
                    if not t: continue
                    fs = float(tsp.attrib.get('font-size', base_fs))
                    tsp_anchor = tsp.attrib.get('text-anchor', anchor)
                    tsp_x = float(tsp.attrib.get('x', base_tx))
                    dy = tsp.attrib.get('dy')
                    if dy is not None:
                        curr_y += float(dy)
                    else:
                        tsp_y = tsp.attrib.get('y')
                        if tsp_y is not None:
                            curr_y = float(tsp_y)

                    is_mono = "monospace" in tsp.attrib.get('font-family', '') or "monospace" in text.attrib.get('font-family', '')
                    w = len(t) * (0.62 if is_mono else 0.60) * fs
                    if tsp_anchor == 'middle':
                        x_start = tsp_x - w / 2
                        x_end = tsp_x + w / 2
                    elif tsp_anchor == 'end':
                        x_start = tsp_x - w
                        x_end = tsp_x
                    else:
                        x_start = tsp_x
                        x_end = tsp_x + w

                    top_y = curr_y - fs
                    bot_y = curr_y + 0.25 * fs
                    assert x_start >= bx + 16, f"Text '{t}' left padding {x_start - bx:.1f} < 16 in {gid}"
                    assert x_end <= bx + bw - 16, f"Text '{t}' right padding {bx + bw - x_end:.1f} < 16 in {gid}"
                    assert top_y >= by + 16, f"Text '{t}' top padding {top_y - by:.1f} < 16 in {gid}"
                    assert bot_y <= by + bh - 16, f"Text '{t}' bot padding {by + bh - bot_y:.1f} < 16 in {gid}"

    print("All text elements have >= 16px padding on all sides! (PASS)")
    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg("candidate_ci_hardening.svg")
