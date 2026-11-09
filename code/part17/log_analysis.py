def analyze_logs(logs: list[str]) -> dict:
    """Identify error patterns in the logs."""
    patterns = {
        "errors": [],
        "warnings": [],
        "exceptions": [],
    }
    for log in logs:
        if "ERROR" in log:
            patterns["errors"].append(log)
        if "WARN" in log and "ERROR" not in log:
            patterns["warnings"].append(log)
        if "Traceback" in log:
            patterns["exceptions"].append(log)
    return patterns
