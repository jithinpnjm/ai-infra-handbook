#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

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
        "Which engine is reading the braces in front of you",
        "Tool",
        "Language",
        "Notes",
        "Ansible, Salt, Cookiecutter, dbt",
        "Jinja2",
        "{{ }}, {% %}, filters",
        "Helm",
        "Go text/template plus Sprig functions",
        '{{ .Values.image.tag | quote }}, {{- if .Values.gpu }}, {{ include "chart.fullname" . }}, toYaml | nindent 4; trim with {{- and -}}',
        "Terraform or OpenTofu",
        "HCL expressions and templatefile()",
        '"${var.name}", for expressions, %{ if } directives',
        "Kustomize",
        "no templating",
        "overlays and patches (JSON6902, strategic merge)",
        "GitHub Actions",
        "${{ expression }}",
        "different syntax and contexts",
        "Docker Compose",
        "${VAR:-default}",
        "shell-like",
        "cloud-init",
        "Jinja2 optional header ## template: jinja",
        "{{ v1.local_hostname }}",
        "Packer",
        "HCL2",
        "templatefile, locals",
        "Prometheus and Alertmanager",
        "Go templates",
        "{{ $labels.instance }}; conflicts with Jinja in Ansible-templated rule files: use raw",
        "separate data from templates; keep templates light on logic; prefer declarative overlays such as Kustomize or typed config; avoid templating a templating language, such as Helm values rendered by Jinja then rendered again by Terraform; keep logic in code or modules, not 200-line Jinja files; validate generated YAML with yamllint, kubeconform or kubectl --dry-run=server",
        "could a reviewer understand the change without running anything?",
        "The same double brace can mean three different things"
    ]

    found_texts = [t for t, fs in text_elements]

    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\nExtra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

    # 5. Check forbidden words
    forbidden = ["orange", "green", "grey", "monospace", "arrow"]
    for t, _ in text_elements:
        for f in forbidden:
            # check word boundary
            assert not re.search(r'\b' + re.escape(f) + r'\b', t, re.IGNORECASE), f"Forbidden word '{f}' found in text: '{t}'"

    print("\nForbidden words check: PASSED!")
    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg("planning/image_tools/candidate_engines.svg")
