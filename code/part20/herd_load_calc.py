# code/part20/herd_load_calc.py
"""Weight-load time when many replicas pull from one shared source.
Model size = parameters x bytes per parameter (Hands-On LLM Serving, chapter 5).
Source bandwidth range 0.5 to 14 GB/s is the book's SSD row of Table 5-5."""


def weights_gb(params_billion: float, bytes_per_param: float) -> float:
    return params_billion * bytes_per_param


def load_seconds(params_billion, bytes_per_param, replicas, source_gb_per_s):
    """All replicas start together and share the source bandwidth equally."""
    if replicas < 1 or source_gb_per_s <= 0:
        raise ValueError("replicas and bandwidth must be positive")
    return weights_gb(params_billion, bytes_per_param) * replicas / source_gb_per_s


if __name__ == "__main__":
    for n in (1, 2, 8, 32):
        t = load_seconds(70, 2, n, 14)
        print(f"{n:>2} replicas of a 70B FP16 model from a 14 GB/s source: {t:7.0f} s")
