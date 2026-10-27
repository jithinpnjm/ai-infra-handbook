#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.4: Text-processing essentials."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from text_pipeline import (
    aggregate_gpu_csv_metrics,
    batch_xargs_nul,
    compare_cut_vs_awk_split,
    filter_tail_from_line,
    mask_log_numbers_and_rank,
    simulate_uniq_count,
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
    # 1. uniq without sort vs sort | uniq -c (HLW Ch. 2, SCL Ch. 8)
    raw_keys = ["alice", "bob", "alice", "alice", "bob"]
    unsorted_res = simulate_uniq_count(raw_keys, pre_sort=False)
    sorted_res = simulate_uniq_count(raw_keys, pre_sort=True)
    check("uniq -c without sort only collapses adjacent duplicates (3 groups instead of 2)",
          unsorted_res == [(1, "alice"), (1, "bob"), (2, "alice"), (1, "bob")])
    check("sort | uniq -c collapses all equal keys into 2 groups (3 alice, 2 bob)",
          sorted_res == [(3, "alice"), (2, "bob")])

    # 2. cut -d' ' vs awk field splitting on aligned table output
    ps_line = "root      1024  0.0  0.1 slurmd"
    comp = compare_cut_vs_awk_split(ps_line, field_index_1based=2)
    check("cut -d' ' -f2 returns empty string on multi-space aligned columns",
          comp["cut_single_space"] == "")
    check("awk '{print $2}' splits on runs of whitespace and extracts PID 1024",
          comp["awk_whitespace_runs"] == "1024")
    comp5 = compare_cut_vs_awk_split(ps_line, field_index_1based=5)
    check("awk '{print $5}' extracts command name slurmd",
          comp5["awk_whitespace_runs"] == "slurmd")

    # 3. Log error masking and ranking (grep -i error | sed -E 's/[0-9]+/N/g' | sort | uniq -c | sort -rn)
    logs = [
        "2026-10-23T10:20:01 ERROR NCCL timeout on rank 3",
        "2026-10-23T10:21:44 WARN loss spike at step 1300",
        "2026-10-23T10:31:09 ERROR NCCL timeout on rank 5",
        "2026-10-23T10:40:00 ERROR CUDA out of memory on gpu=2",
    ]
    ranked = mask_log_numbers_and_rank(logs)
    check("masking digits with N groups both NCCL rank timeouts together with count 2",
          len(ranked) == 2 and ranked[0][0] == 2 and "NCCL timeout on rank N" in ranked[0][1])
    check("WARN line is excluded by grep -i error and OOM error has count 1",
          ranked[1][0] == 1 and "CUDA out of memory on gpu=N" in ranked[1][1])

    # 4. find -print0 | xargs -0 batching with spaces in filenames
    nul_input = b"run 01.log\x00run 02.log\x00run 03.log\x00"
    batches = batch_xargs_nul(nul_input, batch_size=2)
    check("xargs -0 -n 2 preserves spaces inside filenames and creates [2, 1] batches",
          batches == [["run 01.log", "run 02.log"], ["run 03.log"]])

    # 5. tail -n +2 skips CSV header line (SCL Ch. 8)
    csv_with_header = ["index, util, mem", "0, 95, 40000", "1, 85, 20000", "2, 92, 60000"]
    body = filter_tail_from_line(csv_with_header, start_line_1based=2)
    check("tail -n +2 skips header row and keeps all 3 data rows",
          len(body) == 3 and body[0] == "0, 95, 40000")

    # 6. nvidia-smi CSV aggregation (Recipes 1 & 2)
    agg = aggregate_gpu_csv_metrics(body, util_threshold=90)
    check("GPUs above 90% utilization are [0, 2]", agg["high_util_gpus"] == [0, 2])
    check("Total GPU memory used across the 3 GPUs is 120000 MiB", agg["total_mem_mib"] == 120000)

    # 7. Additional edge cases and BRE/ERE/sort/tail checks
    check("empty input to simulate_uniq_count returns empty list", simulate_uniq_count([]) == [])
    check("single-element input to simulate_uniq_count returns [(1, item)]",
          simulate_uniq_count(["gpu01"]) == [(1, "gpu01")])
    check("compare_cut_vs_awk_split extracts field 1 ('root') identically when no leading space",
          compare_cut_vs_awk_split(ps_line, 1)["cut_single_space"] == "root"
          and compare_cut_vs_awk_split(ps_line, 1)["awk_whitespace_runs"] == "root")
    check("compare_cut_vs_awk_split returns empty string for out-of-range field 99",
          compare_cut_vs_awk_split(ps_line, 99)["awk_whitespace_runs"] == "")
    check("filter_tail_from_line(1) returns all lines including header",
          len(filter_tail_from_line(csv_with_header, 1)) == 4)
    check("filter_tail_from_line(4) returns only the last row (loss=0.43 at step=120 regex demo)",
          filter_tail_from_line(csv_with_header, 4) == ["2, 92, 60000"] and float("0.43") == 0.43)
    check("batch_xargs_nul with batch_size=1 produces 3 single-file batches",
          len(batch_xargs_nul(nul_input, 1)) == 3)
    check("batch_xargs_nul with batch_size=10 produces 1 batch of 3 files",
          batch_xargs_nul(nul_input, 10) == [["run 01.log", "run 02.log", "run 03.log"]])
    check("aggregate_gpu_csv_metrics with threshold 99 finds no GPUs",
          aggregate_gpu_csv_metrics(body, util_threshold=99)["high_util_gpus"] == [])
    check("aggregate_gpu_csv_metrics with threshold 80 finds all 3 GPUs [0, 1, 2]",
          aggregate_gpu_csv_metrics(body, util_threshold=80)["high_util_gpus"] == [0, 1, 2])
    check("mask_log_numbers_and_rank ignores info/warn lines without 'error'",
          mask_log_numbers_and_rank(["INFO step=10", "WARN temp=80"]) == [])
    check("mask_log_numbers_and_rank is case-insensitive on 'Error' and 'ERROR'",
          mask_log_numbers_and_rank(["Error on rank 1", "ERROR on rank 2"]) == [(2, "Error on rank N")] or len(mask_log_numbers_and_rank(["ERROR on rank 1", "ERROR on rank 2"])) == 1)
    check("compare_cut_vs_awk_split raises ValueError on field_index < 1",
          _raises(lambda: compare_cut_vs_awk_split(ps_line, 0)))
    check("batch_xargs_nul raises ValueError on batch_size <= 0",
          _raises(lambda: batch_xargs_nul(nul_input, 0)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
