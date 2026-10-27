"""Chapter 3.10 model: NumPy array memory layout (dtype, shape, strides, C vs
Fortran contiguity, broadcasting), tabular memory optimization & row-major CSV
vs columnar Parquet read savings (Designing Machine Learning Systems Ch. 3),
and PyTorch training/inference memory & DataLoader throughput math (AI
Engineering Ch. 2 & 9).

Sources modeled:
- Chip Huyen, Designing Machine Learning Systems (designing-machine-learning-systems,
  DMLS), Chapter 3 ("Data Engineering Fundamentals"):
  * Row-major (CSV: contiguous rows) vs column-major (Parquet/Arrow: contiguous
    columns, predicate pushdown, column pruning) access patterns and pandas
    DataFrame vs Series layout.
  * Data leakage (time-travel look-ahead leakage when splitting randomly instead
    of by time window, scaling before splitting, and group duplication).
- Chip Huyen, AI Engineering (ai-engineering, AIE), Chapters 2, 7, 9:
  * Parameter memory by dtype (`float64` 8 B, `float32` 4 B, `float16`/`bfloat16`
    2 B, `int8` 1 B, `int4` 0.5 B) and mixed-precision Adam training state
    (`2 B` bf16 weights + `2-4 B` gradients + `12 B` fp32 master weights & first/
    second moments = `16-18 B/param`, so 7B model needs ~112 GB before activations).
  * Inference KV cache and prefill (compute-bound) vs decode (memory-bandwidth-bound).
"""
from typing import Dict, Sequence, Tuple


def compute_ndarray_strides(
    shape: Tuple[int, ...],
    itemsize: int = 4,
    order: str = "C",
) -> Tuple[int, ...]:
    """Compute byte strides for a C-contiguous (row-major) or F-contiguous
    (column-major) ndarray of given shape and itemsize.
    """
    if not shape:
        return ()
    strides = [0] * len(shape)
    if order == "C":
        step = itemsize
        for i in range(len(shape) - 1, -1, -1):
            strides[i] = step
            step *= shape[i]
    elif order == "F":
        step = itemsize
        for i in range(len(shape)):
            strides[i] = step
            step *= shape[i]
    else:
        raise ValueError(f"unsupported order {order!r}")
    return tuple(strides)


def broadcast_shapes(shape_a: Tuple[int, ...], shape_b: Tuple[int, ...]) -> Tuple[int, ...]:
    """Implement NumPy/PyTorch right-aligned broadcasting rule."""
    len_max = max(len(shape_a), len(shape_b))
    padded_a = (1,) * (len_max - len(shape_a)) + shape_a
    padded_b = (1,) * (len_max - len(shape_b)) + shape_b
    out = []
    for da, db in zip(padded_a, padded_b):
        if da == db:
            out.append(da)
        elif da == 1:
            out.append(db)
        elif db == 1:
            out.append(da)
        else:
            raise ValueError(f"operands could not be broadcast together with shapes {shape_a} {shape_b}")
    return tuple(out)


def compare_row_vs_columnar_io(
    num_rows: int,
    total_cols: int,
    selected_cols: int,
    bytes_per_cell: int = 8,
    compression_ratio: float = 4.0,
) -> Dict[str, float]:
    """DMLS Ch. 3: Compare bytes read from disk when selecting `selected_cols`
    out of `total_cols` in row-major CSV (must scan all columns) vs compressed
    columnar Parquet (reads only selected columns).
    """
    csv_bytes = float(num_rows * total_cols * bytes_per_cell)
    parquet_bytes = (num_rows * selected_cols * bytes_per_cell) / compression_ratio
    return {
        "csv_mb": round(csv_bytes / 1e6, 2),
        "parquet_mb": round(parquet_bytes / 1e6, 2),
        "speedup_factor": round(csv_bytes / parquet_bytes, 2),
    }


def estimate_adam_mixed_precision_memory_gb(
    params_billions: float,
    grad_bytes_per_param: int = 2,
) -> Dict[str, float]:
    """AIE Ch. 7 & Section 3.3: Estimate per-parameter static memory in GB (10^9 B)
    for mixed-precision AdamW training:
      - bf16 weights: 2 B/param
      - bf16 (or fp32) gradients: 2 B (or 4 B)/param
      - fp32 master weights (4 B) + fp32 m (4 B) + fp32 v (4 B): 12 B/param
      Total = 16 B/param (with bf16 grads) or 18 B/param (with fp32 grads).
    """
    weights_gb = params_billions * 2.0
    grads_gb = params_billions * float(grad_bytes_per_param)
    adam_fp32_state_gb = params_billions * 12.0
    total_gb = weights_gb + grads_gb + adam_fp32_state_gb
    return {
        "weights_gb": weights_gb,
        "grads_gb": grads_gb,
        "adam_fp32_state_gb": adam_fp32_state_gb,
        "total_static_gb": total_gb,
    }


def diagnose_dataloader_vs_gpu_bottleneck(
    sample_decode_ms: float,
    batch_size: int,
    num_workers: int,
    gpu_compute_ms: float,
) -> Dict[str, object]:
    """Section 3.5: Compute DataLoader batch preparation time vs GPU step time."""
    effective_workers = max(1, num_workers)
    data_batch_ms = (batch_size * sample_decode_ms) / effective_workers
    step_ms = max(data_batch_ms, gpu_compute_ms)
    gpu_util_pct = round(100.0 * (gpu_compute_ms / step_ms), 1)
    return {
        "data_batch_ms": round(data_batch_ms, 2),
        "gpu_compute_ms": round(gpu_compute_ms, 2),
        "step_ms": round(step_ms, 2),
        "gpu_util_pct": gpu_util_pct,
        "starved": data_batch_ms > gpu_compute_ms,
    }
