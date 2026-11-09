def correlate_traces(traces: list[dict]) -> list[dict]:
    """Identify the slow operations across the traces."""
    slow_ops = []
    for trace in traces:
        for span in trace["spans"]:
            duration_ms = span["duration_ms"]
            if duration_ms > 1000:  # > 1 second
                slow_ops.append({
                    "trace_id": trace["trace_id"],
                    "span_id": span["span_id"],
                    "name": span["name"],
                    "duration_ms": duration_ms,
                })
    return slow_ops
