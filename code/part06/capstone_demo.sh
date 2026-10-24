#!/bin/bash
# Run the Part 6 toolchain end to end on the sample inputs. Needs python3; set PY to a python with
# prometheus-client and pyyaml for the exporter and alert checks (default: python3).
set -u
PY=${PY:-python3}
H=$(cd "$(dirname "$0")" && pwd)
IN=$H/capstone_inputs
OUT=${1:-$(mktemp -d)}
step() { echo; echo "=== $1"; }
step "1. provisioning: inventory -> dnsmasq + iPXE (6.22)"
$PY $H/gen_provision.py $IN/nodes.csv $OUT/prov
step "2. identity: users -> LDIF + Slurm accounts + homes (6.24)"
$PY $H/identity_gen.py $IN/users.csv $OUT/identity
step "3. scheduler: hardware -> slurm.conf, gres.conf, cgroup.conf (6.8, 6.10)"
$PY $H/gen_slurm_conf.py $IN/hardware.csv $OUT/slurm
step "4. lint slurm.conf (6.8)"
$PY $H/slurmconf_lint.py $OUT/slurm/slurm.conf
step "5. lint the training batch script (6.11)"
$PY $H/sbatch_lint.py $IN/train.sbatch
step "6. monitoring: exporter self-test (6.26)"
$PY $H/slurm_exporter.py --selftest | tail -1
step "7. alert rules check (6.26)"
$PY $H/check_alert_rules.py $H/alerts_gpu_cluster.yml
step "8. node health check, dry run with stub tools (6.14)"
echo "(see chapter 6.14 for the stubbed run; skipped here because it needs stub commands)"
step "9. checkpoint commit protocol self-test (6.21)"
$PY $H/ckpt_atomic.py | tail -2
step "10. facility arithmetic (6.30)"
$PY $H/facility_calc.py | sed -n 1,4p
echo; echo "outputs in $OUT"
