#!/usr/bin/env bash
# Chapter 19.8 local checks. Needs no GPU and no cluster.
# Run from the repository root. KUEUE_CRDS points at config/components/crd/bases of a Kueue v0.20.5 checkout.
# MIGPARTED_VALIDATOR is the binary built from c08_validate_mig_parted.go.txt inside a mig-parted v0.15.1 checkout.
set -euo pipefail

: "${KUEUE_CRDS:?set KUEUE_CRDS to the Kueue CRD directory}"
: "${MIGPARTED_VALIDATOR:?set MIGPARTED_VALIDATOR to the built validator}"

cd code/part19

# 1. Planner, cost calculator and file-consistency tests
C08_MIGPARTED_VALIDATOR="$MIGPARTED_VALIDATOR" python3 -m pytest test_c08_mig_planner.py test_c08_finops_and_configs.py -q

# 2. Print the planner and cost worked examples quoted in the chapter
python3 c08_mig_planner.py
python3 c08_finops.py

# 3. mig-parted config against the upstream parser
"$MIGPARTED_VALIDATOR" c08_mig_parted_config.yaml

# 4. Core Kubernetes objects against the Kubernetes schemas
kubeconform -strict -ignore-missing-schemas -summary \
  c08_namespaces_quota.yaml c08_mig_workload.yaml c08_mig_config_configmap.yaml

# 5. Kueue objects against the upstream CRDs
python3 -I ../../tools/check_crd_yaml.py \
  "$KUEUE_CRDS/kueue.x-k8s.io_clusterqueues.yaml" \
  "$KUEUE_CRDS/kueue.x-k8s.io_localqueues.yaml" \
  "$KUEUE_CRDS/kueue.x-k8s.io_resourceflavors.yaml" \
  -- c08_kueue_mig.yaml

# 6. Prometheus rules
promtool check rules c08_mig_rules.yml
