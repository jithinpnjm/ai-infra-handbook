#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

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

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels):
    print(f"{i+1:2d}: {l}")
