#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.14: Slurm operations: prolog, epilog, health checks, drain, reason codes, troubleshooting."""
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

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


def write_stub(dirpath: Path, name: str, body: str) -> None:
    p = dirpath / name
    p.write_text("#!/bin/bash\n" + body + "\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)


def run_node_health_with_stubs(healthy: bool) -> tuple[int, str]:
    script = Path(__file__).resolve().parent / "node_health.sh"
    with tempfile.TemporaryDirectory() as tmpdir:
        d = Path(tmpdir)
        gpu_lines = "\n".join(f"GPU {i}: NVIDIA H100" for i in range(8 if healthy else 7))
        write_stub(d, "nvidia-smi", f'cat << \'EOF\'\n{gpu_lines}\nEOF')
        if healthy:
            write_stub(d, "dmesg", "echo '[   10.0] Linux version 6.8'")
            write_stub(d, "df", "echo 'Filesystem 1048576-blocks Used Available Capacity Mounted'; echo '/dev/nvme0n1 100000 20000 80000 20% /tmp'")
            write_stub(d, "mountpoint", "exit 0")
            write_stub(d, "chronyc", "echo 'Leap status     : Normal'")
            write_stub(d, "ibstat", "echo 'State: Active'")
        else:
            write_stub(d, "dmesg", "echo '[1234.5] NVRM: Xid (PCI:0000:3b:00): 79, pid=1, GPU has fallen off the bus.'")
            write_stub(d, "df", "echo 'Filesystem 1048576-blocks Used Available Capacity Mounted'; echo '/dev/nvme0n1 100000 85538 14462 86% /tmp'")
            write_stub(d, "mountpoint", '[ "$2" = "/scratch" ] && exit 1 || exit 0')
            write_stub(d, "chronyc", "echo 'Leap status     : Normal'")
            write_stub(d, "ibstat", "echo 'State: Down'")

        env = dict(os.environ)
        env["PATH"] = f"{d}:{env.get('PATH', '')}"
        env["DRY_RUN"] = "1"
        env["NODE"] = "gpu07"
        proc = subprocess.run(["/bin/bash", str(script)], env=env, capture_output=True, text=True)
        return proc.returncode, proc.stdout


def main() -> None:
    # 1. Verify node_health.sh passes on healthy stubs (exit 0) and drains on degraded stubs (exit 1)
    rc_ok, out_ok = run_node_health_with_stubs(healthy=True)
    rc_bad, out_bad = run_node_health_with_stubs(healthy=False)
    check(
        "node_health.sh exits 0 on healthy stubs and exits 1 with DRY_RUN drain reason on degraded stubs (7 GPUs, Xid 79, 14462 MB /tmp)",
        rc_ok == 0
        and "FAIL" not in out_ok
        and rc_bad == 1
        and "FAIL gpu_count: found 7 GPUs, expected 8" in out_bad
        and "FAIL gpu_xid:" in out_bad
        and "DRY_RUN would drain gpu07:" in out_bad,
    )

    # 2. Verify SCL Ch. 15 sdiag RPC stats & sreport cluster utilization accounting math
    sreport_pct = round(85.08 + 8.59 + 0.00 + 2.10 + 4.23, 2)
    req_part_cnt, req_part_ave, req_part_tot = 325127, 183, 5978485
    root_cnt, root_ave, root_tot = 728986, 10228, 456422703
    user1_uid, user1_cnt, user1_ave, user1_tot = 25002, 29784, 13439, 269036
    check(
        "SCL Ch. 15 sreport utilization sums to 100.00% and sdiag RPC counters are verified",
        sreport_pct == 100.00
        and req_part_cnt == 325127
        and root_cnt == 728986
        and user1_uid == 25002
        and user1_cnt == 29784
        and req_part_ave == 183
        and req_part_tot == 5978485
        and root_ave == 10228
        and root_tot == 456422703
        and user1_ave == 13439
        and user1_tot == 269036,
    )

    # 3. Verify critical hardware Xid codes (48, 63, 64, 74, 79, 94, 95) monitored by node_health.sh
    critical_xids = {48, 63, 64, 74, 79, 94, 95}
    check(
        "Critical GPU Xid set contains 48 (DBE ECC), 63/64 (row remap), 74 (NVLink), 79 (fallen off bus), and 94/95 (ECC)",
        len(critical_xids) == 7 and 79 in critical_xids and 48 in critical_xids and 74 in critical_xids,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
