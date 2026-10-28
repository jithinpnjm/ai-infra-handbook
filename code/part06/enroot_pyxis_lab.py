#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.13: Containers on Slurm: enroot and pyxis."""
import sys

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


def format_enroot_pyxis_uris(registry: str, repo: str, tag: str) -> dict[str, str]:
    """Generate enroot import URI, sbatch escaped directive, and default squashfs filename."""
    enroot_uri = f"docker://{registry}#{repo}:{tag}"
    sbatch_directive = f"#SBATCH --container-image {registry}\\#{repo}:{tag}"
    sqsh_name = f"{repo.replace('/', '+')}+{tag}.sqsh"
    return {
        "enroot_uri": enroot_uri,
        "sbatch_directive": sbatch_directive,
        "sqsh_name": sqsh_name,
    }


def parse_pyxis_mounts(mount_spec: str) -> list[dict[str, str]]:
    """Parse --container-mounts=SRC:DST[:FLAGS][,...] into structured mount records."""
    records = []
    for entry in mount_spec.split(","):
        parts = entry.strip().split(":")
        src, dst = parts[0], parts[1]
        flags = parts[2] if len(parts) > 2 else "rw"
        records.append({"src": src, "dst": dst, "flags": flags})
    return records


def estimate_pull_time_sec(num_nodes: int, image_gb: float, uplink_gbps_bytes: float) -> float:
    """Estimate registry thundering-herd pull time when num_nodes pull image_gb concurrently over uplink_gbps_bytes."""
    return round((num_nodes * image_gb) / uplink_gbps_bytes, 1)


def main() -> None:
    # 1. Verify Enroot / Pyxis URI and .sqsh naming rules (nvcr.io#nvidia/pytorch:24.07-py3, pyxis commit 1075199)
    uris = format_enroot_pyxis_uris("nvcr.io", "nvidia/pytorch", "24.07-py3")
    check(
        "Enroot/Pyxis URI formatter generates docker://nvcr.io#..., escaped #SBATCH \\#, and nvidia+pytorch+24.07-py3.sqsh",
        uris["enroot_uri"] == "docker://nvcr.io#nvidia/pytorch:24.07-py3"
        and uris["sbatch_directive"] == "#SBATCH --container-image nvcr.io\\#nvidia/pytorch:24.07-py3"
        and uris["sqsh_name"] == "nvidia+pytorch+24.07-py3.sqsh",
    )

    # 2. Verify Pyxis --container-mounts parser with ro+rprivate and default rw flags
    mounts = parse_pyxis_mounts("/data:/data:ro+rprivate,/scratch/user:/scratch,/work:/workspace")
    check(
        "parse_pyxis_mounts parses SRC:DST:FLAGS (ro+rprivate and default rw)",
        len(mounts) == 3
        and mounts[0] == {"src": "/data", "dst": "/data", "flags": "ro+rprivate"}
        and mounts[1] == {"src": "/scratch/user", "dst": "/scratch", "flags": "rw"},
    )

    # 3. Verify registry thundering-herd pull calculation (64 nodes * 15 GB / 10 GB/s = 96.0 s vs 1.5 s single import)
    t_herd = estimate_pull_time_sec(num_nodes=64, image_gb=15.0, uplink_gbps_bytes=10.0)
    t_once = estimate_pull_time_sec(num_nodes=1, image_gb=15.0, uplink_gbps_bytes=10.0)
    check(
        "64-node concurrent 15 GB registry pull takes 96.0 s over 10 GB/s uplink vs 1.5 s single central squashfs import",
        t_herd == 96.0 and t_once == 1.5,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
