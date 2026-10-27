"""Chapter 1.4 model: Unix text-processing pipelines (grep/ERE, cut vs awk
whitespace splitting, sort | uniq -c vs unsorted uniq, sed substitution,
and xargs -0 NUL-safe batching).

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 2
  (sections 2.5.1 grep and regular expressions, 2.5.2 less, 2.5.4 diff, 2.5.7
  head and tail, 2.5.8 sort).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 8 ("Tips
  for Some Often-Used Commands": less -F/-R/-S/-N/-n/-f, grep -E, sort -u,
  tail -n +N, diff -u).
"""
import re
from typing import Dict, List, Tuple


def simulate_uniq_count(lines: List[str], pre_sort: bool = False) -> List[Tuple[int, str]]:
    """Simulate 'uniq -c' (collapses ONLY adjacent identical lines) vs 'sort | uniq -c'."""
    seq = sorted(lines) if pre_sort else list(lines)
    if not seq:
        return []
    out: List[Tuple[int, str]] = []
    cur = seq[0]
    cnt = 1
    for item in seq[1:]:
        if item == cur:
            cnt += 1
        else:
            out.append((cnt, cur))
            cur = item
            cnt = 1
    out.append((cnt, cur))
    return out


def compare_cut_vs_awk_split(line: str, field_index_1based: int) -> Dict[str, str]:
    """Compare cut -d' ' (single space delimiter) against awk default (runs of whitespace)."""
    if field_index_1based < 1:
        raise ValueError("field_index_1based must be >= 1")
    cut_fields = line.split(" ")
    awk_fields = line.split()
    idx = field_index_1based - 1
    return {
        "cut_single_space": cut_fields[idx] if idx < len(cut_fields) else "",
        "awk_whitespace_runs": awk_fields[idx] if idx < len(awk_fields) else "",
    }


def mask_log_numbers_and_rank(log_lines: List[str]) -> List[Tuple[int, str]]:
    """Reproduce Recipe 7: grep -i error | sed -E 's/[0-9]+/N/g' | sort | uniq -c | sort -rn."""
    masked = [
        re.sub(r"[0-9]+", "N", line)
        for line in log_lines
        if "error" in line.lower()
    ]
    grouped = simulate_uniq_count(masked, pre_sort=True)
    return sorted(grouped, key=lambda x: (-x[0], x[1]))


def batch_xargs_nul(nul_stream: bytes, batch_size: int) -> List[List[str]]:
    """Simulate 'find ... -print0 | xargs -0 -n batch_size' preserving spaces in filenames."""
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    items = [x.decode("utf-8") for x in nul_stream.split(b"\x00") if x]
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


def filter_tail_from_line(lines: List[str], start_line_1based: int) -> List[str]:
    """Simulate 'tail -n +N' (prints from 1-based line N to the end, e.g., tail -n +2 skips header)."""
    if start_line_1based < 1:
        raise ValueError("start_line_1based must be >= 1")
    return lines[start_line_1based - 1 :]


def aggregate_gpu_csv_metrics(csv_lines: List[str], util_threshold: int = 90) -> Dict[str, object]:
    """Parse nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv,noheader,nounits."""
    high_util_gpus: List[int] = []
    total_mem_mib = 0
    for line in csv_lines:
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]
        gpu_idx, util, mem = int(parts[0]), int(parts[1]), int(parts[2])
        total_mem_mib += mem
        if util > util_threshold:
            high_util_gpus.append(gpu_idx)
    return {"high_util_gpus": high_util_gpus, "total_mem_mib": total_mem_mib}
