# Rework ledger X5 (2026-11-12)

## 11.24 MIG in depth
Changed: invalid `4g.40gb` + 2x `2g.20gb` layout fixed (8 compute slices, H100 has 7); driver 575 pairing fixed to CUDA 12.9; drain loop replaced by a process check (`nvidia-smi --query-compute-apps`, `fuser`) with the reset and no-module-unload explanation; GKE MIG node-pool subsection; per-instance DCGM labels; H100/H200/B200 profile list and +me; ceremony (evidence package, "Silicon Tetris", "Senior Architect") removed; source leakage removed from prose; 20 checkpoint questions rewritten as scenarios; exercises 3 to 6 updated. Code and lab changed (`code/part11/mig_in_depth*.py`): 26 checks pass, check_code_files clean.
Verdicts: combo = fixed (NVIDIA MIG User Guide supported profiles). Driver 575 = CUDA 12.9 = fixed (CUDA release notes). Drain/rmmod = fixed. GKE flags and limits = from GKE docs, read today. `GPU_I_ID`/`GPU_I_PROFILE` label names = UNRESOLVED (fetched pages did not confirm; chapter says to check exporter version). Reset-needed-for-mode-change claim rests on nvidia-smi warning text; not re-read in the user guide.
Neighbours: Sources section still lists volume paths (kept by rule); lab output lines are code-generated.

## 11.9
Deleted RAG/vector-DB subsection; replaced with a short "when training is the right tool" subsection. Sources table row still mentions RAG (attribution, kept).

## 11.11
Deleted fio/mdtest section and its outcome bullet; added Network Operator upgrade (`upgradeCRDs` hook, helm steps) and NicClusterPolicy failure cases (name `nic-cluster-policy`, `status.appliedStates`). Source: Mellanox/network-operator READMEs, master, 2026-11-12. UNRESOLVED: what manual OFED steps are needed (vendor page does not list them; chapter says read release notes). Lab output still prints a fio check line (code-generated; code not changed). Failure-table cells still carry `volume-06` tags and the exercises/checkpoint were not rewritten: remaining leakage.

## 12.23
srun `-x` replaced by `--export=ALL,...`; TeX removed (formulas now plain text blocks); duplicated numbers removed; opening rewritten as prose with worked numbers after; ladder table shortened; DOM thresholds marked illustrative (per optic datasheet); `iommu=pt` mislabel fixed; Q10 and Q11 replaced by "which stage catches X" scenarios; V8/V9 tags removed from blocks. Not done: remaining long table cells in BOM tables, all-pairs perftest and SHARP A/B additions (no sourced material). Lab 26/26 pass.

## 12.17
Removed the TPS/RPS and NIXL paragraph and the inference-trap bullet in the intro; added links to 19.5 (lab) and 12.23 (acceptance policy). Inference latency subsections, exercise 6 and Q18/Q19 kept to preserve question counts: candidates to move to Part 15 later. `$...$` math in this chapter left as is.
