SELECT
    team,
    DATE_TRUNC('month', timestamp) AS month,
    SUM(gpu_hours * gpu_price) AS compute_cost,
    SUM(storage_gb_month * storage_price) AS storage_cost,
    SUM(network_egress_gb * network_price) AS network_cost,
    SUM(license_hours * license_price) AS license_cost,
    SUM(compute_cost + storage_cost + network_cost + license_cost) AS total_cost
FROM cost_metrics
GROUP BY team, month
