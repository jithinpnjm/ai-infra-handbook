#!/bin/bash
# code/part19/c04_lab.sh
# Host-side lab steps for chapter 19.4. Run from the repository root. Needs python3 with pytest.
set -eu

# Step 1: unit tests for the manager, calculator, detector and Slurm script logic
python3 -m pytest code/part19/test_c04_checkpoint_manager.py code/part19/test_c04_checkpoint_interval.py \
    code/part19/test_c04_straggler_detector.py code/part19/test_c04_slurm_script.py -q

# Step 2: checkpoint interval for the reference job (32 GPUs, 112 GB checkpoint at 5 GB/s)
python3 code/part19/c04_checkpoint_interval.py --node-mtbf-hours 6334.6 --nodes 4 \
    --checkpoint-gb 112.4 --write-gb-per-s 5 --restart-seconds 600

# Step 3: straggler detector on the fixtures (exit code 1 means a finding)
for f in healthy slow_gpu slow_host spike global_slowdown; do
    python3 code/part19/c04_straggler_detector.py code/part19/c04_fixtures/$f.csv || true
done

# Step 4: validate the manifests against the upstream CRDs cloned into $CRD_DIR
python3 -I tools/check_crd_yaml.py "$CRD_DIR/jobset.x-k8s.io_jobsets.yaml" \
    "$CRD_DIR/pytorchjobs.yaml" -- code/part19/c04_jobset.yaml code/part19/c04_pytorchjob.yaml
