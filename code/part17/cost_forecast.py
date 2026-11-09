def forecast_cost(workload_forecast: dict, gpu_price: float) -> float:
    """Forecast the monthly GPU cost based on the workload forecast."""
    total_cost = 0
    for workload, forecast in workload_forecast.items():
        total_cost += forecast["projected_gpus"] * gpu_price * 24 * 30
    return total_cost
