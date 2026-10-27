#!/usr/bin/env python3
"""Self-checking lab for Chapter 3.10: Python for data and ML infrastructure: NumPy, pandas, PyTorch essentials."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from python_data_ml_infra import (
    broadcast_shapes,
    compare_row_vs_columnar_io,
    compute_ndarray_strides,
    diagnose_dataloader_vs_gpu_bottleneck,
    estimate_adam_mixed_precision_memory_gb,
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
    # 1. Section 1: NumPy ndarray strides (3, 4) float32 -> (16, 4) C-order vs (4, 12) F-order/transpose
    c_strides = compute_ndarray_strides((3, 4), itemsize=4, order="C")
    f_strides = compute_ndarray_strides((3, 4), itemsize=4, order="F")
    bcast = broadcast_shapes((1000, 1), (1, 64))
    check(
        "ndarray (3, 4) float32 has C-strides (16, 4), F-strides (4, 12), and (1000, 1)+(1, 64) broadcasts to (1000, 64)",
        c_strides == (16, 4) and f_strides == (4, 12) and bcast == (1000, 64),
    )

    # 2. Section 2 & DMLS Ch. 3: Row-major CSV vs columnar Parquet reading 3 of 50 columns
    io_cmp = compare_row_vs_columnar_io(num_rows=1_000_000, total_cols=50, selected_cols=3, bytes_per_cell=8, compression_ratio=4.0)
    check(
        "reading 3 of 50 columns across 1M rows scans 400 MB in CSV vs 6 MB in 4x-compressed Parquet (66.67x less I/O)",
        io_cmp["csv_mb"] == 400.0 and io_cmp["parquet_mb"] == 6.0 and io_cmp["speedup_factor"] == 66.67,
    )

    # 3. Section 3.3 & AIE Ch. 7: 7B model mixed-precision Adam static memory (16 B/param = 112 GB > 80 GB GPU)
    mem7b = estimate_adam_mixed_precision_memory_gb(7.0, grad_bytes_per_param=2)
    check(
        "7B model in mixed-precision AdamW requires 14 GB weights + 14 GB grads + 84 GB FP32 Adam state = 112 GB",
        mem7b["weights_gb"] == 14.0
        and mem7b["grads_gb"] == 14.0
        and mem7b["adam_fp32_state_gb"] == 84.0
        and mem7b["total_static_gb"] == 112.0,
    )

    # 4. Section 3.5: DataLoader starvation diagnosis (20 ms decode, batch=64, 100 ms GPU step)
    w0 = diagnose_dataloader_vs_gpu_bottleneck(sample_decode_ms=20.0, batch_size=64, num_workers=0, gpu_compute_ms=100.0)
    w16 = diagnose_dataloader_vs_gpu_bottleneck(sample_decode_ms=20.0, batch_size=64, num_workers=16, gpu_compute_ms=100.0)
    check(
        "num_workers=0 starves GPU (1280 ms data vs 100 ms GPU -> 7.8% util), while num_workers=16 saturates GPU (80 ms data -> 100% util)",
        w0["starved"] is True
        and w0["gpu_util_pct"] == 7.8
        and w16["starved"] is False
        and w16["gpu_util_pct"] == 100.0,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
