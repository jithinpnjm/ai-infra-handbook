"""Storage arithmetic for a training cluster: dataset reads and checkpoint writes.

Bytes per parameter in a checkpoint: Distributed AI Systems ch. 5 says Adam keeps two FP32
copies (8 bytes per parameter) and mixed precision keeps an FP32 master copy (4 more);
BF16 weights are 2. 2 + 4 + 8 = 14 is my sum of those statements.
Reference bandwidths: DGX GB300 SuperPOD reference architecture, Table 5, a different
SKU from the worked example, used only as an order of magnitude.
"""
GUIDELINE_GBS = {  # (level, "read"|"write") -> GB/s for one scalable unit
    ("standard", "read"): 90, ("standard", "write"): 45,
    ("enhanced", "read"): 280, ("enhanced", "write"): 140,
}


def dataset_read_gbs(tokens_per_s, bytes_per_token):
    if tokens_per_s <= 0 or bytes_per_token <= 0:
        raise ValueError("inputs must be positive")
    return tokens_per_s * bytes_per_token / 1e9


def multimodal_read_gbs(samples_per_s, bytes_per_sample):
    return dataset_read_gbs(samples_per_s, bytes_per_sample)


def checkpoint_bytes(params, bytes_per_param=14):
    return params * bytes_per_param


def checkpoint_write_s(params, write_gbs, bytes_per_param=14):
    if write_gbs <= 0:
        raise ValueError("write_gbs must be positive")
    return checkpoint_bytes(params, bytes_per_param) / (write_gbs * 1e9)


def stall_fraction(write_s, interval_s, async_snapshot_s=None):
    """Share of wall clock the GPUs wait. Synchronous: the whole write. Asynchronous:
    only the in-memory snapshot time."""
    if interval_s <= 0:
        raise ValueError("interval_s must be positive")
    return (write_s if async_snapshot_s is None else async_snapshot_s) / interval_s


def retained_tb(params, keep, bytes_per_param=14):
    return keep * checkpoint_bytes(params, bytes_per_param) / 1e12


def min_write_gbs(params, interval_s, budget, bytes_per_param=14):
    """Slowest write bandwidth that keeps a synchronous stall under budget."""
    if not 0 < budget < 1:
        raise ValueError("budget must be in (0, 1)")
    return checkpoint_bytes(params, bytes_per_param) / (budget * interval_s) / 1e9


def meets_guideline(read_gbs, write_gbs, level="standard", units=1):
    """Compare with the reference table scaled linearly by scalable units."""
    if level not in ("standard", "enhanced"):
        raise ValueError("level must be standard or enhanced")
    need_r = GUIDELINE_GBS[(level, "read")] * units
    need_w = GUIDELINE_GBS[(level, "write")] * units
    return read_gbs >= need_r and write_gbs >= need_w
