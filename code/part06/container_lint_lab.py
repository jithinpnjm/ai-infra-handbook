#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.29: Containers and reproducibility in HPC: Apptainer and enroot."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from container_lint import lint

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


GOOD_DEF = """Bootstrap: docker
From: nvcr.io/nvidia/pytorch@sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef

%labels
    Version 2026.10
    Maintainer hpc-team@example.org

%post
    curl -fsSL https://example.org/tool.tar.gz -o /tmp/tool.tar.gz
    echo "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  /tmp/tool.tar.gz" | sha256sum -c -
    pip install --no-cache-dir -r /opt/requirements.lock

%test
    python -c "import torch; print(torch.__version__)"
"""

BAD_DEF = """Bootstrap: docker
From: ubuntu:latest

%post
    apt-get update
    apt-get -y upgrade
    apt-get install -y python3-pip git gcc
    curl -sSL https://example.org/install.sh | sh
    wget https://example.org/model.bin
    git clone https://github.com/example/repo.git
    pip install torch
"""

GOOD_DOCKERFILE = """FROM nvcr.io/nvidia/pytorch@sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
LABEL maintainer="hpc-team@example.org" version="2026.10"
RUN pip install --no-cache-dir --require-hashes -r /opt/requirements.lock
"""


def main() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        good_def = Path(tmpdir) / "good.def"
        bad_def = Path(tmpdir) / "bad.def"
        good_df = Path(tmpdir) / "Dockerfile.good"
        good_def.write_text(GOOD_DEF)
        bad_def.write_text(BAD_DEF)
        good_df.write_text(GOOD_DOCKERFILE)

        # 1. Verify container_lint.py passes good.def (0 findings, sha256sum not misflagged as '| sh')
        res_good = lint(str(good_def))
        check(
            "container_lint.py passes digest-pinned good.def with 0 findings (and does not misflag '| sha256sum')",
            len(res_good) == 0,
            f"res_good={res_good}",
        )

        # 2. Verify container_lint.py catches 2 ERRORs and all warnings/infos in bad.def
        res_bad = lint(str(bad_def))
        errs_bad = [msg for sev, _, msg in res_bad if sev == "ERROR"]
        check(
            "container_lint.py catches 2 ERRORs (unpinned :latest and curl|sh) and 10 warnings/infos in bad.def",
            len(errs_bad) == 2 and len(res_bad) == 12,
            f"errs={len(errs_bad)}, total={len(res_bad)}",
        )

        # 3. Verify container_lint.py also validates digest-pinned Dockerfiles with 0 findings
        res_df = lint(str(good_df))
        check(
            "container_lint.py passes digest-pinned Dockerfile with LABEL and --require-hashes --no-cache-dir",
            len(res_df) == 0,
            f"res_df={res_df}",
        )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
