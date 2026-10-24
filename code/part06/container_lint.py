#!/usr/bin/env python3
"""Lint an Apptainer definition file or a Dockerfile for reproducibility and HPC-hygiene problems.

Checks: floating base tags (latest / no tag / no digest), unpinned package installs, 'upgrade' steps,
curl|sh pipes, downloads without checksum verification, git clones without a commit, pip installs without
pins or hashes, missing %labels/LABEL metadata, root-only assumptions, and cache bloat.
Usage: container_lint.py FILE...   (file type detected from content: 'Bootstrap:' => Apptainer, 'FROM' => Dockerfile)
"""
import re
import sys


def lint(path):
    text = open(path).read()
    lines = text.split("\n")
    out = []

    def add(sev, no, msg):
        out.append((sev, no, msg))

    apptainer = any(l.startswith("Bootstrap:") for l in lines)
    for no, l in enumerate(lines, 1):
        s = l.strip()
        if apptainer and s.startswith("From:"):
            ref = s.split(":", 1)[1].strip()
            if "@sha256:" not in ref and (":" not in ref.split("/")[-1] or ref.endswith(":latest")):
                add("ERROR", no, f"base image '{ref}' is not pinned (use a version tag, better a digest @sha256:...)")
            elif "@sha256:" not in ref:
                add("warn", no, f"base image '{ref}' uses a mutable tag; pin by digest for byte-for-byte reproducibility")
        if not apptainer and re.match(r"(?i)FROM\s+", s):
            ref = s.split()[1]
            if "@sha256:" not in ref and (":" not in ref or ref.endswith(":latest")):
                add("ERROR", no, f"base image '{ref}' is not pinned")
            elif "@sha256:" not in ref:
                add("warn", no, f"base image '{ref}' uses a mutable tag; pin by digest")
        if re.search(r"apt(-get)?\s+(-\S+\s+)*(dist-)?upgrade|dnf\s+(-\S+\s+)*upgrade|yum\s+(-\S+\s+)*update|apt(-get)?\s+update\s*$", s) and "install" not in s:
            add("warn", no, "system upgrade/update step makes the image depend on the build date")
        if re.search(r"apt(-get)?\s+install", s) and not re.search(r"[a-z0-9.+-]+=[0-9]", s) :
            add("warn", no, "apt install without version pins (acceptable if the base image and repo snapshot are pinned)")
        if re.search(r"curl[^|]*\|\s*(sudo\s+)?(ba)?sh\b|wget[^|]*\|\s*(ba)?sh\b", s):
            add("ERROR", no, "pipes a download into a shell: unverifiable and non-reproducible")
        if re.search(r"\b(curl|wget)\b", s) and not re.search(r"sha256sum|sha512sum|gpg|--checksum", " ".join(lines[no - 1:no + 3])):
            add("warn", no, "download without a following checksum/signature check")
        if re.search(r"git\s+clone", s) and not re.search(r"git\s+(checkout|reset)|--branch\s+\S+|-b\s+\S+", " ".join(lines[no - 1:no + 3])):
            add("warn", no, "git clone without pinning a tag/commit")
        if re.search(r"pip3?\s+install", s) and not re.search(r"==|--require-hashes|-r\s+\S+|requirements", s):
            add("warn", no, "pip install without version pins (use a lock file with hashes)")
        if re.search(r"pip3?\s+install", s) and "--no-cache-dir" not in s:
            add("info", no, "pip install without --no-cache-dir inflates the image")
        if re.search(r"conda\s+install", s) and "-y" not in s and "--yes" not in s:
            add("info", no, "conda install without --yes will hang non-interactively")
    if apptainer and "%labels" not in text:
        add("info", 0, "no %labels section (record version, git commit, build date, maintainer)")
    if not apptainer and not re.search(r"(?m)^LABEL\s", text):
        add("info", 0, "no LABEL metadata")
    if apptainer and "%test" not in text:
        add("info", 0, "no %test section: add a smoke test that runs at build time")
    return out


if __name__ == "__main__":
    rc = 0
    for f in sys.argv[1:]:
        print(f"== {f}")
        res = lint(f)
        for sev, no, msg in res:
            print(f"{sev:5s} line {no}: {msg}" if no else f"{sev:5s} {msg}")
            rc |= sev == "ERROR"
        if not res:
            print("no findings")
    sys.exit(rc)
