#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.1: Containers from first principles: images, layers, registries."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from oci_image_layers import (
    check_cuda_driver_compatibility,
    simulate_dockerfile_cache_hits,
    simulate_oci_layer_sizes,
)

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


def main() -> None:
    # 1. Section 2 & KUR Ch. 2: Separate-layer `RUN rm` wastes 500 MB in image tarball vs same-layer cleanup
    bad_layers = [
        {"/app/bin": 50_000_000, "/var/cache/apt/pkg.deb": 500_000_000},
        {"/var/cache/apt/pkg.deb": -1},  # whiteout in Layer 2 hides file, but Layer 1 still ships 500 MB!
    ]
    good_layers = [
        {"/app/bin": 50_000_000},  # created and cleaned in the same RUN (or multi-stage)
    ]
    r_bad = simulate_oci_layer_sizes(bad_layers)
    r_good = simulate_oci_layer_sizes(good_layers)
    check(
        "Deleting a 500 MB cache file in a later layer hides it in visible_bytes (50 MB) but still ships 550 MB over the wire",
        r_bad["visible_bytes"] == 50_000_000
        and r_bad["total_image_bytes"] == 550_000_000
        and r_bad["wasted_whiteout_bytes"] == 500_000_000
        and r_good["total_image_bytes"] == 50_000_000,
    )

    # 2. Section 3 & KUR Ch. 2: Layer ordering and cache hits on a source-code edit
    # Good order: base -> COPY requirements.lock -> pip install -> COPY src/
    good_prev = [("FROM", "py312"), ("COPY_REQ", "lock_v1"), ("PIP_INSTALL", "wheels_v1"), ("COPY_SRC", "src_v1")]
    good_curr = [("FROM", "py312"), ("COPY_REQ", "lock_v1"), ("PIP_INSTALL", "wheels_v1"), ("COPY_SRC", "src_v2")]
    # Bad order: base -> COPY . . -> pip install
    bad_prev = [("FROM", "py312"), ("COPY_ALL", "all_v1"), ("PIP_INSTALL", "wheels_v1")]
    bad_curr = [("FROM", "py312"), ("COPY_ALL", "all_v2"), ("PIP_INSTALL", "wheels_v1")]
    check(
        "Ordering requirements.lock before src/ keeps PIP_INSTALL cached ([True, True, True, False]), whereas COPY . . first invalidates PIP_INSTALL",
        simulate_dockerfile_cache_hits(good_curr, good_prev) == [True, True, True, False]
        and simulate_dockerfile_cache_hits(bad_curr, bad_prev) == [True, False, False],
    )

    # 3. Section 6: Host NVIDIA driver vs container CUDA runtime compatibility
    ok_new_drv, _ = check_cuda_driver_compatibility(550, "12.4")
    fail_old_drv, msg = check_cuda_driver_compatibility(525, "12.4")
    ok_compat, _ = check_cuda_driver_compatibility(535, "12.6", has_cuda_compat_pkg=True)
    check(
        "Host driver 550 runs CUDA 12.4, driver 525 fails with 'CUDA driver version is insufficient', and cuda-compat bridges 535->12.6",
        ok_new_drv is True and fail_old_drv is False and "insufficient" in msg and ok_compat is True,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
