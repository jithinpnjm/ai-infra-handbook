#!/usr/bin/env bash
# code/part19/c12_lab.sh
# Lab for chapter 19.12. Run from the repository root. Needs python3, pytest, PyYAML and kubeconform.
# KEDA_CRD must point at config/crd/bases/keda.sh_scaledobjects.yaml in a clone of kedacore/keda.
set -euo pipefail
: "${KEDA_CRD:?set KEDA_CRD to keda.sh_scaledobjects.yaml from a shallow clone of kedacore/keda}"

python3 code/part19/c12_size_inference_pool.py
python3 code/part19/c12_design_canary.py
python3 code/part19/c12_design_review.py
python3 -m pytest code/part19 -q -k c12
kubeconform -strict -summary code/part19/c12_priority_classes.yaml
python3 -I tools/check_crd_yaml.py "$KEDA_CRD" -- \
  code/part19/c12_inference_scaling.yaml code/part19/c12_inference_scaling_batch.yaml
