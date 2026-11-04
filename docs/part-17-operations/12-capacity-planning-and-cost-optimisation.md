---
id: "c17-12"
title: "17.12 Capacity planning and cost optimisation"
sidebar_label: "17.12 Capacity planning and cost"
sidebar_position: 12
description: "Capacity planning and cost optimisation for AI infrastructure: the forecasting model, the FinOps dashboard, the cost-vs-latency trade-off, the right-sizing exercise, the reserved-instance strategy, and the operational patterns that turn the GPU bill into a predictable operating expense."
status: "drafted"
tier: "2"
level: "A"
lab_venue: "GCP / GKE"
---

# 17.12 Capacity planning and cost optimisation

| Field | Value |
|---|---|
| Level | Advanced |
| Priority tier | 2 |
| Lab venue | GCP / GKE |
| Part | Part 17: Observability, performance and operations |
| Primary sources | NVIDIA Zero-to-Hero Volume 19 (`chapter-03-capacity-planning.md`, `chapter-06-cost-optimisation.md`); *AI Factory* (`ai-factory`, Chapter 8); NVIDIA Zero-to-Hero Volume 21 (AI factory overview); *Scalable Kubernetes Infrastructure for AI Platforms* (`scalable-kubernetes-infrastructure-for-ai-platforms`, Chapter 2); NVIDIA Zero-to-Hero Volume 8 (`chapter-02-cost-optimisation.md`) |
| Cross-references | Chapter 16.14 (Platform design: FinOps); Chapter 17.8 (Performance engineering); Chapter 17.11 (Incident response); Chapter 11 (GPU Kubernetes) |
| Coverage file | `planning/coverage/chapters/17-12.md` |
| Claim & number ledger | `planning/ledgers/17-12.md` |

## Capacity and cost at a glance

```mermaid
flowchart LR
    subgraph Forward["Forward-looking"]
        CP[Capacity planning<br/>forecast + buffer]
        RI[Reserved instances<br/>commitment]
    end

    subgraph Backward["Backward-looking"]
        FN[FinOps dashboard<br/>per-team cost]
        RS[Right-sizing<br/>exercises]
    end

    subgraph Output["Procurement"]
        ORD[Procurement order<br/>CFO signature]
    end

    CP --> ORD
    FN --> RS
    RI --> ORD
    RS --> ORD
```

The capacity planning and FinOps views meet in the procurement order.

## Why this matters for AI infrastructure

Every chapter in Part 17 so far has been about operating the cluster. This chapter is about the cost of the cluster. The cost is what the CFO sees; the cost is what the procurement team negotiates; the cost is what the platform team optimises. An AI factory without capacity planning is an AI factory that pays for GPUs it does not need. An AI factory with capacity planning is an AI factory that pays for the GPUs it needs and no more.

Capacity planning and cost optimisation are the same problem viewed from two sides. Capacity planning is the forward-looking view: how many GPUs will the team need in Q+1. Cost optimisation is the backward-looking view: how many GPUs did the team use in Q, and at what cost. The two views meet in the FinOps dashboard; the FinOps dashboard is the platform team's view of the cluster's economics.

```text
Why capacity planning and cost optimisation are on the critical path (V19 ch3, ch6; AF Ch 8; SKI Ch 2; V8 ch2):
- A typical mature AI platform spends millions of dollars per year on GPUs.
  A 10% capacity planning error is hundreds of thousands of dollars per year.
  The cost of being wrong is significant.
- A typical workload uses 60-80% of the GPU's compute capacity. A right-sizing
  exercise that closes the gap from 60% to 80% saves 25% of the GPU spend.
  The savings are millions of dollars per year.
- The FinOps dashboard is the source of truth for the cost. The dashboard
  shows the per-team, per-model, per-month cost. The dashboard drives the
  capacity planning and the cost optimisation.
```

Three operational realities make this chapter a platform-team concern rather than a data-science-only concern:

1. **The GPU bill is the platform team's responsibility.** The team that does not track the bill is the team that over-provisions. The platform team owns the FinOps dashboard; the platform team owns the capacity planning.
2. **The right-sizing is the platform team's discipline.** The team that does not right-size is the team that wastes GPUs. The platform team owns the right-sizing exercise; the platform team owns the cost optimisation.
3. **The reserved-instance strategy is the platform team's decision.** Reserved instances save 30-60% over on-demand; the platform team picks the commitment. The procurement team signs the contract; the platform team owns the trade-off.

**Before a team can run an AI workload on a GPU cluster, the team must have a capacity planning model and a FinOps dashboard. Capacity planning is the forward-looking view; FinOps is the backward-looking view. The two views meet in the procurement order; the procurement order is what the CFO signs.**

## Prerequisites and outcomes

### Prerequisites

- Chapter 16.14 (Platform design: FinOps) for the FinOps dashboard and the cost attribution model.
- Chapter 17.8 (Performance engineering methodology) for the cost-vs-latency trade-off.
- Chapter 17.11 (Incident response) for the change management context.
- Chapter 11 (GPU Kubernetes) for the GPU pool management.

### Outcomes

After completing this chapter you will be able to:

1. Build the capacity planning model: the forecasting model, the buffer calculation, the procurement order.
2. Build the FinOps dashboard: the per-team cost, the per-model cost, the cost-vs-latency trade-off.
3. Run the right-sizing exercise: identify over-provisioned workloads; reduce the GPU count; measure the savings.
4. Implement the reserved-instance strategy: the commitment level, the utilisation target, the renewal calendar.
5. Operate the capacity planning and cost optimisation process on GKE with reliable forecasts, transparent costs, and predictable procurement.

---

## 1. The capacity planning model

### 1.1 The forecasting model

The capacity planning model forecasts the team's GPU needs for the next quarter. The model is: historical usage + growth rate + buffer = forecast.

```text
Capacity planning model:
- Historical usage: avg GPU pool utilisation over the last 90 days = 80%
- Growth rate: GPU count growth over the last 90 days = 20% per quarter
- Buffer: 30% for spikes (cost of not having enough GPUs vs cost of over-provisioning)
- Forecast: current GPU count * (1 + growth rate) * (1 + buffer)
```

The pattern is: forecast the growth; add the buffer; order the GPUs. The model is simple; the model is defensible; the model is auditable.

### 1.2 The buffer calculation

The buffer is the safety margin between the forecast and the actual need. The buffer is the trade-off between over-provisioning (waste) and under-provisioning (SLO breach).

| Buffer | Trade-off |
|---|---|
| 10% | Low waste; high SLO breach risk |
| 20% | Moderate waste; moderate SLO breach risk |
| 30% | Balanced; the platform team's default |
| 50% | High waste; low SLO breach risk |
| 100% | Doubled GPU spend; no SLO breach risk |

The pattern is: 30% is the default; the buffer is tuned based on the workload's spike pattern; the buffer is reviewed quarterly.

### 1.3 The procurement order

The procurement order is the output of the capacity planning model. The order is the number of GPUs the team needs for the next quarter.

```bash
# Compute the Q+1 GPU order
python code/part17/capacity_plan.py \
  --current-gpu-count 100 \
  --growth-rate 0.20 \
  --buffer 0.30 \
  --output procurement_order.md
# expected: the Q+1 GPU order is 156 GPUs (rounded up)
```

The pattern is: the order is a script's output; the script is reviewed; the script's output is the CFO's signature.

---

## 2. The FinOps dashboard

### 2.1 The cost model

The cost model has three components: GPU compute, storage, and network.

```text
Cost model (V19 ch6; AF Ch 8):
- GPU compute: GPU-hours * GPU price per hour (varies by GPU class)
- Storage: GB-month * storage price per GB-month
- Network egress: GB * network egress price per GB
- Licensing (NVAIE): GPU-hours * license price per GPU-hour
```

The pattern is: the cost model is per-team, per-model, per-month; the cost model is the source of the FinOps dashboard.

### 2.2 The FinOps dashboard

The FinOps dashboard shows the cost per team, the cost per model, and the cost trend.

```yaml
# code/part17/finops_dashboard.json (shape only)
{
  "dashboard": {
    "title": "AI Factory - FinOps",
    "panels": [
      {"title": "Cost per team this month", "type": "bargauge", "targets": [{"expr": "sum by (team) (kubecost_team_cost_monthly)"}]},
      {"title": "Cost per model this month", "type": "bargauge", "targets": [{"expr": "sum by (model) (kubecost_model_cost_monthly)"}]},
      {"title": "GPU hours per team this month", "type": "stat", "targets": [{"expr": "sum by (team) (kubecost_team_gpu_hours_monthly)"}]},
      {"title": "Cost trend over the last 90 days", "type": "timeseries", "targets": [{"expr": "sum(kubecost_team_cost_daily)"}]},
      {"title": "Cost vs latency trade-off", "type": "table", "targets": [{"expr": "..."}]}
    ]
  }
}
```

The pattern is: the dashboard shows the cost per team; the dashboard shows the cost per model; the dashboard shows the trend; the dashboard shows the trade-off.

### 2.3 The chargeback integration

The chargeback integration feeds the business's billing system. The integration is a SQL query that aggregates the cost data by team; the query feeds the ERP.

```sql
-- code/part17/chargeback_query.sql (shape only)
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
```

The pattern is: the chargeback is automated; the chargeback feeds the ERP; the chargeback is auditable.

---

## 3. Right-sizing

### 3.1 The right-sizing exercise

The right-sizing exercise identifies over-provisioned workloads; the exercise reduces the GPU count; the exercise measures the savings.

```text
Right-sizing exercise:
- Workload A: 8 GPUs, 60% utilisation -> reduce to 5 GPUs (target 96% utilisation)
- Workload B: 16 GPUs, 80% utilisation -> no change
- Workload C: 4 GPUs, 40% utilisation -> reduce to 2 GPUs (target 80% utilisation)
- Savings: 8 - 5 + 4 - 2 = 5 GPUs * 24 hours * 30 days = 3600 GPU-hours
- Cost savings: 3600 * $3.20 = $11,520 per month
```

The pattern is: identify over-provisioned workloads; reduce the GPU count; measure the savings; track the savings on the FinOps dashboard.

### 3.2 The right-sizing metrics

The right-sizing metrics are the metrics that identify over-provisioned workloads.

| Metric | What it measures | Target |
|---|---|---|
| GPU utilisation per workload | The fraction of GPU in use | 80-95% |
| Memory utilisation per workload | The fraction of HBM in use | 80-95% |
| GPU hours per request | The GPU hours consumed per request | As low as possible |
| Cost per inference | The dollar cost per inference | As low as possible |

The pattern is: the metrics are tracked per workload; the metrics are reviewed quarterly; the right-sizing exercise identifies the workloads that are below the target.

### 3.3 The right-sizing recommendations

The right-sizing recommendations are the actions that reduce the GPU count.

```bash
# Generate the right-sizing recommendations
python code/part17/right_size.py \
  --cluster gke-prod-us-central1 \
  --output right_sizing_recommendations.md
# expected: a list of workloads with their GPU count, utilisation, and recommended GPU count
```

The pattern is: the recommendations are generated by a script; the recommendations are reviewed; the recommendations are applied; the savings are tracked.

---

## 4. Reserved instances

### 4.1 The reserved-instance strategy

The reserved-instance strategy commits to a certain number of GPUs for a certain period in exchange for a discount. The strategy is the trade-off between flexibility and cost.

| Commitment | Discount | Use case |
|---|---|---|
| On-demand | 0% | Spike capacity; unpredictable workloads |
| 1-year reserved | 30-40% | Steady-state workloads |
| 3-year reserved | 50-60% | Long-term workloads |
| Spot | 50-70% | Preemptible workloads; training jobs |

The pattern is: 1-year reserved for steady-state workloads; 3-year reserved for long-term workloads; spot for training jobs; on-demand for spikes.

### 4.2 The utilisation target

The utilisation target is the minimum utilisation that justifies the reserved-instance commitment.

```text
Reserved-instance utilisation target:
- 1-year reserved: minimum 80% utilisation
- 3-year reserved: minimum 70% utilisation
- Spot: minimum 0% utilisation (spot can be preempted at any time)
```

The pattern is: if the utilisation drops below the target, the reserved instance is wasted; the team should switch to on-demand or spot.

### 4.3 The renewal calendar

The renewal calendar is the schedule for renewing the reserved-instance commitments. The calendar is published quarterly; the calendar includes the commitment level, the expiry date, and the renewal decision.

```bash
# Schedule the renewal calendar
python code/part17/renewal_calendar.py \
  --cluster gke-prod-us-central1 \
  --output renewal_calendar.md
# expected: a calendar of upcoming renewals with the commitment level and the expiry date
```

The pattern is: the renewal calendar is published in advance; the renewal decision is made before the expiry date; the renewal decision is documented.

---

## 5. Operating capacity planning and cost optimisation on GKE

### 5.1 The components

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| Kubecost (or OpenCost) | Kubernetes Deployment | Prometheus + object storage | Cost aggregation latency p99 < 1 hour |
| Capacity planning dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |
| FinOps dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |
| Chargeback query | BigQuery | (BigQuery) | Query latency p99 < 30 s |

### 5.2 IAM and the cost optimisation

The cost optimisation stack has its own IAM. The pattern is:

| Role | Who | What they can do |
|---|---|---|
| `finops.reader` | Every team | Read the FinOps dashboard; query the cost data |
| `finops.writer` | The platform team | Update the cost model; update the FinOps dashboard |
| `finops.admin` | The CFO's office | Approve the procurement order; approve the chargeback |

The cost attribution is the platform team's discipline. Every GPU is tagged with the team, the model, and the cost centre; the tags feed the Kubecost allocation; the allocation feeds the FinOps dashboard.

### 5.3 Observability

| Metric | Why it matters | Alert |
|---|---|---|
| Cost per team per month | FinOps dashboard | > budget for 1 day |
| Cost per model per month | Model economics | > budget for 1 day |
| GPU utilisation per team | Capacity planning | < 30% for 7 days |
| Reserved-instance utilisation | Reserved-instance ROI | < target for 30 days |
| Right-sizing savings | Right-sizing effectiveness | < 10% per quarter |

The right-sizing savings alert is the most important. A low savings rate means the team is not optimising; a low savings rate means the GPU bill is growing without bound.

---

## 6. How it fails

Six failure modes recur.

### 6.1 "The forecast is wrong"

**Symptom:** The forecast says 156 GPUs; the actual usage is 100 GPUs; the team over-provisioned by 56 GPUs.

**Diagnosis:** The forecast model is wrong; the growth rate is wrong; the buffer is wrong; the historical data is wrong.

**Fix:** Tune the forecast model; review the historical data; add a confidence interval; review the forecast quarterly.

### 6.2 "The right-sizing exercise finds nothing"

**Symptom:** The right-sizing exercise is run quarterly; the exercise finds no over-provisioned workloads; the GPU bill grows without bound.

**Diagnosis:** The right-sizing metrics are wrong; the right-sizing exercise is too narrow; the team is not looking at all workloads.

**Fix:** Add the right-sizing metrics; expand the right-sizing exercise to all workloads; train the team on the right-sizing methodology.

### 6.3 "The reserved-instance commitment is wasted"

**Symptom:** The reserved-instance commitment is 80% utilised; the cost is higher than on-demand; the team is overpaying.

**Diagnosis:** The forecast was too optimistic; the workload's spike pattern does not match the commitment; the team did not adjust the commitment.

**Fix:** Adjust the commitment level; switch to on-demand or spot; sell the reserved-instance commitment if possible.

### 6.4 "The chargeback is wrong"

**Symptom:** The chargeback shows team A owes more than team B; the teams dispute the chargeback; the CFO escalates.

**Diagnosis:** The cost attribution is wrong; the cost model is wrong; the chargeback query is wrong.

**Fix:** Verify the cost attribution; verify the cost model; verify the chargeback query; automate the chargeback audit.

### 6.5 "The GPU bill grows without bound"

**Symptom:** The GPU bill grows 20% per quarter; the forecast is not updated; the procurement is not capped.

**Diagnosis:** The forecast is not updated; the procurement is not capped; the right-sizing is not run.

**Fix:** Update the forecast quarterly; cap the procurement; run the right-sizing exercise quarterly.

### 6.6 "The cost optimisation is ad-hoc"

**Symptom:** The team optimises costs ad-hoc; the team does not follow the right-sizing methodology; the team does not use the FinOps dashboard.

**Diagnosis:** The cost optimisation process is documented but not enforced; the team is not trained on the process.

**Fix:** Train the team on the cost optimisation process; enforce the process in code review; add the process to the team's quarterly OKRs.

---

## 7. Hands-on lab

This lab walks through the capacity planning model, the FinOps dashboard, the right-sizing exercise, and the reserved-instance strategy. The lab is **untested** in this repository.

### 7.1 Prerequisites

- Kubecost (or OpenCost) installed.
- The observability stack from earlier chapters.
- A GKE Autopilot or Standard cluster with at least 4 H100 GPUs.

### 7.2 Step 1: deploy Kubecost

```bash
helm repo add kubecost https://kubecost.github.io/cost-analyzer
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost --create-namespace \
  --set kubecostToken=$KUBECOST_TOKEN
# expected: Kubecost pods are running; Kubecost is scraping the cluster
```

### 7.3 Step 2: build the FinOps dashboard

```bash
kubectl -n monitoring create configmap finops-dashboard \
  --from-file=dashboards/finops.json

curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @dashboards/finops_import.json
# expected: the FinOps dashboard is available at /d/finops/ai-factory-finops
```

### 7.4 Step 3: run the capacity planning model

```bash
python code/part17/capacity_plan.py \
  --current-gpu-count 4 \
  --growth-rate 0.20 \
  --buffer 0.30 \
  --output procurement_order.md
# expected: the Q+1 GPU order is 6 GPUs (rounded up)
```

### 7.5 Step 4: run the right-sizing exercise

```bash
python code/part17/right_size.py \
  --cluster gke-prod-us-central1 \
  --output right_sizing_recommendations.md
# expected: a list of workloads with their GPU count, utilisation, and recommended GPU count
```

### 7.6 Step 5: query the chargeback

```bash
bq query --use_legacy_sql=false \
  "SELECT team, month, total_cost
   FROM \`${PROJECT_ID}.finops.chargeback\`
   ORDER BY month DESC LIMIT 12"
# expected: the per-team, per-month chargeback
```

### 7.7 What to record

After the lab, you should be able to answer five questions in five seconds each:

1. What is the current cost per team this month?
2. What is the Q+1 GPU order per the capacity planning model?
3. What is the current right-sizing savings rate?
4. What is the current reserved-instance utilisation?
5. What is the next reserved-instance renewal date?

If any takes more than 30 seconds, the capacity planning and cost optimisation stack is not yet a production service. The lab is **untested** against a live GKE cluster.

---

## Exercises

1. **Add a per-model cost dashboard.** Build a Grafana dashboard that shows the cost per model; the dashboard is the model's economics view. *Solution sketch:* a Grafana dashboard with the model's cost, the model's GPU hours, the model's inference count; the dashboard feeds the model's FinOps.
2. **Add a right-sizing recommendation script.** Build a script that takes the current GPU usage and recommends the right-sized GPU count. *Solution sketch:* a Python script that reads the metrics; computes the right-sized count; outputs the recommendation.
3. **Add a reserved-instance tracking dashboard.** Build a Grafana dashboard that shows the reserved-instance utilisation; the dashboard is the reserved-instance ROI view. *Solution sketch:* a Grafana dashboard with the reserved-instance utilisation; the dashboard feeds the cost optimisation.
4. **Add a FinOps alert per team.** Configure an alert that fires when a team's monthly cost exceeds its budget. *Solution sketch:* a Prometheus alert on the per-team cost; the alert pages the team's lead.
5. **Add a capacity planning review process.** Schedule a quarterly capacity planning review; the review produces a procurement order; the procurement order is reviewed by the CFO. *Solution sketch:* a calendar event; the review script; the procurement order.
6. **Add a chargeback audit.** Run a monthly chargeback audit; the audit verifies the per-team cost; the audit flags anomalies. *Solution sketch:* a Python script that reads the chargeback; the script verifies the per-team cost; the script flags anomalies.

---

## Checkpoint questions

<details><summary>1. What is the capacity planning model?</summary>
A model that forecasts the team's GPU needs for the next quarter. The model is: historical usage + growth rate + buffer = forecast. The model is simple; the model is defensible; the model is auditable. The default buffer is 30%; the buffer is tuned based on the workload's spike pattern.
</details>

<details><summary>2. What is the FinOps dashboard?</summary>
A Grafana dashboard that shows the per-team, per-model, per-month cost. The dashboard is the platform team's view of the cluster's economics. The dashboard feeds the chargeback; the dashboard drives the capacity planning and the cost optimisation.
</details>

<details><summary>3. What is the right-sizing exercise?</summary>
An exercise that identifies over-provisioned workloads; the exercise reduces the GPU count; the exercise measures the savings. The pattern is: identify over-provisioned workloads; reduce the GPU count; measure the savings; track the savings on the FinOps dashboard.
</details>

<details><summary>4. What is the reserved-instance strategy?</summary>
The strategy that commits to a certain number of GPUs for a certain period in exchange for a discount. 1-year reserved saves 30-40%; 3-year reserved saves 50-60%; spot saves 50-70%. The pattern is: 1-year reserved for steady-state workloads; 3-year reserved for long-term workloads; spot for training jobs; on-demand for spikes.
</details>

<details><summary>5. What is the most common capacity planning failure?</summary>
The forecast is wrong. The forecast says 156 GPUs; the actual usage is 100 GPUs; the team over-provisioned by 56 GPUs. The diagnosis is that the forecast model is wrong; the growth rate is wrong; the buffer is wrong. The fix is to tune the forecast model; review the historical data; add a confidence interval.
</details>

<details><summary>6. What is the most common right-sizing failure?</summary>
The right-sizing exercise finds nothing. The exercise is run quarterly; the exercise finds no over-provisioned workloads; the GPU bill grows without bound. The diagnosis is that the right-sizing metrics are wrong; the right-sizing exercise is too narrow. The fix is to add the right-sizing metrics; expand the exercise to all workloads.
</details>

<details><summary>7. What is the most common reserved-instance failure?</summary>
The reserved-instance commitment is wasted. The commitment is 80% utilised; the cost is higher than on-demand; the team is overpaying. The diagnosis is that the forecast was too optimistic; the workload's spike pattern does not match the commitment. The fix is to adjust the commitment level; switch to on-demand or spot.
</details>

<details><summary>8. What is the most common chargeback failure?</summary>
The chargeback is wrong. The chargeback shows team A owes more than team B; the teams dispute the chargeback; the CFO escalates. The diagnosis is that the cost attribution is wrong; the cost model is wrong; the chargeback query is wrong. The fix is to verify the cost attribution; verify the cost model; automate the chargeback audit.
</details>

<details><summary>9. What is the most common GPU bill growth failure?</summary>
The GPU bill grows without bound. The bill grows 20% per quarter; the forecast is not updated; the procurement is not capped. The diagnosis is that the forecast is not updated; the procurement is not capped; the right-sizing is not run. The fix is to update the forecast quarterly; cap the procurement; run the right-sizing exercise.
</details>

<details><summary>10. What is the most common cost optimisation failure?</summary>
The cost optimisation is ad-hoc. The team optimises costs ad-hoc; the team does not follow the right-sizing methodology; the team does not use the FinOps dashboard. The diagnosis is that the cost optimisation process is documented but not enforced. The fix is to train the team on the process; enforce the process in code review.
</details>

<details><summary>11. What is the difference between the capacity planning model and the FinOps dashboard?</summary>
The capacity planning model is the forward-looking view: how many GPUs will the team need in Q+1. The FinOps dashboard is the backward-looking view: how many GPUs did the team use in Q, and at what cost. The capacity planning model is the forecast; the FinOps dashboard is the actual.
</details>

<details><summary>12. What is the difference between the right-sizing exercise and the cost optimisation?</summary>
The right-sizing exercise is the specific activity of identifying over-provisioned workloads and reducing the GPU count. The cost optimisation is the broader discipline of reducing the cluster's overall cost. The right-sizing is one tool in the cost optimisation toolbox.
</details>

<details><summary>13. What is the difference between reserved-instance and spot-instance?</summary>
Reserved-instance is a commitment to a certain number of GPUs for a certain period in exchange for a discount. Spot-instance is a preemptible instance that can be taken away at any time; spot is cheaper but less reliable. The pattern is: reserved for steady-state workloads; spot for training jobs.
</details>

<details><summary>14. What is the difference between the capacity planning buffer and the error budget?</summary>
The capacity planning buffer is the safety margin for the GPU count; the buffer is the trade-off between over-provisioning and under-provisioning. The error budget is the safety margin for the SLO; the budget is the trade-off between reliability and velocity. The capacity planning buffer is for the cluster; the error budget is for the service.
</details>

<details><summary>15. What is the relationship between the FinOps dashboard and the chargeback?</summary>
The FinOps dashboard is the source of truth for the cost; the dashboard shows the per-team, per-model, per-month cost. The chargeback is the integration that feeds the business's billing system; the chargeback aggregates the cost data by team. The FinOps dashboard is the source; the chargeback is the consumer.
</details>

<details><summary>16. What is the difference between on-demand and reserved-instance cost?</summary>
On-demand is the pay-as-you-go price; the price is the highest. Reserved-instance is the discounted price; the discount is 30-60% depending on the commitment. The reserved-instance commitment is for a certain number of GPUs for a certain period; the on-demand is for spikes.
</details>

<details><summary>17. What is the most important cost metric?</summary>
Cost per team per month. The metric is the per-team cost; the metric feeds the chargeback; the metric drives the budget alerts. The team that tracks the metric can optimise; the team that does not track the metric cannot optimise.
</details>

<details><summary>18. What is the difference between the FinOps dashboard and the cost-vs-latency trade-off?</summary>
The FinOps dashboard is the backward-looking view: how much the team spent in Q. The cost-vs-latency trade-off is the forward-looking view: how much the team should spend in Q+1 to meet the SLO. The FinOps dashboard is the actual; the cost-vs-latency trade-off is the forecast.
</details>

<details><summary>19. Why is capacity planning a Tier 2 chapter?</summary>
Because the capacity planning process is what keeps the GPU bill predictable. The process is what the platform team owns; the process is what the CFO sees; the process is what the procurement team negotiates. A team that does not have the capacity planning process is a team that overpays for GPUs.
</details>

<details><summary>20. What five questions should the capacity planning lab let you answer in five seconds each?</summary>
What is the current cost per team this month. What is the Q+1 GPU order per the capacity planning model. What is the current right-sizing savings rate. What is the current reserved-instance utilisation. What is the next reserved-instance renewal date. If any takes more than 30 seconds, the capacity planning and cost optimisation stack is not yet a production service.
</details>

---

## Sources and review notes

- NVIDIA Zero-to-Hero Volume 19 (`chapter-03-capacity-planning.md`, `chapter-06-cost-optimisation.md`). Source for the capacity planning model, the FinOps dashboard, and the cost optimisation patterns. The wording has been rewritten in the handbook's voice.
- *AI Factory* (`ai-factory`, Chapter 8). Source for the AI factory lifecycle and the cost economics.
- NVIDIA Zero-to-Hero Volume 21 (AI factory overview). Source for the multi-tenant AI factory economics.
- *Scalable Kubernetes Infrastructure for AI Platforms* (`scalable-kubernetes-infrastructure-for-ai-platforms`, Chapter 2). Source for the Kubernetes cost optimisation patterns.
- NVIDIA Zero-to-Hero Volume 8 (`chapter-02-cost-optimisation.md`). Source for the GPU-specific cost optimisation patterns.

### Cross-references to other handbook chapters

- Chapter 16.14 for the platform design FinOps patterns.
- Chapter 17.8 for the performance engineering methodology.
- Chapter 17.11 for the incident response and change management.
- Chapter 11 for the GPU Kubernetes.

### Migrated from `nvidia-devops`

The capacity planning and cost optimisation patterns draw on Volume 19 chapters 3 and 6, Volume 8 chapter 2, and Volume 21. The wording has been rewritten in the handbook's voice.

### Explicitly labelled inferences

- The buffer calculation (30% default) is a starting point; specific buffers depend on the workload's spike pattern.
- The right-sizing savings targets (10% per quarter) are starting points; specific targets depend on the workload.
- The reserved-instance commitment ratios (1-year: 30-40%; 3-year: 50-60%) are approximate; specific discounts depend on the cloud provider.

### Not verified on live hardware

- The lab in Section 7 is **untested** against a live GKE cluster in this repository.
- The Kubecost version assumed in the lab should be pinned against the current releases before production use.
- The cost numbers in the lab are illustrative; production costs vary by usage pattern, region, and commitment.
