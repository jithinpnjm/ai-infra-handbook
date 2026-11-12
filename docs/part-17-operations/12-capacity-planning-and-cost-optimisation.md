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

Read the diagram as two views that meet at the procurement order. The capacity plan and the reserved-instance commitments look forward. The FinOps dashboard and right-sizing look back at what you already spent, and right-sizing feeds the order too.

## Why this matters for AI infrastructure

Picture a platform team that has just bought a rack of GPUs. A few months later, finance asks why the GPU bill keeps rising, and nobody can explain it. Part 17 so far has taught you to keep the cluster running. This chapter teaches you to pay for it on purpose.

Capacity planning and cost optimisation are two views of one problem. Capacity planning looks forward and asks how many GPUs the team will need next quarter. Cost optimisation looks back and asks how many GPUs the team used, and what they cost. Both views meet in the FinOps dashboard, which is the platform team's picture of the cluster's economics.

The block below shows the stakes with example values. Replace them with your own figures before you put any of them in a budget.

```text
Why capacity planning and cost optimisation are on the critical path (background reading: NVIDIA Zero-to-Hero volume 19; AI Factory; Scalable Kubernetes Infrastructure for AI Platforms; NVIDIA Zero-to-Hero volume 8; the figures below are examples, not quotations):
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

Production-scale teams also measure goodput, which is useful work completed per unit of time, rather than raw busy time. AI Systems Performance Engineering, chapter 1, uses Meta's "Revisiting Reliability" paper as its case. A cluster that looked fully utilised still lost 70 to 75 percent of its compute to communication delays, slow data supply, and failure recovery.

Three habits make this a platform-team job rather than a data-science job.

1. The platform team owns the GPU bill. A team that cannot see its own cost has little reason to give GPUs back.
2. Right-sizing is a platform discipline too. Without it, a workload keeps the GPUs it was given long after it needs them.
3. Reserved commitments are a platform decision. The procurement team signs the contract, but the platform team owns the trade-off between flexibility and discount.

**Before a team runs its first workload, make sure it has both a capacity model and a FinOps dashboard.** Capacity planning tells you what to order, and FinOps tells you what you actually spent. The procurement order is where the two meet.

## Prerequisites and outcomes

### Prerequisites

Before you start, review the chapters below. Chapter 16.14 gives you the cost attribution model that this chapter reuses.

- Chapter 16.14 (Platform design: FinOps) for the FinOps dashboard and the cost attribution model.
- Chapter 17.8 (Performance engineering methodology) for the cost-versus-latency trade-off.
- Chapter 17.11 (Incident response) for the change management context.
- Chapter 11 (GPU Kubernetes) for the GPU pool management.

### Outcomes

By the end of this chapter, you will be able to:

- Build a capacity planning model with a forecast, a buffer, and a procurement order.
- Build a FinOps dashboard that shows cost per team, cost per model, and the cost-versus-latency trade-off.
- Run a right-sizing exercise that finds over-provisioned workloads, cuts their GPU count, and measures the savings.
- Set up a reserved-instance strategy with a commitment level, a utilisation target, and a renewal calendar.
- Run the whole process on GKE, so forecasts, costs, and procurement stay predictable.

---

## 1. The capacity planning model

### 1.1 The forecasting model

Imagine your team runs 100 GPUs today, and its GPU count grew by 20 percent over the last quarter. How many GPUs should you order for next quarter? The capacity planning model answers that. It starts from the current GPU count, applies the growth rate and a buffer for spikes, and produces a forecast.

The block below lists the inputs, including historical utilisation. The forecast formula itself uses only the current count, the growth rate, and the buffer. Historical utilisation is a check you run before you trust the number, not a term in the formula.

```text
Capacity planning model:
- Historical usage: avg GPU pool utilisation over the last 90 days = 80%
- Growth rate: GPU count growth over the last 90 days = 20% per quarter
- Buffer: 30% for spikes (cost of not having enough GPUs vs cost of over-provisioning)
- Forecast: current GPU count * (1 + growth rate) * (1 + buffer)
```

Work the arithmetic by hand once: 100 × 1.20 × 1.30 = 156. The 30 percent buffer is an example value, so choose your own after you study the workload's spikes.

### 1.2 The buffer calculation

The buffer is the room you keep above the forecast, so a spike does not leave the service short. A buffer that is too small risks missing service targets. A buffer that is too large means paying for GPUs that sit idle. The table shows how that trade-off moves, using example values rather than measured ones.

| Buffer | Trade-off |
|---|---|
| 10% | Low waste; high SLO breach risk |
| 20% | Moderate waste; moderate SLO breach risk |
| 30% | Balanced, and the platform team's default |
| 50% | High waste; low SLO breach risk |
| 100% | Doubled GPU spend; no SLO breach risk |

This chapter starts at 30 percent, and that is only a starting point. Review the buffer each quarter against the workload's spike pattern.

### 1.3 The procurement order

The model produces two numbers: the target fleet for next quarter, and the order, which is how many GPUs to add to reach it. The script below prints both and writes them to a file. A person should read the script and its output before anyone signs the order.

```bash
# Compute the Q+1 GPU order
python code/part17/capacity_plan.py \
  --current-gpu-count 100 \
  --growth-rate 0.20 \
  --buffer 0.30 \
  --output procurement_order.md
# expected: target fleet 156 GPUs (order 56 more)
```

Before you trust the output, check the current GPU count you fed in. A wrong input produces a confident, wrong order.

---

## 2. The FinOps dashboard

### 2.1 The cost model

A GPU workload has four cost lines: compute, storage, network egress, and licensing. Each line works the same way. You multiply how much you used by what it costs, so the model is only as good as the usage numbers and prices you feed it. Use the prices you actually pay, because they differ by GPU class.

```text
Cost model (background reading: NVIDIA Zero-to-Hero volume 19; AI Factory; the figures below are examples, not quotations):
- GPU compute: GPU-hours * GPU price per hour (varies by GPU class)
- Storage: GB-month * storage price per GB-month
- Network egress: GB * network egress price per GB
- Licensing (NVAIE): GPU-hours * license price per GPU-hour
```

Keep this model per team, per model, and per month. The dashboard in the next section reads from it.

### 2.2 The FinOps dashboard

A team can only act on a cost it can see, so start the dashboard with cost per team. The JSON below defines five panels: cost per team, cost per model, GPU hours per team, a 90-day cost trend, and a table that sets cost beside p99 latency for each model.

```yaml
# code/part17/finops_dashboard.json
{
  "dashboard": {
    "title": "AI Factory - FinOps",
    "panels": [
      {"title": "Cost per team this month", "type": "bargauge", "targets": [{"expr": "sum by (team) (kubecost_team_cost_monthly)"}]},
      {"title": "Cost per model this month", "type": "bargauge", "targets": [{"expr": "sum by (model) (kubecost_model_cost_monthly)"}]},
      {"title": "GPU hours per team this month", "type": "stat", "targets": [{"expr": "sum by (team) (kubecost_team_gpu_hours_monthly)"}]},
      {"title": "Cost trend over the last 90 days", "type": "timeseries", "targets": [{"expr": "sum(kubecost_team_cost_daily)"}]},
      {"title": "Cost vs latency trade-off", "type": "table", "targets": [{"expr": "sum by (model) (kubecost_model_cost_monthly)", "refId": "A"}, {"expr": "histogram_quantile(0.99, sum by (model, le) (rate(inference_request_duration_seconds_bucket[5m])))", "refId": "B"}]}
    ]
  }
}
```

### 2.3 The chargeback integration

Chargeback moves these costs into the business's billing system. The SQL query below sums each team's cost by month, and the finance system reads the result. Check one month's totals by hand before you trust the chargeback.

AI Systems Performance Engineering, chapter 2, describes a model where internal teams pay per GPU-hour from their own budgets. The book argues that such a charge also covers electricity and depreciation, and that it makes people value the hardware.

```sql
-- code/part17/chargeback_query.sql
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

---

## 3. Right-sizing

### 3.1 The right-sizing exercise

Picture a cluster with three workloads. Workload A holds 8 GPUs and uses 60 percent of them. Workload B holds 16 GPUs and stays busy. Workload C holds 4 GPUs and uses 40 percent. Right-sizing asks whether A and C can give GPUs back without slowing down.

The block below works the example through. The $3.20 price is an assumed rate for illustration, not a quote from any provider.

```text
Right-sizing exercise:
- Workload A: 8 GPUs, 60% utilisation -> reduce to 5 GPUs (target 96% utilisation)
- Workload B: 16 GPUs, 80% utilisation -> no change
- Workload C: 4 GPUs, 40% utilisation -> reduce to 2 GPUs (target 80% utilisation)
- Savings: 8 - 5 + 4 - 2 = 5 GPUs * 24 hours * 30 days = 3600 GPU-hours
- Cost savings: 3600 * $3.20 = $11,520 per month
```

Workloads A and C free up 5 GPUs, or 3,600 GPU-hours over 30 days. Recompute the dollar figure with your own rate.

### 3.2 The right-sizing metrics

Read these four metrics together. Low GPU use with full memory can still mean a workload needs its GPUs. The targets in the table are examples, so choose your own once you see how your workloads behave.

| Metric | What it measures | Target |
|---|---|---|
| GPU utilisation per workload | The fraction of GPU in use | 80-95% |
| Memory utilisation per workload | The fraction of HBM in use | 80-95% |
| GPU hours per request | The GPU hours consumed per request | As low as possible |
| Cost per inference | The dollar cost per inference | As low as possible |

### 3.3 The right-sizing recommendations

Run the script below against your production cluster. It lists each workload with its GPU count, its utilisation, and a recommended count. Review each recommendation before you act, because a low average can hide a workload that peaks at certain hours.

```bash
# Generate the right-sizing recommendations
python code/part17/right_size.py \
  --cluster gke-prod-us-central1 \
  --output right_sizing_recommendations.md
# expected: a list of workloads with their GPU count, utilisation, and recommended GPU count
```
---

## 4. Reserved instances

### 4.1 The reserved-instance strategy

A commitment trades flexibility for a lower price. You agree to pay for a set number of GPUs over a set period, whether or not you use them all. The table lists four options. The discounts are example ranges, so check them against your provider's price list before you decide.

| Commitment | Discount | Use case |
|---|---|---|
| On-demand | 0% | Spike capacity; unpredictable workloads |
| 1-year reserved | 30-40% | Steady-state workloads |
| 3-year reserved | 50-60% | Long-term workloads |
| Spot | 50-70% | Preemptible workloads; training jobs |

### 4.2 The utilisation target

A commitment only pays off if you use it. The utilisation target is the lowest use that justifies a commitment. Work out the break-even point first. If the discount is 30 percent, you pay 70 percent of the on-demand price for every committed hour, so you must use 70 percent of those hours to break even.

The block below sets example targets. Replace them with figures from your own price sheet.

```text
Reserved-instance utilisation target:
- 1-year reserved: minimum 80% utilisation
- 3-year reserved: minimum 70% utilisation
- Spot: minimum 0% utilisation (spot can be preempted at any time)
```

### 4.3 The renewal calendar

A commitment that expires without notice either renews by default or lapses, and both can cost you. A renewal calendar lists each commitment, its expiry date, and the decision that is due. The script below builds that calendar. Many teams review it once a quarter, but choose the cadence that fits your contracts.

```bash
# Schedule the renewal calendar
python code/part17/renewal_calendar.py \
  --cluster gke-prod-us-central1 \
  --output renewal_calendar.md
# expected: a calendar of upcoming renewals with the commitment level and the expiry date
```

---

## 5. Operating capacity planning and cost optimisation on GKE

### 5.1 The components

Four components make up the stack. Kubecost or OpenCost collects the cost data, Grafana draws the dashboards, and BigQuery answers the chargeback query. The table lists where each one runs and the latency target it should meet. The targets are examples, so measure your own system first and then set targets that match what your team needs.

| Component | Where it runs | Backing store | SLO |
|---|---|---|---|
| Kubecost (or OpenCost) | Kubernetes Deployment | Prometheus + object storage | Cost aggregation latency p99 < 1 hour |
| Capacity planning dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |
| FinOps dashboard | Grafana | Prometheus + Kubecost | Dashboard load p99 < 5 s |
| Chargeback query | BigQuery | (BigQuery) | Query latency p99 < 30 s |

Cost also depends on how traffic enters the cluster. Production Kubernetes, chapter 6, explains that a LoadBalancer Service in a cloud cluster gets its own external load balancer, and that this adds up. An Ingress controller routes many services through one entry point, which keeps that cost down.

### 5.2 IAM and the cost optimisation

Cost data is sensitive, so the stack gets its own access roles. The table shows one way to split them, and you should adjust it to match your organisation. Teams can read the dashboard. The platform team can change the model and the dashboard. Only the CFO's office approves orders and chargebacks.

| Role | Who | What they can do |
|---|---|---|
| `finops.reader` | Every team | Read the FinOps dashboard; query the cost data |
| `finops.writer` | The platform team | Update the cost model; update the FinOps dashboard |
| `finops.admin` | The CFO's office | Approve the procurement order; approve the chargeback |

Cost attribution is the platform team's discipline. Tag every GPU with its team, model, and cost centre. The Kubecost allocation and the FinOps dashboard both read those tags, so an untagged GPU is a cost that nobody owns.

### 5.3 Observability

Five signals show whether the process is working. The table pairs each one with the alert it should trigger. The thresholds are examples, so set them from your own budgets and your own history.

| Metric | Why it matters | Alert |
|---|---|---|
| Cost per team per month | FinOps dashboard | > budget for 1 day |
| Cost per model per month | Model economics | > budget for 1 day |
| GPU utilisation per team | Capacity planning | < 30% for 7 days |
| Reserved-instance utilisation | Reserved-instance ROI | < target for 30 days |
| Right-sizing savings | Right-sizing effectiveness | < 10% per quarter |

The right-sizing savings alert matters most. A low savings rate suggests the team has stopped looking for waste, and the bill is growing without a check.

---

## 6. How it fails

Six failure modes come up again and again. Each one below gives you a symptom to look for, a likely cause, and a fix. The numbers in these examples are illustrations, not measured data.

### 6.1 "The forecast is wrong"

**Symptom:** The forecast said the team would need 156 GPUs next quarter, and the order was placed. When the quarter ended, the actual peak use was still 100 GPUs because the expected growth never arrived. That leaves 56 GPUs bought and idle. The numbers are the chapter's example, and the 100 is an assumed actual, not a measurement.

**Diagnosis:** The forecast model is off. The growth rate, the buffer, or the history the model learned from may be wrong.

**Fix:** Tune the model and check its history. Add a confidence range to the forecast, and review it each quarter.

### 6.2 "The right-sizing exercise finds nothing"

**Symptom:** The team runs the right-sizing exercise every quarter. It finds nothing, and the GPU bill keeps climbing.

**Diagnosis:** The metrics may be wrong, the exercise may cover too few workloads, or the team may not be looking at all of them.

**Fix:** Add the right metrics, widen the exercise to every workload, and train people on the method.

### 6.3 "The reserved-instance commitment is wasted"

**Symptom:** The commitment looks well used, but the bill is higher than on-demand would have been.

**Diagnosis:** Check how utilisation is measured first. At a 30 percent discount, a commitment only breaks even at about 70 percent use, so a figure of 80 percent should save money. If it does not, the forecast was too optimistic, the spike pattern does not match the commitment, or the team did not adjust it.

**Fix:** Adjust the commitment level, move spiky work to on-demand or spot, and sell the commitment if your provider allows it.

### 6.4 "The chargeback is wrong"

**Symptom:** Team A's chargeback is larger than team B's. The teams dispute it, and the CFO's office escalates.

**Diagnosis:** The cost attribution, the cost model, or the chargeback query is wrong.

**Fix:** Check the attribution and the model. Test the query against spend you already know, and automate a chargeback audit.

### 6.5 "The GPU bill grows without bound"

**Symptom:** The GPU bill rises each quarter. Nobody updates the forecast, and nobody caps the orders.

**Diagnosis:** The forecast is stale, the orders have no cap, and right-sizing is not running.

**Fix:** Update the forecast each quarter, cap the orders, and run right-sizing every quarter.

### 6.6 "The cost optimisation is ad-hoc"

**Symptom:** Teams cut costs on their own. They skip the right-sizing method and ignore the FinOps dashboard.

**Diagnosis:** The process is written down, but nobody enforces it, and the team has not been trained on it.

**Fix:** Train the team, check the process in code review, and add it to the team's quarterly goals.

---

## 7. Hands-on lab

This lab takes you through the capacity model, the FinOps dashboard, the right-sizing exercise, and the reserved-instance strategy, in that order. The lab is **untested** in this repository, so treat each step as a plan to verify on your own cluster.

### 7.1 Prerequisites

Check three things before you start.

- Kubecost (or OpenCost) installed.
- The observability stack from earlier chapters.
- A GKE Autopilot or Standard cluster with at least 4 H100 GPUs.

### 7.2 Step 1: deploy Kubecost

Start by installing Kubecost into its own namespace. Wait until its pods are running before you move on.

```bash
helm repo add kubecost https://kubecost.github.io/cost-analyzer
helm install kubecost kubecost/cost-analyzer \
  --namespace kubecost --create-namespace \
  --set kubecostToken=$KUBECOST_TOKEN
# expected: Kubecost pods are running; Kubecost is scraping the cluster
```

### 7.3 Step 2: build the FinOps dashboard

Next, load the dashboard into Grafana. The import command below uses Grafana's default admin credentials, so change that password first and never run the command against a shared Grafana.

```bash
kubectl -n monitoring create configmap finops-dashboard \
  --from-file=dashboards/finops.json

curl -X POST http://admin:admin@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @dashboards/finops_import.json
# expected: the FinOps dashboard is available at /d/finops/ai-factory-finops
```

### 7.4 Step 3: run the capacity planning model

Run the model with your current GPU count. Check the printed number against your own arithmetic before you trust it. Four GPUs, with 20 percent growth and a 30 percent buffer, give 6.24 before any rounding.

```bash
python code/part17/capacity_plan.py \
  --current-gpu-count 4 \
  --growth-rate 0.20 \
  --buffer 0.30 \
  --output procurement_order.md
# expected: target fleet 7 GPUs (order 3 more; 6.24 rounded up)
```

### 7.5 Step 4: run the right-sizing exercise

Run the right-sizing script against the cluster, then open the recommendations file. Start with the workloads that show the lowest utilisation.

```bash
python code/part17/right_size.py \
  --cluster gke-prod-us-central1 \
  --output right_sizing_recommendations.md
# expected: a list of workloads with their GPU count, utilisation, and recommended GPU count
```

### 7.6 Step 5: query the chargeback

Finally, query the chargeback table in BigQuery. The query returns up to 12 rows, newest first, so you can see each team's recent months.

```bash
bq query --use_legacy_sql=false \
  "SELECT team, month, total_cost
   FROM \`${PROJECT_ID}.finops.chargeback\`
   ORDER BY month DESC LIMIT 12"
# expected: the per-team, per-month chargeback
```

### 7.7 What to record

Answer these five questions from the dashboards alone, and time yourself. The 30-second limit is an example, so set the limit your team actually needs.

1. What is the current cost per team this month?
2. What is the Q+1 GPU order per the capacity planning model?
3. What is the current right-sizing savings rate?
4. What is the current reserved-instance utilisation?
5. What is the next reserved-instance renewal date?

If any answer takes longer than your limit, the stack is not yet a production service. The lab has not been tested against a live GKE cluster.

---

## Exercises

1. **Add a per-model cost dashboard.** Build a Grafana dashboard that shows what each model costs to run. It should combine the model's cost, its GPU hours, and its inference count. *Solution sketch:* a Grafana dashboard that reads the per-model cost, GPU hours, and inference count from the same data sources the FinOps dashboard uses.
2. **Add a right-sizing recommendation script.** Build a script that reads the current GPU usage and recommends a smaller count where the GPUs sit idle. *Solution sketch:* a Python script that reads the metrics, computes the right-sized count, and writes the recommendation to a file.
3. **Add a reserved-instance tracking dashboard.** Build a Grafana dashboard that shows how much of each commitment is used. It is the view you use to judge whether a commitment is paying off. *Solution sketch:* a Grafana dashboard that plots reserved-instance utilisation against the target you set in section 4.
4. **Add a FinOps alert per team.** Configure an alert that fires when a team's monthly cost exceeds its budget. *Solution sketch:* a Prometheus alert on the per-team cost that notifies the team's lead.
5. **Add a capacity planning review process.** Schedule a quarterly review that produces a procurement order and sends it to the CFO's office for approval. *Solution sketch:* a calendar event, a review script, and a signed procurement order.
6. **Add a chargeback audit.** Run a monthly audit that checks each team's chargeback and flags anomalies. *Solution sketch:* a Python script that reads the chargeback table, recomputes each team's total, and flags any difference.

---

## Checkpoint questions

<details><summary>1. Finance asks why the GPU bill keeps rising and nobody on the platform team can explain it. What should have existed, and what would it show?</summary>
A FinOps dashboard, which is the platform team's picture of the cluster's economics. It shows cost per team, cost per model, and GPU hours per team this month, plus a 90-day cost trend. A team that cannot see its own cost has little reason to give GPUs back.
</details>

<details><summary>2. Team A's chargeback is larger than team B's, the teams dispute it, and the CFO's office escalates. Where do you look?</summary>
The chapter names three suspects, which are the cost attribution, the cost model, and the chargeback query. Test the query against spend you already know, and check the tags on each GPU. Then automate a chargeback audit so the next dispute is caught earlier.
</details>

<details><summary>3. The forecast asked for 156 GPUs, but the team only used 100. What does that leave you with, and what may have gone wrong?</summary>
It leaves 56 GPUs bought and idle. The growth rate, the buffer, or the history the model learned from may be wrong. Tune the model, add a confidence range to the forecast, and review it each quarter.
</details>

<details><summary>4. The team runs right-sizing every quarter, finds nothing, and the GPU bill keeps climbing. What does the chapter say may be wrong?</summary>
The metrics may be wrong, the exercise may cover too few workloads, or the team may not be looking at all of them. Add the right metrics, widen the exercise to every workload, and train people on the method. A right-sizing savings rate below 10 percent per quarter is the alert that should have flagged this.
</details>

<details><summary>5. A 1-year commitment shows 80 percent utilisation, yet the bill is higher than on-demand would have been. What do you check first?</summary>
Check how utilisation is measured. At a 30 percent discount a commitment breaks even at about 70 percent use, so 80 percent should save money. If it does not, the forecast was too optimistic, the spike pattern does not match the commitment, or the team did not adjust it.
</details>

<details><summary>6. Dashboards show the cluster fully busy, yet jobs finish slowly. Which idea from the chapter explains this, and what example supports it?</summary>
Goodput, which is useful work completed per unit of time, is a better measure than raw busy time. The chapter cites Meta's "Revisiting Reliability" paper through AI Systems Performance Engineering, chapter 1. A cluster that looked fully used still lost 70 to 75 percent of its compute to communication delays, slow data supply, and failure recovery.
</details>

<details><summary>7. Why does a 30 percent discount require about 70 percent utilisation to break even?</summary>
With a 30 percent discount you pay 70 percent of the on-demand price for every committed hour, whether you use it or not. Using 70 percent of those hours matches what on-demand would have cost. Below that, the commitment costs more than on-demand.
</details>

<details><summary>8. Why would closing the gap from 60 percent to 80 percent utilisation save 25 percent of GPU spend?</summary>
The same work needs fewer GPUs when each one is busier. At 60 percent use the work needs 60 out of every 80 GPUs it would need at 80 percent, so 60 divided by 80 is 0.75. That is a 25 percent saving. The figures are the chapter's examples.
</details>

<details><summary>9. Why does an untagged GPU hurt the cost process?</summary>
Kubecost allocation and the FinOps dashboard both read the team, model, and cost centre tags. An untagged GPU has no team, so its cost belongs to nobody. It then cannot appear in a chargeback or be reviewed in right-sizing.
</details>

<details><summary>10. Why can a service of type LoadBalancer make cost grow quietly, and what does an Ingress change?</summary>
In a cloud cluster each LoadBalancer Service gets its own external load balancer, and those charges add up. An Ingress controller routes many services through one entry point. That keeps the number of load balancers, and the bill, down.
</details>

<details><summary>11. Why does the chapter say a low right-sizing savings rate is the most important alert?</summary>
A low rate suggests the team has stopped looking for waste. The bill then grows without a check, because nothing is pulling unused GPUs back. The example alert fires when savings fall below 10 percent per quarter.
</details>

<details><summary>12. You must set a buffer. When would you pick 30 percent over 10 percent, and what do you give up?</summary>
Pick 30 percent when missing the SLO during a spike costs more than idle GPUs. You give up some spend, because 10 percent has low waste but a high SLO breach risk. The chapter treats 30 percent as a balanced starting point and asks you to review it each quarter against your spike pattern.
</details>

<details><summary>13. A training workload is steady for three years and another is spiky. When would you choose 3-year reserved, 1-year reserved, on-demand, or spot, and what do you give up with each?</summary>
Use 3-year reserved for long-term steady work, with a 50 to 60 percent discount and the least flexibility. Use 1-year reserved for steady-state work at 30 to 40 percent. Use on-demand for spikes at no discount, and spot for preemptible training jobs at 50 to 70 percent, where you accept being preempted at any time.
</details>

<details><summary>14. Should the platform team charge each team per GPU-hour or keep GPUs in one shared budget, and what does each give up?</summary>
A per-GPU-hour charge makes teams see the cost and value the hardware. AI Systems Performance Engineering, chapter 2, adds that it also covers electricity and depreciation. You give up simplicity, because you need tags, a cost model, and a chargeback query that teams will trust. A shared budget is easier but hides who uses what.
</details>

<details><summary>15. The workload's average utilisation looks low. Do you cut its GPUs straight away, or check first, and what do you risk either way?</summary>
Review each recommendation first, because a low average can hide a workload that peaks at certain hours. Cutting immediately saves money but risks missing the SLO at the peak. Checking costs a little time and keeps the savings honest.
</details>

<details><summary>16. A team has 100 GPUs, growth of 20 percent, and a 30 percent buffer. What is the target fleet and the order?</summary>
The forecast is current count times 1.20 times 1.30. That is 100 times 1.20 times 1.30, which is 156 GPUs. The order is 156 minus 100, so 56 more.
</details>

<details><summary>17. A lab cluster has 4 GPUs, 20 percent growth, and a 30 percent buffer. What does the script print, and why?</summary>
The raw result is 4 times 1.20 times 1.30, which is 6.24. You cannot buy a fraction of a GPU, so the target fleet is 7. The order is 7 minus 4, which is 3 more.
</details>

<details><summary>18. In the right-sizing example, A drops from 8 to 5 GPUs and C from 4 to 2. At $3.20 per GPU-hour, what is the monthly saving?</summary>
A frees 3 GPUs and C frees 2, which is 5 GPUs. Over 30 days that is 5 times 24 times 30, which is 3,600 GPU-hours. At $3.20 each the saving is 3,600 times 3.20, which is $11,520. The $3.20 is an assumed rate, so use your own.
</details>

<details><summary>19. The procurement script prints an order that looks far too high. What do you check first, second, and third?</summary>
First check the current GPU count you fed in, because a wrong input gives a confident, wrong order. Second check the growth rate and the buffer against the last 90 days of history. Third work the formula by hand, as in 100 times 1.20 times 1.30, and compare it with the printed number.
</details>

<details><summary>20. A chargeback total for one month looks wrong. In what order do you verify it before finance reads it?</summary>
First check one month's totals by hand against the four cost lines, which are compute, storage, network egress, and licensing. Second check that the cost attribution tags are present on the GPUs involved. Third test the query against spend you already know.
</details>

---

## Sources and review notes

- NVIDIA Zero-to-Hero Volume 19 (`chapter-03-capacity-planning.md`, `chapter-06-cost-optimisation.md`). Source for the capacity planning model, the FinOps dashboard, and the cost optimisation patterns. The wording has been rewritten in the handbook's voice.
- *AI Factory* (`ai-factory`, Chapter 8, on software engineering). Background on the lifecycle only; it has no GPU cost material.
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

corrected 2026-11-11: no quarterly_review.py exists and none is used here; the capacity_plan.py commands use its real flags (--current-gpu-count, --growth-rate, --buffer, --output), and the expected output now matches what the script prints (target fleet and order); source code/part17/capacity_plan.py, run 2026-11-11.
