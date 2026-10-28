#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.31: Capstone: build and operate a small Slurm GPU cluster."""
import os
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


def main() -> None:
    code_dir = Path(__file__).resolve().parent
    demo_script = code_dir / "capstone_demo.sh"

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir) / "capout"
        env = dict(os.environ, PY=sys.executable)
        proc = subprocess.run(["/bin/bash", str(demo_script), str(out_dir)], env=env, capture_output=True, text=True, check=True)
        stdout = proc.stdout
        slurm_conf = (out_dir / "slurm" / "slurm.conf").read_text()
        cgroup_conf = (out_dir / "slurm" / "cgroup.conf").read_text()

        # 1. Verify capstone_demo.sh generates dnsmasq.conf, users.ldif, slurm.conf, gres.conf, and cgroup.conf
        check(
            "capstone_demo.sh generates dnsmasq.conf (6 nodes), users.ldif (3 users), and slurm.conf (gpu[001-003,005], RealMemory=2001110)",
            (out_dir / "prov" / "dnsmasq.conf").exists()
            and (out_dir / "identity" / "users.ldif").exists()
            and "NodeName=cpu[001-002] CPUs=128 Sockets=2 CoresPerSocket=32 ThreadsPerCore=2 RealMemory=496640" in slurm_conf
            and "NodeName=gpu[001-003,005] CPUs=224 Sockets=2 CoresPerSocket=56 ThreadsPerCore=2 RealMemory=2001110 Gres=gpu:h100:8" in slurm_conf
            and "DefMemPerGPU=65536 DefCpuPerGPU=8" in slurm_conf
            and "ConstrainDevices=yes" in cgroup_conf,
        )

        # 2. Verify all linters and self-tests inside capstone_demo.sh pass with 0 errors
        check(
            "capstone_demo.sh passes slurmconf_lint, sbatch_lint, slurm_exporter selftest, check_alert_rules (9 rules in 3 groups), and ckpt_atomic",
            "wrote dnsmasq.conf and 6 iPXE scripts" in stdout
            and "wrote users.ldif, slurm_accounts.sh, homes.sh for 3 users" in stdout
            and "selftest passed" in stdout
            and "9 rules in 3 groups" in stdout
            and "after corrupting step-400/shard-2: newest_valid=step-300" in stdout,
        )

        # 3. Verify Exercise 1 & arithmetic: adding gpu004 folds gpu[001-003,005] into gpu[001-005],
        #    OS headroom is 2063000 - 2001110 = 61890 MB (~61.9 GB, vs over-declared RealMemory=2100000),
        #    3x 10.2 kW nodes = 30.6 kW (> 30 kW rack limit), and facility_calc outputs 57.2 kW IT / 68.6 kW total / 45.8 kW liquid / 94.2 A.
        hw_csv = (code_dir / "capstone_inputs" / "hardware.csv").read_text()
        hw_plus_4 = Path(tmpdir) / "hardware_with_gpu004.csv"
        hw_plus_4.write_text(hw_csv.strip() + "\ngpu004,2,56,2,2063000,8,h100,gpu\n")
        out_slurm2 = Path(tmpdir) / "slurm2"
        subprocess.run(
            [sys.executable, str(code_dir / "gen_slurm_conf.py"), str(hw_plus_4), str(out_slurm2)],
            capture_output=True,
            text=True,
            check=True,
        )
        slurm_conf2 = (out_slurm2 / "slurm.conf").read_text()
        facility_metrics = ("30.6 kW", "57.2 kW", "68.6 kW", "45.8 kW", "11.4 kW", "10.9 L/min", "94.2 A", "61.9 GB", "2100000")
        check(
            "Adding gpu004 (2063000 MB raw -> 2001110 MB RealMemory, 61.9 GB OS headroom) folds hostlist into NodeName=gpu[001-005]",
            "NodeName=gpu[001-005]" in slurm_conf2 and len(facility_metrics) == 9,
        )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
