#!/usr/bin/env bash
# Dataset versioning with DVC against a LOCAL remote (a directory), so no cloud account is needed.
# Run: DVC=/path/to/dvc bash c13_dvc_demo.sh   (default: `dvc` on PATH). Works in a throwaway temp dir.
set -euo pipefail
DVC="${DVC:-dvc}"
WORK="$(mktemp -d)"
cd "$WORK"
git init -q . && git config user.email lab@example.com && git config user.name lab
$DVC init -q
git commit -qm "init dvc"
mkdir -p data remote
printf 'id,label\n1,a\n2,b\n' > data/train.csv
$DVC add data/train.csv
$DVC remote add -d -q store "$WORK/remote"
git add data/.gitignore data/train.csv.dvc .dvc/config
git commit -qm "dataset v1"
git tag data-v1
$DVC push
printf '3,c\n' >> data/train.csv
$DVC add data/train.csv
git add data/train.csv.dvc && git commit -qm "dataset v2" && git tag data-v2
$DVC push
# Reproduce v1 from git + remote only: delete the local file and the cache, check out the tag, pull.
rm -rf data/train.csv .dvc/cache
git checkout -q data-v1
$DVC pull
echo "v1 rows: $(wc -l < data/train.csv)"
echo "v1 md5 in git: $(grep md5 data/train.csv.dvc | head -1)"
