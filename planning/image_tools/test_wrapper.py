#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

labels = {
    "title": "CI hardening: least privilege, reproducibility, packaging and nightly runs",
    "p1_title": "Least privilege",
    "p1_body": "permissions: set to the minimum; pin third-party actions by SHA; never echo secrets; pull requests from forks are untrusted and get no secrets; pull_request_target only with great care",
    "p2_title": "Reproducible",
    "p2_body": "lock files, pinned base images, --require-hashes, hermetic builds, record tool versions in logs; cache dependencies and test data keyed on lock file hashes; minimum-dependency run: uv pip install --resolution lowest-direct validates lower bounds",
    "p3_title": "Packaging and release",
    "p3_body": "install the built wheel into a clean venv and run a smoke test: catches missing package data and wrong entry points; tag, changelog from conventional commits; version from the git tag with hatch-vcs or setuptools-scm; sign artefacts, provenance attestations, SBOM; protect the environment so publishing needs approval",
    "p4_title": "GPU and nightly",
    "p4_body1": "GPU tests on self-hosted runners labelled gpu, ephemeral or containerised jobs, limit who can trigger, clean state between jobs; NVIDIA publishes GPU-enabled container images and the container toolkit",
    "p4_body2": "nightly: full suite with random seeds, dependency audit, slow and integration tiers; notify on failure; track flakiness over time",
    "footer": "artefacts: coverage files, JUnit XML, failure logs; GitLab CI uses stages, needs, cache, artifacts:reports:junit, rules: and runner tags",
    "bottom": "Order the jobs cheap to expensive, and make the required checks branch-protected"
}

# In columns 1 & 2:
# panel x: 40 or 820. width: 740.
# Available width inside panel with 24px padding on each side: 740 - 48 = 692px.
# conservative width factor: 0.60 for sans, 0.62 for monospace.
# At 24px:
# 692 / 14.4 = 48.05 chars sans.
# 692 / 14.88 = 46.5 chars mono.

# In footer and bottom:
# box width: 1520. Available: 1520 - 48 = 1472px.
# 1472 / 14.4 = 102 chars.

# Let's propose wrapping for each body:

p1_lines = [
    "permissions: set to the minimum; ",
    "pin third-party actions by SHA; ",
    "never echo secrets; ",
    "pull requests from forks are untrusted ",
    "and get no secrets; ",
    "pull_request_target only with great care"
]

p2_lines = [
    "lock files, pinned base images, ",
    "--require-hashes, hermetic builds, ",
    "record tool versions in logs; ",
    "cache dependencies and test data ",
    "keyed on lock file hashes; ",
    "minimum-dependency run: ",
    "uv pip install --resolution lowest-direct ",
    "validates lower bounds"
]

p3_lines = [
    "install the built wheel into a clean venv ",
    "and run a smoke test: catches missing package ",
    "data and wrong entry points; ",
    "tag, changelog from conventional commits; ",
    "version from the git tag with hatch-vcs ",
    "or setuptools-scm; ",
    "sign artefacts, provenance attestations, SBOM; ",
    "protect the environment so publishing ",
    "needs approval"
]

p4_body1_lines = [
    "GPU tests on self-hosted runners labelled gpu, ",
    "ephemeral or containerised jobs, limit who can ",
    "trigger, clean state between jobs; ",
    "NVIDIA publishes GPU-enabled container ",
    "images and the container toolkit"
]

p4_body2_lines = [
    "nightly: full suite with random seeds, ",
    "dependency audit, slow and integration tiers; ",
    "notify on failure; track flakiness over time"
]

footer_lines = [
    "artefacts: coverage files, JUnit XML, failure logs; GitLab CI uses ",
    "stages, needs, cache, artifacts:reports:junit, rules: and runner tags"
]

bottom_lines = [
    "Order the jobs cheap to expensive, and make the required checks branch-protected"
]

print("=== Checking reconstructed text fidelity ===")
assert "".join(p1_lines).strip() == labels["p1_body"]
print("P1 body match: PASS")

assert "".join(p2_lines).strip() == labels["p2_body"]
print("P2 body match: PASS")

assert "".join(p3_lines).strip() == labels["p3_body"]
print("P3 body match: PASS")

assert "".join(p4_body1_lines).strip() == labels["p4_body1"]
print("P4 body1 match: PASS")

assert "".join(p4_body2_lines).strip() == labels["p4_body2"]
print("P4 body2 match: PASS")

assert "".join(footer_lines).strip() == labels["footer"]
print("Footer match: PASS")

assert "".join(bottom_lines).strip() == labels["bottom"]
print("Bottom match: PASS")

print("\n=== Checking line widths in 740px box (max allowed width = 740 - 32 = 708px) ===")
max_allowed_w = 708

for name, lines in [("P1", p1_lines), ("P2", p2_lines), ("P3", p3_lines), ("P4_1", p4_body1_lines), ("P4_2", p4_body2_lines)]:
    print(f"\n-- {name} ({len(lines)} lines) --")
    for l in lines:
        w_sans = len(l) * 0.60 * 24
        w_mono = len(l) * 0.62 * 24
        print(f"  [{len(l):2d} chars] w={w_mono:5.1f}px (mono) | w={w_sans:5.1f}px (sans) | '{l.strip()}'")
        assert w_mono < max_allowed_w, f"Line too long! {l}"

print("\nAll lines fit within 708px width limit!")
