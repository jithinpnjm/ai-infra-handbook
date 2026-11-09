def forecast_workloads(workloads: dict, horizon_days: int = 90) -> dict:
    """workloads: {name: {"current_gpus": int, "growth_rate": float per 90 days}}. Compound growth over the horizon."""
    forecast = {}
    for name, w in workloads.items():
        projected = w["current_gpus"] * (1 + w["growth_rate"]) ** (horizon_days / 90)
        forecast[name] = {"current_gpus": w["current_gpus"], "projected_gpus": projected, "growth_rate": w["growth_rate"]}
    return forecast
